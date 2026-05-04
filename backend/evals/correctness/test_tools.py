import pytest
import asyncio
from tools import get_weather, calculate, get_current_time, execute_tool_call

@pytest.mark.asyncio
async def test_calculate_valid():
    assert await calculate("10 + 20") == "30"
    assert await calculate("5 * 5") == "25"
    assert await calculate("(10 + 2) * 3") == "36"

@pytest.mark.asyncio
async def test_calculate_invalid():
    # Test safe eval restriction
    res = await calculate("import os")
    assert "Error" in res
    
    res = await calculate("10 + abc")
    assert "Error" in res

@pytest.mark.asyncio
async def test_get_current_time():
    res = await get_current_time()
    assert "2026" in res or "2025" in res # Depending on system time
    assert ":" in res # Time format

@pytest.mark.asyncio
async def test_get_weather_real():
    # This tests the actual API call, might be slow or flaky based on network
    res = await get_weather("Karachi")
    assert "°C" in res or "Could not find" in res or "Failed" in res

@pytest.mark.asyncio
async def test_execute_tool_call_dispatcher():
    tool_call = {
        "function": {
            "name": "calculate",
            "arguments": "{\"expression\": \"2 + 2\"}"
        }
    }
    res = await execute_tool_call(tool_call)
    assert res["role"] == "tool"
    assert res["content"] == "4"
    assert res["name"] == "calculate"

@pytest.mark.asyncio
async def test_execute_tool_not_found():
    tool_call = {
        "function": {
            "name": "non_existent_tool",
            "arguments": "{}"
        }
    }
    res = await execute_tool_call(tool_call)
    assert "Error" in res["content"]
