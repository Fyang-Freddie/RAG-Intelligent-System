"""
Performance Profiler Utility
Provides decorators and context managers for measuring execution time
"""
import time
import logging
from typing import Dict, Any, List, Callable, Optional
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)

# ============================================================================
# PERFORMANCE MONITOR CLASS
# ============================================================================

class PerformanceMonitor:
    """
    Track and report performance statistics for operations
    Thread-safe singleton for collecting timing data across the application
    """
    
    _instance: Optional['PerformanceMonitor'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.timings: Dict[str, List[float]] = {}
        self.counts: Dict[str, int] = {}
        self._initialized = True
    
    def record_timing(self, operation: str, duration: float) -> None:
        """
        Record timing for an operation
        
        Args:
            operation: Name of the operation
            duration: Time taken in seconds
        """
        if operation not in self.timings:
            self.timings[operation] = []
        self.timings[operation].append(duration)
        self.counts[operation] = self.counts.get(operation, 0) + 1
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all operations
        
        Returns:
            Dictionary with statistics for each operation
        """
        summary = {}
        for operation, times in self.timings.items():
            if times:
                summary[operation] = {
                    'count': len(times),
                    'total_time': sum(times),
                    'avg_time': sum(times) / len(times),
                    'min_time': min(times),
                    'max_time': max(times)
                }
        return summary
    
    def print_summary(self) -> None:
        """Print formatted performance summary to console"""
        summary = self.get_summary()
        if not summary:
            logger.info("No performance data collected")
            return
        
        logger.info("=" * 50)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 50)
        logger.info(f"{'Operation':<35} | {'Time':>10}")
        logger.info("-" * 50)
        
        # Show most recent timing for each operation
        total = 0
        for operation in summary.keys():
            # Get the most recent timing (last item in the list)
            most_recent = self.timings[operation][-1]
            logger.info(f"{operation:<35} | {most_recent:>9.3f}s")
            total += most_recent
        
        logger.info("=" * 50)
        logger.info(f"{'TOTAL':<35} | {total:>9.3f}s")
        logger.info("=" * 50)
        
        # Clear all timing data after printing
        self.reset()
    
    def reset(self) -> None:
        """Clear all collected timing data"""
        self.timings.clear()
        self.counts.clear()


# ============================================================================
# GLOBAL INSTANCE AND ACCESS FUNCTIONS
# ============================================================================

def get_performance_monitor() -> PerformanceMonitor:
    """
    Get global performance monitor instance (singleton)
    
    Returns:
        The global PerformanceMonitor instance
    """
    return PerformanceMonitor()


def print_performance_summary() -> None:
    """Print performance summary for all tracked operations"""
    get_performance_monitor().print_summary()


def reset_performance_data() -> None:
    """Reset all performance tracking data"""
    get_performance_monitor().reset()


# ============================================================================
# CONTEXT MANAGER FOR TRACKING PERFORMANCE
# ============================================================================

@contextmanager
def track_performance(operation_name: str):
    """
    Context manager to track operation performance
    
    Usage:
        with track_performance("image_processing"):
            process_image()
    
    Args:
        operation_name: Name of the operation being tracked
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        get_performance_monitor().record_timing(operation_name, duration)
        logger.debug(f"{operation_name} completed in {duration:.3f}s")


# ============================================================================
# DECORATOR FOR AUTOMATIC PERFORMANCE TRACKING
# ============================================================================

def timed_operation(operation_name: Optional[str] = None):
    """
    Decorator to automatically track function performance
    
    Usage:
        @timed_operation("process_file")
        def process_file(data):
            ...
    
    Or (uses function name as operation name):
        @timed_operation()
        def process_image(data):
            ...
    
    Args:
        operation_name: Optional name for the operation (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        name = operation_name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with track_performance(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# CLASS DECORATOR FOR TRACKING ALL METHODS
# ============================================================================

def profile_class(cls):
    """
    Class decorator to automatically profile all public methods
    
    Usage:
        @profile_class
        class MyProcessor:
            def process(self):
                ...
    
    This will track timing for all methods except those starting with '_'
    """
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if callable(attr) and not attr_name.startswith('_'):
            setattr(cls, attr_name, timed_operation(f"{cls.__name__}.{attr_name}")(attr))
    return cls
