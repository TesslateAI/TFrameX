#!/usr/bin/env python3
"""
TFrameX Enterprise Performance Benchmark

This script benchmarks enterprise features to ensure they meet
performance requirements.
"""

import asyncio
import logging
import time
import statistics
from pathlib import Path
from typing import List, Dict, Any

# Load test environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env.test")

from tframex.enterprise import (
    EnterpriseApp, create_default_config,
    create_storage_backend, MetricsManager
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmark runner for enterprise features."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
    
    async def benchmark_storage_operations(self, iterations: int = 1000):
        """Benchmark storage operations."""
        logger.info(f"Benchmarking storage operations ({iterations} iterations)...")
        
        storage = await create_storage_backend("memory", {})
        
        # Benchmark insert operations
        insert_times = []
        for i in range(iterations):
            start_time = time.perf_counter()
            await storage.insert("benchmark", {
                "id": f"record_{i}",
                "data": f"test_data_{i}",
                "value": i,
                "metadata": {"benchmark": True}
            })
            end_time = time.perf_counter()
            insert_times.append((end_time - start_time) * 1000)  # Convert to ms
        
        # Benchmark select operations
        select_times = []
        for i in range(min(iterations, 100)):  # Limit selects to avoid too much data
            start_time = time.perf_counter()
            await storage.select("benchmark", filters={"id": f"record_{i}"})
            end_time = time.perf_counter()
            select_times.append((end_time - start_time) * 1000)
        
        self.results["storage"] = {
            "insert_operations": {
                "mean_ms": statistics.mean(insert_times),
                "median_ms": statistics.median(insert_times),
                "max_ms": max(insert_times),
                "min_ms": min(insert_times),
                "ops_per_second": 1000 / statistics.mean(insert_times)
            },
            "select_operations": {
                "mean_ms": statistics.mean(select_times),
                "median_ms": statistics.median(select_times),
                "max_ms": max(select_times),
                "min_ms": min(select_times),
                "ops_per_second": 1000 / statistics.mean(select_times)
            }
        }
        
        logger.info(f"Storage insert: {self.results['storage']['insert_operations']['ops_per_second']:.1f} ops/sec")
        logger.info(f"Storage select: {self.results['storage']['select_operations']['ops_per_second']:.1f} ops/sec")
    
    async def benchmark_metrics_collection(self, iterations: int = 1000):
        """Benchmark metrics collection."""
        logger.info(f"Benchmarking metrics collection ({iterations} iterations)...")
        
        config = {
            "enabled": True,
            "backends": {
                "test_custom": {
                    "type": "custom",
                    "enabled": True,
                    "backend_class": "tframex.enterprise.metrics.custom.LoggingMetricsBackend",
                    "backend_config": {"log_level": "ERROR"}  # Reduce logging for benchmark
                }
            },
            "collection_interval": 60,  # Long interval to avoid background collection
            "buffer_size": iterations + 100
        }
        
        metrics_manager = MetricsManager(config)
        await metrics_manager.start()
        
        try:
            # Benchmark counter operations
            counter_times = []
            for i in range(iterations):
                start_time = time.perf_counter()
                await metrics_manager.increment_counter(
                    "benchmark.counter",
                    value=1,
                    labels={"iteration": str(i)}
                )
                end_time = time.perf_counter()
                counter_times.append((end_time - start_time) * 1000)
            
            # Benchmark gauge operations
            gauge_times = []
            for i in range(iterations):
                start_time = time.perf_counter()
                await metrics_manager.set_gauge(
                    "benchmark.gauge",
                    value=float(i),
                    labels={"iteration": str(i)}
                )
                end_time = time.perf_counter()
                gauge_times.append((end_time - start_time) * 1000)
            
            self.results["metrics"] = {
                "counter_operations": {
                    "mean_ms": statistics.mean(counter_times),
                    "median_ms": statistics.median(counter_times),
                    "max_ms": max(counter_times),
                    "min_ms": min(counter_times),
                    "ops_per_second": 1000 / statistics.mean(counter_times)
                },
                "gauge_operations": {
                    "mean_ms": statistics.mean(gauge_times),
                    "median_ms": statistics.median(gauge_times),
                    "max_ms": max(gauge_times),
                    "min_ms": min(gauge_times),
                    "ops_per_second": 1000 / statistics.mean(gauge_times)
                }
            }
            
            logger.info(f"Metrics counter: {self.results['metrics']['counter_operations']['ops_per_second']:.1f} ops/sec")
            logger.info(f"Metrics gauge: {self.results['metrics']['gauge_operations']['ops_per_second']:.1f} ops/sec")
        
        finally:
            await metrics_manager.stop()
    
    async def benchmark_authentication(self, iterations: int = 100):
        """Benchmark authentication operations."""
        logger.info(f"Benchmarking authentication ({iterations} iterations)...")
        
        from tframex.enterprise.security.auth import APIKeyProvider
        from uuid import uuid4
        
        storage = await create_storage_backend("memory", {})
        
        # Setup test users
        test_keys = []
        for i in range(iterations):
            user_id = uuid4()
            user_data = {
                "id": str(user_id),
                "username": f"user_{i}",
                "email": f"user_{i}@example.com",
                "is_active": True
            }
            await storage.insert("users", user_data)
            
            # Create API key provider and generate key
            provider = APIKeyProvider({"storage": storage, "key_length": 32})
            await provider.initialize()
            api_key = await provider.create_api_key(user_id)
            test_keys.append(api_key)
        
        # Benchmark authentication
        auth_times = []
        provider = APIKeyProvider({"storage": storage, "key_length": 32})
        await provider.initialize()
        
        for api_key in test_keys:
            start_time = time.perf_counter()
            result = await provider.authenticate({"api_key": api_key})
            end_time = time.perf_counter()
            auth_times.append((end_time - start_time) * 1000)
            
            if not result.success:
                logger.warning("Authentication failed during benchmark")
        
        self.results["authentication"] = {
            "operations": {
                "mean_ms": statistics.mean(auth_times),
                "median_ms": statistics.median(auth_times),
                "max_ms": max(auth_times),
                "min_ms": min(auth_times),
                "ops_per_second": 1000 / statistics.mean(auth_times)
            }
        }
        
        logger.info(f"Authentication: {self.results['authentication']['operations']['ops_per_second']:.1f} ops/sec")
    
    async def benchmark_enterprise_app_startup(self, iterations: int = 5):
        """Benchmark enterprise app startup time."""
        logger.info(f"Benchmarking enterprise app startup ({iterations} iterations)...")
        
        startup_times = []
        
        for i in range(iterations):
            config = create_default_config(environment="test")
            
            start_time = time.perf_counter()
            
            app = EnterpriseApp(
                enterprise_config=config,
                auto_initialize=False
            )
            
            await app.initialize_enterprise()
            await app.start_enterprise()
            
            end_time = time.perf_counter()
            startup_time = (end_time - start_time) * 1000
            startup_times.append(startup_time)
            
            # Clean shutdown
            await app.stop_enterprise()
            
            logger.info(f"Startup {i+1}: {startup_time:.1f}ms")
        
        self.results["startup"] = {
            "mean_ms": statistics.mean(startup_times),
            "median_ms": statistics.median(startup_times),
            "max_ms": max(startup_times),
            "min_ms": min(startup_times)
        }
        
        logger.info(f"Average startup time: {self.results['startup']['mean_ms']:.1f}ms")
    
    def print_summary(self):
        """Print benchmark summary."""
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE BENCHMARK SUMMARY")
        logger.info("="*60)
        
        for category, metrics in self.results.items():
            logger.info(f"\n{category.upper()}:")
            
            if "operations" in metrics:
                ops = metrics["operations"]
                logger.info(f"  Operations/sec: {ops['ops_per_second']:.1f}")
                logger.info(f"  Mean latency: {ops['mean_ms']:.2f}ms")
                logger.info(f"  Median latency: {ops['median_ms']:.2f}ms")
                logger.info(f"  Max latency: {ops['max_ms']:.2f}ms")
            
            else:
                for operation, stats in metrics.items():
                    if isinstance(stats, dict) and 'ops_per_second' in stats:
                        logger.info(f"  {operation}:")
                        logger.info(f"    Operations/sec: {stats['ops_per_second']:.1f}")
                        logger.info(f"    Mean latency: {stats['mean_ms']:.2f}ms")
                    elif isinstance(stats, (int, float)):
                        logger.info(f"  {operation}: {stats:.2f}ms")
        
        # Performance thresholds
        logger.info(f"\nPERFORMANCE ANALYSIS:")
        
        # Check storage performance
        if "storage" in self.results:
            insert_ops = self.results["storage"]["insert_operations"]["ops_per_second"]
            if insert_ops < 1000:
                logger.warning(f"⚠️  Storage insert performance below 1000 ops/sec: {insert_ops:.1f}")
            else:
                logger.info(f"✅ Storage insert performance good: {insert_ops:.1f} ops/sec")
        
        # Check metrics performance
        if "metrics" in self.results:
            counter_ops = self.results["metrics"]["counter_operations"]["ops_per_second"]
            if counter_ops < 5000:
                logger.warning(f"⚠️  Metrics performance below 5000 ops/sec: {counter_ops:.1f}")
            else:
                logger.info(f"✅ Metrics performance good: {counter_ops:.1f} ops/sec")
        
        # Check startup time
        if "startup" in self.results:
            startup_time = self.results["startup"]["mean_ms"]
            if startup_time > 5000:  # 5 seconds
                logger.warning(f"⚠️  Startup time above 5s: {startup_time:.1f}ms")
            else:
                logger.info(f"✅ Startup time good: {startup_time:.1f}ms")


async def main():
    """Run performance benchmarks."""
    logger.info("Starting TFrameX Enterprise performance benchmarks...")
    
    benchmark = PerformanceBenchmark()
    
    try:
        # Run benchmarks
        await benchmark.benchmark_storage_operations(1000)
        await benchmark.benchmark_metrics_collection(1000)
        await benchmark.benchmark_authentication(100)
        await benchmark.benchmark_enterprise_app_startup(3)
        
        # Print results
        benchmark.print_summary()
        
        logger.info("\n🎉 Performance benchmarks completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Benchmark failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)