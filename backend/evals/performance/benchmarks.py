import time
import asyncio
import statistics
import httpx
import json
from config import settings
from llm_engine import stream_response
from conversation_manager import ConversationSession

async def measure_latency(scenario_name: str, query: str):
    """Measures latency for a single turn."""
    session = ConversationSession(userId="bench_user")
    await session.ingestUserTurn(query)
    messages = session.buildMessages()
    
    start_time = time.perf_counter()
    ttft = 0
    tokens = 0
    
    reply_parts = []
    async for token in stream_response(messages):
        if tokens == 0:
            ttft = time.perf_counter() - start_time
        tokens += 1
        reply_parts.append(token)
    
    end_time = time.perf_counter()
    e2e_time = end_time - start_time
    
    inter_token_latency = (e2e_time - ttft) / (tokens - 1) if tokens > 1 else 0
    
    return {
        "scenario": scenario_name,
        "ttft": ttft,
        "inter_token": inter_token_latency,
        "e2e": e2e_time,
        "tokens": tokens
    }

async def run_latency_benchmarks():
    scenarios = [
        ("simple", "Hello, how are you?"),
        ("rag", "What is your return policy for GPUs?"),
        ("tool", "Calculate 1234 * 56"),
        ("mixed", "I prefer NVIDIA. What is the price of the RTX 4090?")
    ]
    
    results = {s[0]: [] for s in scenarios}
    
    print("Running latency benchmarks (30 trials per scenario)...")
    for name, query in scenarios:
        for _ in range(30):
            res = await measure_latency(name, query)
            results[name].append(res)
            
    summary = {}
    for name, data in results.items():
        ttfts = sorted([r["ttft"] for r in data])
        e2es = sorted([r["e2e"] for r in data])
        summary[name] = {
            "ttft_avg": statistics.mean(ttfts),
            "ttft_med": statistics.median(ttfts),
            "ttft_p90": statistics.quantiles(ttfts, n=10)[8],
            "ttft_p99": statistics.quantiles(ttfts, n=100)[98],
            "e2e_avg": statistics.mean(e2es),
            "e2e_med": statistics.median(e2es),
            "e2e_p90": statistics.quantiles(e2es, n=10)[8],
            "e2e_p99": statistics.quantiles(e2es, n=100)[98]
        }
    return summary

async def run_throughput_benchmark(max_concurrency: int = 5):
    """Simulates concurrent users and measures success rate and latency."""
    
    async def simulate_user(user_id: int):
        start = time.perf_counter()
        try:
            # Each user does 3 turns
            session = ConversationSession(userId=f"concurrent_{user_id}")
            for i in range(3):
                await session.ingestUserTurn(f"Message {i} from user {user_id}")
                messages = session.buildMessages()
                async for _ in stream_response(messages):
                    pass
            return time.perf_counter() - start, True
        except:
            return 0, False

    print(f"Running throughput benchmark with up to {max_concurrency} concurrent users...")
    
    report = []
    for c in range(1, max_concurrency + 1):
        tasks = [simulate_user(i) for i in range(c)]
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start_time
        
        successes = [r[1] for r in results if r[1]]
        avg_user_time = statistics.mean([r[0] for r in results if r[1]]) if successes else 0
        
        report.append({
            "concurrency": c,
            "success_rate": len(successes) / c,
            "avg_session_time": avg_user_time,
            "total_time": total_time,
            "turns_per_second": (c * 3) / total_time
        })
        
    return report

if __name__ == "__main__":
    print("Running Latency Benchmarks (30 trials per scenario)...")
    latency_res = asyncio.run(run_latency_benchmarks())
    for name, stats in latency_res.items():
        print(f"\nScenario: {name}")
        print(f"  Avg TTFT: {stats['ttft_avg']:.3f}s | P90: {stats['ttft_p90']:.3f}s")
        print(f"  Avg E2E:  {stats['e2e_avg']:.3f}s | P90: {stats['e2e_p90']:.3f}s")

    print("\n" + "="*30)
    print("Running Throughput Benchmarks (Concurrency 1-5)...")
    throughput_res = asyncio.run(run_throughput_benchmark())
    print(f"{'Users':<6} | {'Success':<8} | {'Avg Session':<12} | {'Turns/Sec':<10}")
    for r in throughput_res:
        print(f"{r['concurrency']:<6} | {r['success_rate']:<8.0%} | {r['avg_session_time']:<11.2f}s | {r['turns_per_second']:<10.2f}")
