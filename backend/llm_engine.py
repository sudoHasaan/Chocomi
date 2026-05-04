import json
from collections.abc import AsyncGenerator
import re

import httpx

from config import settings
from tools import AVAILABLE_TOOLS, execute_tool_call


def _split_positional_args(text: str) -> list[str]:
    args: list[str] = []
    current: list[str] = []
    quote: str | None = None

    for ch in text:
        if quote:
            if ch == quote:
                quote = None
            else:
                current.append(ch)
            continue

        if ch in {'"', "'"}:
            quote = ch
            continue

        if ch == ",":
            arg = "".join(current).strip()
            if arg:
                args.append(arg)
            current = []
            continue

        current.append(ch)

    tail = "".join(current).strip()
    if tail:
        args.append(tail)
    return args


async def parse_tool_calls(text: str) -> list[dict]:
    """Extract tool calls from [TOOL: name(args)] markers."""
    tool_calls = []
    pattern = r'\[TOOL:\s*([\w_]+)\(([^)]*)\)\]'
    matches = re.findall(pattern, text)
    for func_name, args_str in matches:
        if func_name in AVAILABLE_TOOLS:
            args = {}
            args_str = args_str.strip()
            positional = _split_positional_args(args_str) if args_str else []
            
            if args_str:
                if func_name == "get_weather":
                    args = {"location": args_str.strip('\'"')}
                elif func_name == "calculate":
                    args = {"expression": args_str.strip('\'"')}
                elif func_name == "get_current_time":
                    if args_str and args_str != '()':
                        args = {"timezone": args_str.strip('\'"')}
                elif func_name == "crm_get_user_info":
                    if positional:
                        args = {"user_id": positional[0]}
                elif func_name == "crm_update_user_info":
                    if len(positional) >= 3:
                        args = {"user_id": positional[0], "field": positional[1], "value": positional[2]}
            
            tool_calls.append({
                "function": {"name": func_name, "arguments": args}
            })
    return tool_calls

async def stream_response(messages: list[dict]) -> AsyncGenerator[str, None]:
    url = f"{settings.ollamaBaseUrl}/api/chat"
    payload = {
        "model": settings.ollamaModel,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.1, "num_predict": 150},
    }

    buffer = ""
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line: continue
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    buffer += token
                    # If we find a complete tool call, execute it and yield result
                    if "]" in buffer:
                        start = buffer.find("[TOOL:")
                        end = buffer.find("]", start)
                        if start != -1 and end != -1:
                            # Yield text before tool
                            if start > 0: yield buffer[:start]
                            
                            tool_text = buffer[start:end+1]
                            buffer = buffer[end+1:]
                            
                            tc_parsed = await parse_tool_calls(tool_text)
                            if tc_parsed:
                                res = await execute_tool_call(tc_parsed[0])
                                yield f" (Tool Result: {res.get('content', '')}) "
                        else:
                            # No complete tool call yet, yield and keep partial
                            if "[" not in buffer:
                                yield buffer
                                buffer = ""
                    else:
                        if "[" not in buffer:
                            yield buffer
                            buffer = ""
                
                if chunk.get("done"):
                    if buffer: yield buffer
                    break