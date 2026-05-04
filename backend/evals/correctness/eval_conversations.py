import json
import asyncio
from conversation_manager import ConversationSession
from llm_engine import stream_response
from evals.correctness.judge import score_response
from evals.correctness.eval_rag import evaluate_faithfulness

async def run_conversation_eval():
    """Runs the 10 multi-turn dialogues and evaluates them."""
    with open("evals/data/conversations.json", "r") as f:
        test_cases = json.load(f)
    
    results = []
    total_score = 0
    
    print(f"Running {len(test_cases)} conversation evaluations...")
    
    for case in test_cases:
        session = ConversationSession(userId=f"eval_{case['id']}")
        last_response = ""
        
        # Run through the turns
        for turn in case["turns"]:
            if turn["role"] == "user":
                await session.ingestUserTurn(turn["content"])
                
                # We skip the _maybe_answer_with_direct_tools logic here for simplicity 
                # or we could include it. Let's include it to be realistic.
                from main import _maybe_answer_with_direct_tools
                direct = await _maybe_answer_with_direct_tools(turn["content"])
                if direct:
                    last_response = direct
                    session.addAssistantTurn(direct)
                else:
                    messages = session.buildMessages()
                    reply_parts = []
                    async for token in stream_response(messages):
                        reply_parts.append(token)
                    last_response = "".join(reply_parts)
                    session.addAssistantTurn(last_response)
        
        # Evaluate final response
        score = await score_response(case["rubric"], case["turns"][-1]["content"], last_response)
        
        # Optional: Check faithfulness if it was a RAG query
        is_faithful = 1.0
        if "RAG" in case["description"]:
            # Extract context used in the last turn
            context = ""
            for msg in session.buildMessages():
                if msg["role"] == "system" and "<RETRIEVED_CONTEXT>" in msg["content"]:
                    import re
                    match = re.search(r"<RETRIEVED_CONTEXT>(.*?)</RETRIEVED_CONTEXT>", msg["content"], re.DOTALL)
                    if match: context = match.group(1).strip()
            
            is_faithful = await evaluate_faithfulness(case["turns"][-1]["content"], context, last_response)

        results.append({
            "id": case["id"],
            "description": case["description"],
            "response": last_response,
            "score": score,
            "faithfulness": is_faithful
        })
        total_score += score
    
    avg_score = total_score / len(test_cases)
    return {
        "avg_conversational_quality": avg_score,
        "detail": results
    }

if __name__ == "__main__":
    res = asyncio.run(run_conversation_eval())
    print(f"Average Score: {res['avg_conversational_quality']}")
