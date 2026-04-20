import json
import httpx
from datetime import datetime
import asyncio
from crm_store import get_user_info, store_user_info, update_user_info

# 1. Weather Tool (Using Open-Meteo Free API)
async def get_weather(location: str = "Karachi") -> str:
    """Get current weather for a location."""
    async with httpx.AsyncClient() as client:
        try:
            # First get coordinates from city name
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
            geo_resp = await client.get(geo_url)
            geo_data = geo_resp.json()
            
            if not geo_data.get("results"):
                return f"Could not find coordinates for {location}"
                
            lat = geo_data["results"][0]["latitude"]
            lon = geo_data["results"][0]["longitude"]
            
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            resp = await client.get(url)
            data = resp.json()
            cw = data.get("current_weather", {})
            if not cw:
                return f"unavailable for {location}"
            return f"{cw.get('temperature', 'unknown')}°C, wind speed {cw.get('windspeed', 'unknown')} km/h"
        except Exception as e:
            return f"Failed to get weather: {e}"

# 2. Calculator Tool
async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    # Extremely basic and safe eval subset
    allowed_chars = "0123456789+-*/(). "
    if not all(c in allowed_chars for c in expression):
        return "Error: Invalid characters in expression"
    try:
        # safe eval using compile
        code = compile(expression, "<string>", "eval")
        for name in code.co_names:
            if name not in []: 
                return "Error: Functions not allowed"
        result = eval(code, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

# 3. Time / Calendar Tool
async def get_current_time(timezone: str = None) -> str:
    """Get the current date and time in local system timezone."""
    try:
        import time
        return time.strftime("%I:%M %p on %B %d, %Y (%A)", time.localtime())
    except Exception as e:
        return f"Error getting time: {e}"


# 4. CRM Tools
async def crm_get_user_info(user_id: str) -> str:
    """Retrieve persisted user profile and recent interaction history."""
    data = get_user_info(user_id)
    return json.dumps(data, ensure_ascii=True)


async def crm_store_user_info(
    user_id: str,
    name: str = "",
    email: str = "",
    phone: str = "",
    preferences: str = "",
    notes: str = "",
) -> str:
    """Store user info in CRM (upsert semantics)."""
    data = store_user_info(
        user_id=user_id,
        name=name,
        email=email,
        phone=phone,
        preferences=preferences,
        notes=notes,
    )
    return json.dumps(data, ensure_ascii=True)


async def crm_update_user_info(user_id: str, field: str, value: str) -> str:
    """Update one CRM field for a user."""
    data = update_user_info(user_id=user_id, field=field, value=value)
    return json.dumps(data, ensure_ascii=True)

# Tool Registry
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "calculate": calculate,
    "get_current_time": get_current_time,
    "crm_get_user_info": crm_get_user_info,
    "crm_store_user_info": crm_store_user_info,
    "crm_update_user_info": crm_update_user_info,
}

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Call this to get the current weather. Do not ask for a location.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g., 'New York'"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression. E.g. '25 * 4 + 10'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "ALWAYS call this tool to get the current date and time. Do not try to guess the time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Optional timezone to retrieve the time for"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_get_user_info",
            "description": "Retrieve user CRM profile and recent interaction history. Call for returning users.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "Unique user/session id"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_store_user_info",
            "description": "Store user information in CRM (name, contact, preferences).",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "phone": {"type": "string"},
                    "preferences": {"type": "string"},
                    "notes": {"type": "string"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "crm_update_user_info",
            "description": "Update one CRM profile field for a user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "field": {"type": "string", "description": "name|email|phone|preferences|notes"},
                    "value": {"type": "string"}
                },
                "required": ["user_id", "field", "value"]
            }
        }
    }
]

async def execute_tool_call(tool_call: dict) -> dict:
    """Executes a single tool call and returns the result message."""
    func_name = tool_call["function"]["name"]
    args = tool_call["function"].get("arguments", {})
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except:
            args = {}
            
    print(f"Executing tool: {func_name} with args: {args}")
    
    if func_name in AVAILABLE_TOOLS:
        func = AVAILABLE_TOOLS[func_name]
        try:
            result = await func(**args)
        except TypeError as e:
            result = f"Argument error: {e}"
    else:
        result = f"Error: Tool '{func_name}' not found."
        
    return {
        "role": "tool",
        "content": str(result),
        "name": func_name
    }
