#!/usr/bin/env python3
"""
Metrics Collector Module

Performance metrics collection and export for HFT-PacketFilter package.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import json
import csv
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from dataclasses import dataclass, field
import psutil
import os


@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: float
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp,
            "name": self.name,
            "value": self.value,
            "tags": self.tags
        }


class MetricsCollector:
    """
    High-performance metrics collection system
    
    Features:
    - Real-time metrics collection
    - Multiple export formats
    - Configurable retention
    - Thread-safe operations
    - System resource monitoring
    """
    
    def __init__(self, 
                 export_format: str = "json",
                 retention_seconds: int = 3600,
                 collection_interval: int = 60):
        """
        Initialize metrics collector
        
        Args:
            export_format: Export format ('json', 'prometheus', 'influxdb', 'csv')
            retention_seconds: How long to keep metrics in memory
            collection_interval: System metrics collection interval
        """
        self.export_format = export_format
        self.retention_seconds = retention_seconds
        self.collection_interval = collection_interval
        
        # Metrics storage
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # System monitoring
        self.system_monitoring_enabled = False
        self.system_monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Performance tracking
        self.start_time = time.time()
        self.total_metrics_collected = 0
    
    def enable_system_monitoring(self):
        """Enable automatic system metrics collection"""
        if not self.system_monitoring_enabled:
            self.system_monitoring_enabled = True
            self._stop_event.clear()
            self.system_monitor_thread = threading.Thread(
                target=self._system_monitor_loop,
                daemon=True
            )
            self.system_monitor_thread.start()
    
    def disable_system_monitoring(self):
        """Disable system metrics collection"""
        if self.system_monitoring_enabled:
            self.system_monitoring_enabled = False
            self._stop_event.set()
            if self.system_monitor_thread:
                self.system_monitor_thread.join(timeout=5)
    
    def _system_monitor_loop(self):
        """System monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self._collect_system_metrics()
                self._stop_event.wait(self.collection_interval)
            except Exception as e:
                # Log error but continue monitoring
                pass
    
    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        timestamp = time.time()
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_gauge("system.cpu.usage_percent", cpu_percent, timestamp=timestamp)
            
            # Memory metrics
            memory = psutil.virtual_memory()
            self.record_gauge("system.memory.usage_percent", memory.percent, timestamp=timestamp)
            self.record_gauge("system.memory.available_bytes", memory.available, timestamp=timestamp)
            self.record_gauge("system.memory.used_bytes", memory.used, timestamp=timestamp)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            self.record_gauge("system.disk.usage_percent", 
                            (disk.used / disk.total) * 100, timestamp=timestamp)
            self.record_gauge("system.disk.free_bytes", disk.free, timestamp=timestamp)
            
            # Network metrics
            network = psutil.net_io_counters()
            self.record_counter("system.network.bytes_sent", network.bytes_sent, timestamp=timestamp)
            self.record_counter("system.network.bytes_recv", network.bytes_recv, timestamp=timestamp)
            self.record_counter("system.network.packets_sent", network.packets_sent, timestamp=timestamp)
            self.record_counter("system.network.packets_recv", network.packets_recv, timestamp=timestamp)
            
            # Process metrics
            process = psutil.Process()
            self.record_gauge("process.cpu.usage_percent", process.cpu_percent(), timestamp=timestamp)
            self.record_gauge("process.memory.rss_bytes", process.memory_info().rss, timestamp=timestamp)
            self.record_gauge("process.memory.vms_bytes", process.memory_info().vms, timestamp=timestamp)
            self.record_gauge("process.threads.count", process.num_threads(), timestamp=timestamp)
            
            # File descriptors (Unix only)
            try:
                self.record_gauge("process.fd.count", process.num_fds(), timestamp=timestamp)
            except AttributeError:
                pass  # Windows doesn't have num_fds
            
        except Exception as e:
            # Log error but don't fail
            pass
    
    def record_counter(self, name: str, value: float = 1.0, 
                      tags: Optional[Dict[str, str]] = None, 
                      timestamp: Optional[float] = None):
        """Record counter metric (monotonically increasing)"""
        timestamp = timestamp or time.time()
        tags = tags or {}
        
        with self._lock:
            self.counters[name] += value
            metric = MetricPoint(timestamp, name, self.counters[name], tags)
            self.metrics[name].append(metric)
            self.total_metrics_collected += 1
            self._cleanup_old_metrics()
    
    def record_gauge(self, name: str, value: float, 
                    tags: Optional[Dict[str, str]] = None,
                    timestamp: Optional[float] = None):
        """Record gauge metric (point-in-time value)"""
        timestamp = timestamp or time.time()
        tags = tags or {}
        
        with self._lock:
            self.gauges[name] = value
            metric = MetricPoint(timestamp, name, value, tags)
            self.metrics[name].append(metric)
            self.total_metrics_collected += 1
            self._cleanup_old_metrics()
    
    def record_histogram(self, name: str, value: float,
                        tags: Optional[Dict[str, str]] = None,
                        timestamp: Optional[float] = None):
        """Record histogram metric (distribution of values)"""
        timestamp = timestamp or time.time()
        tags = tags or {}
        
        with self._lock:
            self.histograms[name].append(value)
            # Keep only recent values for histogram
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            
            metric = MetricPoint(timestamp, name, value, tags)
            self.metrics[name].append(metric)
            self.total_metrics_collected += 1
            self._cleanup_old_metrics()
    
    def record_timing(self, name: str, duration_ms: float,
                     tags: Optional[Dict[str, str]] = None,
                     timestamp: Optional[float] = None):
        """Record timing metric"""
        self.record_histogram(f"{name}.duration_ms", duration_ms, tags, timestamp)
    
    def increment(self, name: str, value: float = 1.0,
                 tags: Optional[Dict[str, str]] = None):
        """Increment counter by value"""
        self.record_counter(name, value, tags)
    
    def set_gauge(self, name: str, value: float,
                 tags: Optional[Dict[str, str]] = None):
        """Set gauge to specific value"""
        self.record_gauge(name, value, tags)
    
    def time_function(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Decorator/context manager for timing functions"""
        return TimingContext(self, name, tags)
    
    def _cleanup_old_metrics(self):
        """Remove old metrics beyond retention period"""
        cutoff_time = time.time() - self.retention_seconds
        
        for metric_name, metric_deque in self.metrics.items():
            # Remove old metrics from the left of deque
            while metric_deque and metric_deque[0].timestamp < cutoff_time:
                metric_deque.popleft()
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metric values"""
        with self._lock:
            current_metrics = {
                "timestamp": time.time(),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {}
            }
            
            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    import statistics
                    current_metrics["histograms"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
            
            return current_metrics
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100.0) * len(sorted_values))
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]
    
    def get_metric_history(self, name: str, 
                          start_time: Optional[float] = None,
                          end_time: Optional[float] = None) -> List[MetricPoint]:
        """Get historical data for a specific metric"""
        with self._lock:
            if name not in self.metrics:
                return []
            
            start_time = start_time or (time.time() - 3600)  # Default to last hour
            end_time = end_time or time.time()
            
            return [
                metric for metric in self.metrics[name]
                if start_time <= metric.timestamp <= end_time
            ]
    
    def update_metrics(self, metrics_dict: Dict[str, Any]):
        """Update multiple metrics at once"""
        timestamp = time.time()
        
        for name, value in metrics_dict.items():
            if isinstance(value, (int, float)):
                self.record_gauge(name, float(value), timestamp=timestamp)
    
    def export_metrics(self, format: Optional[str] = None) -> str:
        """Export metrics in specified format"""
        format = format or self.export_format
        
        if format == "json":
            return self._export_json()
        elif format == "prometheus":
            return self._export_prometheus()
        elif format == "influxdb":
            return self._export_influxdb()
        elif format == "csv":
            return self._export_csv()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_json(self) -> str:
        """Export metrics as JSON"""
        current_metrics = self.get_current_metrics()
        
        # Add metadata
        export_data = {
            "metadata": {
                "export_time": time.time(),
                "collector_uptime": time.time() - self.start_time,
                "total_metrics_collected": self.total_metrics_collected,
                "retention_seconds": self.retention_seconds
            },
            "metrics": current_metrics
        }
        
        return json.dumps(export_data, indent=2)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        current_metrics = self.get_current_metrics()
        
        # Export counters
        for name, value in current_metrics["counters"].items():
            prometheus_name = name.replace(".", "_")
            lines.append(f"# TYPE {prometheus_name} counter")
            lines.append(f"{prometheus_name} {value}")
        
        # Export gauges
        for name, value in current_metrics["gauges"].items():
            prometheus_name = name.replace(".", "_")
            lines.append(f"# TYPE {prometheus_name} gauge")
            lines.append(f"{prometheus_name} {value}")
        
        # Export histograms
        for name, stats in current_metrics["histograms"].items():
            prometheus_name = name.replace(".", "_")
            lines.append(f"# TYPE {prometheus_name} histogram")
            lines.append(f"{prometheus_name}_count {stats['count']}")
            lines.append(f"{prometheus_name}_sum {stats['mean'] * stats['count']}")
            lines.append(f"{prometheus_name}_bucket{{le=\"+Inf\"}} {stats['count']}")
        
        return "\n".join(lines)
    
    def _export_influxdb(self) -> str:
        """Export metrics in InfluxDB line protocol format"""
        lines = []
        current_metrics = self.get_current_metrics()
        timestamp_ns = int(time.time() * 1e9)
        
        # Export all metrics
        for metric_type in ["counters", "gauges"]:
            for name, value in current_metrics[metric_type].items():
                line = f"{name},type={metric_type} value={value} {timestamp_ns}"
                lines.append(line)
        
        return "\n".join(lines)
    
    def _export_csv(self) -> str:
        """Export metrics as CSV"""
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["timestamp", "metric_name", "metric_type", "value"])
        
        current_metrics = self.get_current_metrics()
        timestamp = current_metrics["timestamp"]
        
        # Write data
        for metric_type in ["counters", "gauges"]:
            for name, value in current_metrics[metric_type].items():
                writer.writerow([timestamp, name, metric_type, value])
        
        return output.getvalue()
    
    def save_to_file(self, filename: str, format: Optional[str] = None):
        """Save metrics to file"""
        format = format or self.export_format
        data = self.export_metrics(format)
        
        with open(filename, 'w') as f:
            f.write(data)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics"""
        with self._lock:
            return {
                "uptime_seconds": time.time() - self.start_time,
                "total_metrics_collected": self.total_metrics_collected,
                "unique_metrics": len(self.metrics),
                "retention_seconds": self.retention_seconds,
                "system_monitoring_enabled": self.system_monitoring_enabled,
                "export_format": self.export_format,
                "memory_usage": {
                    "counters": len(self.counters),
                    "gauges": len(self.gauges),
                    "histograms": len(self.histograms),
                    "total_data_points": sum(len(deque) for deque in self.metrics.values())
                }
            }
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.total_metrics_collected = 0
            self.start_time = time.time()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disable_system_monitoring()


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, name: str, 
                 tags: Optional[Dict[str, str]] = None):
        self.collector = collector
        self.name = name
        self.tags = tags or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            self.collector.record_timing(self.name, duration_ms, self.tags)


# Global metrics collector instance
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector


def configure_metrics_collector(export_format: str = "json",
                              retention_seconds: int = 3600,
                              collection_interval: int = 60,
                              enable_system_monitoring: bool = True):
    """Configure global metrics collector"""
    global _global_collector
    _global_collector = MetricsCollector(
        export_format=export_format,
        retention_seconds=retention_seconds,
        collection_interval=collection_interval
    )
    
    if enable_system_monitoring:
        _global_collector.enable_system_monitoring()


# Convenience functions for global collector
def record_counter(name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
    """Record counter using global collector"""
    get_metrics_collector().record_counter(name, value, tags)


def record_gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record gauge using global collector"""
    get_metrics_collector().record_gauge(name, value, tags)


def record_timing(name: str, duration_ms: float, tags: Optional[Dict[str, str]] = None):
    """Record timing using global collector"""
    get_metrics_collector().record_timing(name, duration_ms, tags)


def time_function(name: str, tags: Optional[Dict[str, str]] = None):
    """Time function using global collector"""
    return get_metrics_collector().time_function(name, tags) 