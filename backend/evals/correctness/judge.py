import json
import logging
import httpx
from config import settings

logger = logging.getLogger(__name__)

async def call_judge(prompt: str, model: str = "llama3.1:8b") -> str:
    """Calls the LLM as a judge to score a response."""
    judge_model = model # Use specified model
    url = f"{settings.ollamaBaseUrl}/api/chat"
    
    payload = {
        "model": judge_model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"temperature": 0} # Deterministic judging
    }
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(url, json=payload)
            res.raise_for_status()
            return res.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Judge call failed: {e}")
        return "Error: Could not call judge."

async def score_response(rubric: str, user_input: str, assistant_response: str) -> float:
    """Uses LLM to score a response based on a rubric. Returns a float score 0-1."""
    prompt = f"""You are a strict evaluation judge. 
    Evaluate the Assistant's response based on the Rubric provided.
    
    User Input: {user_input}
    Assistant Response: {assistant_response}
    
    Rubric: {rubric}
    
    Instructions:
    1. Read the Rubric carefully.
    2. Analyze if the Assistant followed the rubric perfectly.
    3. Output ONLY a single numeric score (e.g., 0, 0.5, or 1) and nothing else.
    """
    
    result = await call_judge(prompt)
    try:
        # Extract the first number found in the response
        import re
        match = re.search(r"([0-9\.]+)", result)
        if match:
            return float(match.group(1))
    except:
        pass
    return 0.0
