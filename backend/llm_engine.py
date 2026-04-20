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
    """Extract tool calls from <TOOL>...</TOOL> markers in text."""
    tool_calls = []
    pattern = r'<TOOL>([\w_]+)\(([^)]*)\)</TOOL>'
    matches = re.findall(pattern, text)
    for func_name, args_str in matches:
        if func_name in AVAILABLE_TOOLS:
            args = {}
            args_str = args_str.strip()
            positional = _split_positional_args(args_str) if args_str else []
            
            if args_str:
                # Map the positional argument to the function's expected parameter
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
                elif func_name == "crm_store_user_info":
                    # crm_store_user_info(user_id, name, email, phone, preferences, notes)
                    if positional:
                        args = {"user_id": positional[0]}
                    if len(positional) > 1:
                        args["name"] = positional[1]
                    if len(positional) > 2:
                        args["email"] = positional[2]
                    if len(positional) > 3:
                        args["phone"] = positional[3]
                    if len(positional) > 4:
                        args["preferences"] = positional[4]
                    if len(positional) > 5:
                        args["notes"] = positional[5]
                elif func_name == "crm_update_user_info":
                    # crm_update_user_info(user_id, field, value)
                    if len(positional) >= 3:
                        args = {
                            "user_id": positional[0],
                            "field": positional[1],
                            "value": positional[2],
                        }
            
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
        "options": {
            "temperature": 0.2,
            "num_predict": 120,
        },
    }

    full_response = ""
    buffer = ""

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                
                token = chunk.get("message", {}).get("content", "")
                if token:
                    full_response += token
                    buffer += token
                    
                    # Intercept and hide <TOOL> markers, while streaming regular text instantly
                    while buffer:
                        idx = buffer.find("<")
                        if idx == -1:
                            yield buffer
                            buffer = ""
                            break
                        elif idx > 0:
                            yield buffer[:idx]
                            buffer = buffer[idx:]
                            
                        # Now buffer starts with '<'
                        if buffer.startswith("<TOOL>"):
                            end_idx = buffer.find("</TOOL>")
                            if end_idx != -1:
                                tool_text = buffer[6:end_idx]
                                buffer = buffer[end_idx + 7:]
                                # We found a tool right now in the stream, let's parse it and run it immediately!
                                tc_parsed = await parse_tool_calls("<TOOL>"+tool_text+"</TOOL>")
                                if tc_parsed:
                                    res = await execute_tool_call(tc_parsed[0])
                                    # Emit tool results immediately to avoid artificial latency.
                                    content = res.get("content", "")
                                    words = (" " + content + " ").split(" ")
                                    for word in words:
                                        if word:
                                            yield word + " "
                            else:
                                break
                        else:
                            # It starts with '<', is it a tool tag prefix?
                            if "<TOOL>".startswith(buffer):
                                # Wait for more tokens since it could become <TOOL>
                                break
                            else:
                                # Not a tool tag, just a regular '<', yield and continue
                                yield buffer[0]
                                buffer = buffer[1:]
                                
                if chunk.get("done"):
                    if buffer and not buffer.startswith("<TOOL"):
                        yield buffer
                    break
    
    # We already intercepted and injected tool responses instantly in the stream!
    # No need to parse them again at the end.
    pass