"""
Phase 2: Real-Time Scheduler
Infrastructure Layer - RT kernel optimization

Leverages Linux RT kernel for:
- Predictable latency
- Priority-based scheduling
- Better concurrent performance

Requires: Linux with PREEMPT_RT patch (Arch Linux RT kernel)
"""

import os
import sys
from typing import Callable, Any
from functools import wraps
import asyncio


class RTScheduler:
    """
    Real-Time Process Scheduler

    Single Responsibility: Manage process priorities

    Use for:
    - Critical agent operations
    - Embedding generation
    - LLM inference calls
    - MCP server communication
    """

    # RT scheduling policies (Linux)
    SCHED_FIFO = 1  # First-In-First-Out
    SCHED_RR = 2    # Round-Robin
    SCHED_OTHER = 0  # Normal scheduling

    # Priority levels (1-99, higher = more priority)
    PRIORITY_CRITICAL = 80   # Critical operations
    PRIORITY_HIGH = 60       # Important operations
    PRIORITY_NORMAL = 40     # Standard operations
    PRIORITY_LOW = 20        # Background tasks

    @staticmethod
    def is_rt_available() -> bool:
        """Check if RT scheduling is available"""
        if sys.platform != "linux":
            return False

        try:
            # Check if we can set scheduling policy
            current_policy = os.sched_getscheduler(0)
            return True
        except (AttributeError, OSError):
            return False

    @staticmethod
    def set_priority(
        priority: int = PRIORITY_NORMAL,
        policy: int = SCHED_FIFO
    ) -> bool:
        """
        Set RT priority for current process

        Args:
            priority: 1-99 (higher = more priority)
            policy: SCHED_FIFO, SCHED_RR, or SCHED_OTHER

        Returns:
            True if successful, False otherwise

        Requires:
            - Linux RT kernel
            - CAP_SYS_NICE capability or root
        """
        if not RTScheduler.is_rt_available():
            return False

        try:
            param = os.sched_param(priority)
            os.sched_setscheduler(0, policy, param)
            return True
        except PermissionError:
            print(
                "Warning: RT scheduling requires elevated privileges. "
                "Run with: sudo setcap cap_sys_nice=eip /usr/bin/python3"
            )
            return False
        except Exception as e:
            print(f"Warning: Could not set RT priority: {e}")
            return False

    @staticmethod
    def get_current_priority() -> dict:
        """Get current scheduling info"""
        try:
            policy = os.sched_getscheduler(0)
            param = os.sched_getparam(0)

            policy_names = {
                RTScheduler.SCHED_FIFO: "SCHED_FIFO",
                RTScheduler.SCHED_RR: "SCHED_RR",
                RTScheduler.SCHED_OTHER: "SCHED_OTHER"
            }

            return {
                "policy": policy_names.get(policy, "UNKNOWN"),
                "priority": param.sched_priority
            }
        except Exception:
            return {"policy": "UNAVAILABLE", "priority": 0}

    @staticmethod
    def with_priority(priority: int = PRIORITY_NORMAL):
        """
        Decorator to run function with RT priority

        Usage:
            @RTScheduler.with_priority(RTScheduler.PRIORITY_HIGH)
            async def critical_operation():
                # This runs with high priority
                pass
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                # Save current priority
                original_info = RTScheduler.get_current_priority()

                # Set new priority
                RTScheduler.set_priority(priority)

                try:
                    # Execute function
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    # Restore original priority
                    if original_info["policy"] != "UNAVAILABLE":
                        policy_map = {
                            "SCHED_FIFO": RTScheduler.SCHED_FIFO,
                            "SCHED_RR": RTScheduler.SCHED_RR,
                            "SCHED_OTHER": RTScheduler.SCHED_OTHER
                        }
                        original_policy = policy_map.get(
                            original_info["policy"],
                            RTScheduler.SCHED_OTHER
                        )
                        RTScheduler.set_priority(
                            original_info["priority"],
                            original_policy
                        )

            @wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                original_info = RTScheduler.get_current_priority()
                RTScheduler.set_priority(priority)

                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    if original_info["policy"] != "UNAVAILABLE":
                        policy_map = {
                            "SCHED_FIFO": RTScheduler.SCHED_FIFO,
                            "SCHED_RR": RTScheduler.SCHED_RR,
                            "SCHED_OTHER": RTScheduler.SCHED_OTHER
                        }
                        original_policy = policy_map.get(
                            original_info["policy"],
                            RTScheduler.SCHED_OTHER
                        )
                        RTScheduler.set_priority(
                            original_info["priority"],
                            original_policy
                        )

            # Return appropriate wrapper
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator


class PerformanceOptimizer:
    """
    Additional performance optimizations for RT kernel

    Combines RT scheduling with other optimizations:
    - CPU affinity
    - Memory locking
    - Cache optimization
    """

    @staticmethod
    def set_cpu_affinity(cpu_ids: list[int]) -> bool:
        """
        Pin process to specific CPU cores

        Useful for: Reducing context switches
        """
        try:
            os.sched_setaffinity(0, cpu_ids)
            return True
        except (AttributeError, OSError):
            return False

    @staticmethod
    def get_cpu_count() -> int:
        """Get number of available CPUs"""
        return os.cpu_count() or 1

    @staticmethod
    def optimize_for_inference():
        """
        Apply optimizations for LLM inference

        Recommendations:
        - High priority for inference
        - Pin to performance cores
        - Lock memory to prevent swapping
        """
        if not RTScheduler.is_rt_available():
            print("RT scheduling not available - using normal priority")
            return

        # Set high priority
        success = RTScheduler.set_priority(
            RTScheduler.PRIORITY_HIGH,
            RTScheduler.SCHED_FIFO
        )

        if success:
            print("✓ RT priority set for inference")

        # Pin to last CPU (often performance core on hybrid CPUs)
        cpu_count = PerformanceOptimizer.get_cpu_count()
        if cpu_count > 1:
            PerformanceOptimizer.set_cpu_affinity([cpu_count - 1])
            print(f"✓ Pinned to CPU {cpu_count - 1}")


# Example usage
async def example_rt_usage():
    """Demonstrate RT scheduling"""

    print("RT Scheduler Demo")
    print("=" * 60)

    # Check availability
    print(f"RT scheduling available: {RTScheduler.is_rt_available()}")

    # Get current status
    info = RTScheduler.get_current_priority()
    print(f"Current policy: {info['policy']}")
    print(f"Current priority: {info['priority']}")

    # Example: Critical operation with high priority
    @RTScheduler.with_priority(RTScheduler.PRIORITY_HIGH)
    async def critical_embedding_generation():
        """Simulate embedding generation"""
        import time
        start = time.time()
        await asyncio.sleep(0.1)  # Simulate work
        elapsed = time.time() - start
        print(f"  Embedding generated in {elapsed:.3f}s")

    # Example: Normal priority operation
    @RTScheduler.with_priority(RTScheduler.PRIORITY_NORMAL)
    async def normal_search():
        """Simulate search"""
        import time
        start = time.time()
        await asyncio.sleep(0.1)
        elapsed = time.time() - start
        print(f"  Search completed in {elapsed:.3f}s")

    print("\nRunning operations:")
    await critical_embedding_generation()
    await normal_search()

    print("\n" + "=" * 60)
    print("Setup for production:")
    print("  1. Install RT kernel: sudo pacman -S linux-rt linux-rt-headers")
    print("  2. Grant capability: sudo setcap cap_sys_nice=eip /usr/bin/python3")
    print("  3. Reboot into RT kernel")
    print("  4. Run your application")


if __name__ == "__main__":
    asyncio.run(example_rt_usage())
