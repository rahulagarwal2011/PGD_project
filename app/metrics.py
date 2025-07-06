import time
import statistics

class Benchmark:
    def __init__(self):
        self.latencies = []
        self.errors = 0
        self.start_time = time.time()
    
    def record_latency(self, latency):
        self.latencies.append(latency)
    
    def record_error(self):
        self.errors += 1
    
    def summary(self):
        total_time = time.time() - self.start_time
        count = len(self.latencies)
        throughput = count / total_time if total_time > 0 else 0
        avg = statistics.mean(self.latencies) if count else 0
        stddev = statistics.stdev(self.latencies) if count > 1 else 0
        min_l = min(self.latencies) if count else 0
        max_l = max(self.latencies) if count else 0
        error_rate = (self.errors / (count + self.errors)) * 100 if (count + self.errors) else 0

        return {
            "average_latency": avg,
            "stddev_latency": stddev,
            "min_latency": min_l,
            "max_latency": max_l,
            "throughput": throughput,
            "error_rate": error_rate
        }

def reset(self):
    self.latencies.clear()
    self.errors = 0
    self.start_time = time.time()

# ✅ Global instances
rsa_benchmark = Benchmark()
pqc_benchmark = Benchmark()
