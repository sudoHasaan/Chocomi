import asyncio
import json
import os
import platform
import psutil
import httpx
from datetime import datetime
from config import settings

# Import our evaluators
from evals.correctness.eval_conversations import run_conversation_eval
from evals.correctness.eval_rag import evaluate_retrieval
from evals.correctness.eval_tools import evaluate_tool_accuracy
from evals.performance.benchmarks import run_latency_benchmarks, run_throughput_benchmark

async def check_model_available(model_name: str):
    """Verify if the model is pulled in Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{settings.ollamaBaseUrl}/api/tags")
            if res.status_code == 200:
                models = [m["name"] for m in res.json().get("models", [])]
                return model_name in models
    except:
        pass
    return False

async def generate_report():
    print("Starting Comprehensive Evaluation Suite (Aggregated 5-Run Mode)...")
    num_runs = 5
    
    # Verify Judge Model
    judge_model = "llama3.1:8b"
    if not await check_model_available(judge_model):
        print(f"WARNING: Judge model '{judge_model}' not found in Ollama.")
    
    start_time = datetime.now()
    
    # Aggregators
    total_conv_score = 0
    total_rag_precision = 0
    total_rag_recall = 0
    total_tool_accuracy = 0
    all_failures = []
    
    for i in range(num_runs):
        print(f"--- Running Evaluation Cycle {i+1}/{num_runs} ---")
        conv_res = await run_conversation_eval()
        rag_res = await evaluate_retrieval()
        tool_res = await evaluate_tool_accuracy()
        
        total_conv_score += conv_res["avg_conversational_quality"]
        total_rag_precision += rag_res["avg_precision_at_5"]
        total_rag_recall += rag_res["avg_recall_at_5"]
        total_tool_accuracy += tool_res["tool_invocation_accuracy"]
        
        # Collect failures from this run
        for detail in conv_res.get("detail", []):
            if detail["score"] < 1.0:
                all_failures.append(f"Run {i+1} | {detail['id']}: Score {detail['score']} - {detail['response'][:100]}...")

    # Calculate final averages
    avg_conv_score = total_conv_score / num_runs
    avg_rag_precision = total_rag_precision / num_runs
    avg_rag_recall = total_rag_recall / num_runs
    avg_tool_accuracy = total_tool_accuracy / num_runs

    # 2. Performance Evaluations (One run of 30 trials is usually enough for performance)
    print("--- Running Performance Benchmarks ---")
    latency_results = await run_latency_benchmarks()
    throughput_results = await run_throughput_benchmark(max_concurrency=5)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 3. Hardware Specs
    hw_info = {
        "os": platform.system(),
        "processor": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024**3), 2)} GB",
        "storage": f"{round(psutil.disk_usage('.').total / (1024**3), 2)} GB",
        "timestamp": start_time.isoformat()
    }
    
    # 4. Generate Markdown
    report = f"""# Chocomi Evaluation Report
Generated on: {start_time.strftime("%Y-%m-%d %H:%M:%S")}
Total Duration: {duration}

## 1. System Information
- **OS:** {hw_info['os']}
- **CPU:** {hw_info['processor']}
- **RAM:** {hw_info['ram']}
- **Storage:** {hw_info['storage']}
- **Judge Model:** llama3.1:8b
- **Chat Model:** qwen2.5:1.5b (Ollama)

## 2. Correctness Metrics (Averaged over 5 runs)
### Overall Conversational Quality
- **Average Score:** {avg_conv_score:.2f} / 1.0

### RAG Retrieval (at k=5)
- **Precision:** {avg_rag_precision:.2f}
- **Recall:** {avg_rag_recall:.2f}

### Tool Invocation Accuracy
- **Accuracy:** {avg_tool_accuracy:.2%}

## 3. Performance Metrics
### Latency (Seconds)
| Scenario | Avg TTFT | Med TTFT | P90 TTFT | P99 TTFT | Avg E2E | Med E2E | P90 E2E | P99 E2E |
|----------|----------|----------|----------|----------|---------|---------|---------|---------|
"""
    for name, stats in latency_results.items():
        report += f"| {name} | {stats['ttft_avg']:.3f} | {stats['ttft_med']:.3f} | {stats['ttft_p90']:.3f} | {stats['ttft_p99']:.3f} | {stats['e2e_avg']:.3f} | {stats['e2e_med']:.3f} | {stats['e2e_p90']:.3f} | {stats['e2e_p99']:.3f} |\n"

    report += "\n### Throughput (Concurrency)\n"
    report += "| Concurrency | Success Rate | Avg Session Time | Turns / Sec |\n"
    report += "|-------------|--------------|------------------|-------------|\n"
    
    for row in throughput_results:
        report += f"| {row['concurrency']} | {row['success_rate']:.2%} | {row['avg_session_time']:.2f}s | {row['turns_per_second']:.2f} |\n"

    report += "\n## 4. Test Failures / Details (Aggregated)\n"
    for failure in all_failures[:15]:
        report += f"- {failure}\n"

    # Save report
    report_path = "evals/report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Evaluation complete! Report saved to {report_path}")

if __name__ == "__main__":
    # Ensure we are in the backend directory
    if os.path.basename(os.getcwd()) != "backend":
        print("Please run this from the backend directory.")
    else:
        asyncio.run(generate_report())
