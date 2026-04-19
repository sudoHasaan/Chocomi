import json
from collections.abc import AsyncGenerator
import asyncio
import re

import httpx

from config import settings
from tools import AVAILABLE_TOOLS, execute_tool_call


async def parse_tool_calls(text: str) -> list[dict]:
    """Extract tool calls from <TOOL>...</TOOL> markers in text."""
    tool_calls = []
    pattern = r'<TOOL>([\w_]+)\(([^)]*)\)</TOOL>'
    matches = re.findall(pattern, text)
    for func_name, args_str in matches:
        if func_name in AVAILABLE_TOOLS:
            args = {}
            args_str = args_str.strip()
            
            if args_str:
                # Map the positional argument to the function's expected parameter
                if func_name == "get_weather":
                    args = {"location": args_str.strip('\'"')}
                elif func_name == "calculate":
                    args = {"expression": args_str.strip('\'"')}
                elif func_name == "get_current_time":
                    if args_str and args_str != '()':
                        args = {"timezone": args_str.strip('\'"')}
            
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
                                    # Stream the tool response word by word to match the LLM's natural speed
                                    content = res.get("content", "")
                                    words = (" " + content + " ").split(" ")
                                    for word in words:
                                        if word:
                                            yield word + " "
                                            await asyncio.sleep(0.05)
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