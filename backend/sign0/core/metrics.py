"""
Sign0 Real-Time Telemetry & Prometheus Metrics Instrumentation
Monitors inference throughput, P50/P99 latency, active WebSocket connections, and bandwidth.
"""

import time
from typing import Dict, Any
from collections import deque


class MetricsCollector:
    """Lightweight in-memory telemetry collector with Prometheus exposition format."""

    def __init__(self, max_history: int = 5000):
        self.inference_count = 0
        self.total_frames_streamed = 0
        self.total_bytes_transferred = 0
        self.active_websockets = 0
        self.words_assembled = 0
        self.latencies = deque(maxlen=max_history)
        self.start_time = time.time()

    def record_inference(self, latency_ms: float, bytes_count: int = 0):
        self.inference_count += 1
        self.latencies.append(latency_ms)
        self.total_bytes_transferred += bytes_count

    def increment_ws(self):
        self.active_websockets += 1

    def decrement_ws(self):
        self.active_websockets = max(0, self.active_websockets - 1)

    def record_word_assembled(self):
        self.words_assembled += 1

    def get_percentiles(self) -> Dict[str, float]:
        if not self.latencies:
            return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mean": 0.0}
        sorted_lats = sorted(self.latencies)
        n = len(sorted_lats)
        return {
            "p50": round(sorted_lats[int(n * 0.50)], 3),
            "p90": round(sorted_lats[int(n * 0.90)], 3),
            "p99": round(sorted_lats[int(n * 0.99)], 3),
            "mean": round(sum(sorted_lats) / n, 3),
        }

    def get_summary(self) -> Dict[str, Any]:
        uptime_sec = max(1.0, time.time() - self.start_time)
        percentiles = self.get_percentiles()
        return {
            "uptime_seconds": round(uptime_sec, 1),
            "total_inferences": self.inference_count,
            "inferences_per_second": round(self.inference_count / uptime_sec, 2),
            "active_websockets": self.active_websockets,
            "total_bytes_transferred": self.total_bytes_transferred,
            "total_words_assembled": self.words_assembled,
            "latency_p50_ms": percentiles["p50"],
            "latency_p99_ms": percentiles["p99"],
            "latency_mean_ms": percentiles["mean"],
        }

    def to_prometheus_format(self) -> str:
        summary = self.get_summary()
        lines = [
            "# HELP sign0_inference_requests_total Total number of ML inference requests",
            "# TYPE sign0_inference_requests_total counter",
            f"sign0_inference_requests_total {summary['total_inferences']}",
            "# HELP sign0_active_websocket_streams Current active WebSocket streams",
            "# TYPE sign0_active_websocket_streams gauge",
            f"sign0_active_websocket_streams {summary['active_websockets']}",
            "# HELP sign0_inference_latency_p50_ms 50th percentile inference latency in ms",
            "# TYPE sign0_inference_latency_p50_ms gauge",
            f"sign0_inference_latency_p50_ms {summary['latency_p50_ms']}",
            "# HELP sign0_inference_latency_p99_ms 99th percentile inference latency in ms",
            "# TYPE sign0_inference_latency_p99_ms gauge",
            f"sign0_inference_latency_p99_ms {summary['latency_p99_ms']}",
            "# HELP sign0_bytes_transferred_total Total payload bytes processed",
            "# TYPE sign0_bytes_transferred_total counter",
            f"sign0_bytes_transferred_total {summary['total_bytes_transferred']}",
            "# HELP sign0_words_assembled_total Total sign language words assembled",
            "# TYPE sign0_words_assembled_total counter",
            f"sign0_words_assembled_total {summary['total_words_assembled']}",
        ]
        return "\n".join(lines) + "\n"


metrics = MetricsCollector()
