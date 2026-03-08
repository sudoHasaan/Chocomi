import sys
import os
import json
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import pytest_asyncio
from conversation_manager import ConversationSession, SYSTEM_PROMPT
from llm_engine import stream_response
from config import settings


@pytest_asyncio.fixture
async def session():
    """Provides a fresh ConversationSession for each test."""
    return ConversationSession()

async def get_full_response(messages: list[dict]) -> str:
    """Helper to collect all yielded chunks from the stream."""
    response_chunks = []
    async for chunk in stream_response(messages):
        response_chunks.append(chunk)
    return "".join(response_chunks).strip()

async def judge_response(assistant_response: str, criteria: str) -> bool:
    """
    Uses the local LLM as a judge to evaluate if the assistant's response met the criteria.
    Returns True if the LLM judge replies with [PASS], False otherwise.
    """
    judge_prompt = f"""You are an objective evaluator. Read the assistant's response and determine if it meets the criteria.
Assistant Response: "{assistant_response}"
Criteria: {criteria}

If it strictly meets the criteria, reply with EXACTLY the word: [PASS]
If it fails to meet the criteria in any way, reply with EXACTLY the word: [FAIL]
Do NOT output anything else.
"""
    judge_messages = [{"role": "user", "content": judge_prompt}]
    url = f"{settings.ollamaBaseUrl}/api/chat"
    payload = {
        "model": settings.ollamaModel,
        "messages": judge_messages,
        "stream": False,
        "options": {"temperature": 0.0} # We want deterministic judging
    }
    
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        judge_output = data.get("message", {}).get("content", "").strip()
        
    return "[PASS]" in judge_output.upper()


@pytest.mark.asyncio
async def test_initial_greeting(session: ConversationSession):
    """Test 1: Greetings/Tone"""
    session.addUserTurn("Hello! I need some help with my PC.")
    response = await get_full_response(session.buildMessages())
    
    criteria = "The assistant must greet the user and explicitly introduce itself using the name 'Chocomi'."
    passed = await judge_response(response, criteria)
    assert passed, f"Judge failed the response. Actual response: {response}"

@pytest.mark.asyncio
async def test_accurate_pricing_and_stock(session: ConversationSession):
    """Test 2: Accuracy"""
    session.addUserTurn("Do you have the NVIDIA RTX 4070 Super in stock? How much is it?")
    response = await get_full_response(session.buildMessages())
    
    criteria = "The assistant must state that the item is in stock and that the price is $589."
    passed = await judge_response(response, criteria)
    assert passed, f"Judge failed the response. Actual response: {response}"

@pytest.mark.asyncio
async def test_out_of_scope_refusal(session: ConversationSession):
    """Test 3: Out-of-Scope"""
    session.addUserTurn("How do I bake a chocolate cake?")
    response = await get_full_response(session.buildMessages())
    
    criteria = "The assistant must refuse to provide a cake recipe, stating it can only assist with PC hardware."
    passed = await judge_response(response, criteria)
    assert passed, f"Judge failed the response. Actual response: {response}"

@pytest.mark.asyncio
async def test_unknown_inventory_fallback(session: ConversationSession):
    """Test 4: Unknown Inventory"""
    session.addUserTurn("Do you sell the Intel Arc A770 GPU?")
    response = await get_full_response(session.buildMessages())
    
    criteria = "The assistant must provide the phone number +1 (555) 010-4090 for further checking."
    passed = await judge_response(response, criteria)
    assert passed, f"Judge failed the response. Actual response: {response}"

@pytest.mark.asyncio
async def test_conciseness(session: ConversationSession):
    """Test 5: Conciseness (Deterministic String Matching)"""
    session.addUserTurn("Can you tell me everything about your Intel processors and what I need for a full build?")
    response = await get_full_response(session.buildMessages())
    
    paragraphs = [p for p in response.split('\n\n') if p.strip()]
    assert len(paragraphs) <= 4, f"Response exceeded 4 paragraphs (got {len(paragraphs)}). Response: {response}"
