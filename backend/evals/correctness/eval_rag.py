import json
import asyncio
from vector_store import retrieve_context
from evals.correctness.judge import call_judge
from config import settings

async def evaluate_retrieval():
    """Computes Precision@k and Recall@k for RAG retrieval."""
    with open("evals/data/rag_queries.json", "r") as f:
        test_cases = json.load(f)
    
    results = []
    total_precision = 0
    total_recall = 0
    
    print(f"Evaluating retrieval for {len(test_cases)} queries...")
    
    for case in test_cases:
        query = case["query"]
        expected_ids = set(case["relevant_docs"])
        
        # We'll test with k=5 to be generous for recall
        _, retrieved_ids = retrieve_context(query, k=5, return_ids=True)
        retrieved_ids = set(retrieved_ids)
        
        relevant_retrieved = retrieved_ids.intersection(expected_ids)
        
        precision = len(relevant_retrieved) / len(retrieved_ids) if retrieved_ids else 0
        recall = len(relevant_retrieved) / len(expected_ids) if expected_ids else 0
        
        total_precision += precision
        total_recall += recall
        
        results.append({
            "query": query,
            "precision": precision,
            "recall": recall,
            "retrieved": list(retrieved_ids),
            "expected": list(expected_ids)
        })
    
    avg_precision = total_precision / len(test_cases)
    avg_recall = total_recall / len(test_cases)
    
    return {
        "avg_precision_at_5": avg_precision,
        "avg_recall_at_5": avg_recall,
        "detail": results
    }

async def evaluate_faithfulness(query: str, context: str, answer: str):
    """Uses LLM to check if the answer is faithful to the context."""
    prompt = f"""Evaluate the faithfulness of the answer based ONLY on the retrieved context.
    
    Query: {query}
    Context: {context}
    Answer: {answer}
    
    Instructions:
    - Is the answer supported by the context?
    - Does the answer include information NOT in the context?
    - Output 1 if perfectly faithful, 0.5 if partially faithful, 0 if it hallucinates or contradicts context.
    - Output ONLY the number.
    """
    
    res = await call_judge(prompt)
    try:
        import re
        match = re.search(r"([0-9\.]+)", res)
        if match:
            return float(match.group(1))
    except:
        pass
    return 0.0

if __name__ == "__main__":
    res = asyncio.run(evaluate_retrieval())
    print(f"Average Precision@5: {res['avg_precision_at_5']:.2f}")
    print(f"Average Recall@5: {res['avg_recall_at_5']:.2f}")
