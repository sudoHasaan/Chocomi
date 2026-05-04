# Chocomi Evaluation Report
Generated on: 2026-05-04 13:30:34
Total Duration: 0:03:40.817954

## 1. System Information
- **OS:** Windows
- **CPU:** Intel64 Family 6 Model 151 Stepping 5, GenuineIntel
- **RAM:** 15.86 GB
- **Storage:** 585.67 GB
- **Judge Model:** llama3.1:8b
- **Chat Model:** qwen2.5:1.5b (Ollama)

## 2. Correctness Metrics (Averaged over 5 runs)
### Overall Conversational Quality
- **Average Score:** 0.74 / 1.0

### RAG Retrieval (at k=5)
- **Precision:** 0.30
- **Recall:** 1.00

### Tool Invocation Accuracy
- **Accuracy:** 36.00%

## 3. Performance Metrics
### Latency (Seconds)
| Scenario | Avg TTFT | Med TTFT | P90 TTFT | P99 TTFT | Avg E2E | Med E2E | P90 E2E | P99 E2E |
|----------|----------|----------|----------|----------|---------|---------|---------|---------|
| simple | 0.346 | 0.345 | 0.353 | 0.403 | 0.466 | 0.465 | 0.473 | 0.524 |
| rag | 0.346 | 0.345 | 0.353 | 0.398 | 0.928 | 0.903 | 1.088 | 1.138 |
| tool | 0.422 | 0.419 | 0.435 | 0.459 | 0.493 | 0.493 | 0.500 | 0.544 |
| mixed | 0.344 | 0.341 | 0.352 | 0.391 | 0.470 | 0.466 | 0.486 | 0.506 |

### Throughput (Concurrency)
| Concurrency | Success Rate | Avg Session Time | Turns / Sec |
|-------------|--------------|------------------|-------------|
| 1 | 100.00% | 1.97s | 1.52 |
| 2 | 100.00% | 2.40s | 2.39 |
| 3 | 100.00% | 2.30s | 3.56 |
| 4 | 100.00% | 2.65s | 4.05 |
| 5 | 100.00% | 3.30s | 3.86 |

## 4. Test Failures / Details (Aggregated)
- Run 1 | conv_01_product_inquiry: Score 0.0 - I'm sorry, but I don't have that info. We specialize in PC Hardware! Call us at +1 (555) 010-4090....
- Run 1 | conv_03_crm_personalization: Score 0.5 - Your name is Alex, and you prefer NVIDIA GPUs....
- Run 1 | conv_08_hallucination_check: Score 0.0 - I'm sorry, but I don't have any information about a specific product called "ByteBodega Quantum GPU"...
- Run 2 | conv_01_product_inquiry: Score 0.0 - I'm sorry, but I don't have that info. We specialize in PC Hardware! Call us at +1 (555) 010-4090 fo...
- Run 2 | conv_03_crm_personalization: Score 0.5 - Your name is Alex, and you prefer NVIDIA GPUs....
- Run 2 | conv_07_complex_rag_compare: Score 0.0 - Both the NVIDIA RTX 4070 Super and the RTX 4080 are excellent choices for high-performance 4K gaming...
- Run 3 | conv_01_product_inquiry: Score 0.0 - I'm sorry, but I don't have that info. We specialize in PC Hardware! Call us at +1 (555) 010-4090....
- Run 3 | conv_03_crm_personalization: Score 0.5 - You mentioned your name is Alex, and you prefer NVIDIA GPUs....
- Run 3 | conv_07_complex_rag_compare: Score 0.0 - The NVIDIA RTX 4080 Super 16GB is generally considered a better choice for 4K gaming compared to the...
- Run 3 | conv_09_multi_turn_build: Score 0.5 - For video editing, the **AMD Ryzen 9 5900X** is a great choice. It's powerful enough for most video ...
- Run 4 | conv_01_product_inquiry: Score 0.0 - I'm sorry, but I don't have that info. We specialize in PC Hardware! Call us at +1 (555) 010-4090....
- Run 4 | conv_03_crm_personalization: Score 0.5 - You mentioned your name is Alex, and you prefer NVIDIA GPUs....
- Run 4 | conv_07_complex_rag_compare: Score 0.0 - Both the NVIDIA RTX 4070 Super and the RTX 4080 are excellent choices for high-performance 4K gaming...
- Run 5 | conv_01_product_inquiry: Score 0.0 - I'm sorry, but I don't have that info. We specialize in PC Hardware! Call us at +1 (555) 010-4090....
- Run 5 | conv_03_crm_personalization: Score 0.5 - Your name is Alex, and you prefer NVIDIA GPUs....
