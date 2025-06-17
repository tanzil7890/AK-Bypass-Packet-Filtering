#!/usr/bin/env python3
"""
Market Data Quality Analyzer

Real-time market data feed quality assessment and monitoring for HFT environments.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque, defaultdict
import statistics
import logging

from ..core.data_structures import MarketDataQuality
from ..core.exceptions import MarketDataQualityError
from ..utils.logger import get_logger
from ..utils.metrics_collector import get_metrics_collector


@dataclass
class QualityMetrics:
    """Market data quality metrics"""
    timestamp: float
    feed_name: str
    exchange_name: str
    
    # Message statistics
    message_count: int = 0
    message_rate: float = 0.0
    bytes_received: int = 0
    throughput_mbps: float = 0.0
    
    # Quality indicators
    gap_count: int = 0
    duplicate_count: int = 0
    out_of_order_count: int = 0
    corruption_count: int = 0
    
    # Latency metrics
    latency_us: float = 0.0
    jitter_us: float = 0.0
    
    # Sequence tracking
    expected_sequence: int = 0
    last_sequence: int = 0
    sequence_errors: int = 0
    
    # Quality score (0-100)
    quality_score: float = 100.0
    
    def calculate_quality_score(self) -> float:
        """Calculate overall quality score"""
        score = 100.0
        
        # Penalize gaps
        if self.message_count > 0:
            gap_penalty = (self.gap_count / self.message_count) * 50
            score -= gap_penalty
        
        # Penalize duplicates
        if self.message_count > 0:
            duplicate_penalty = (self.duplicate_count / self.message_count) * 30
            score -= duplicate_penalty
        
        # Penalize out of order
        if self.message_count > 0:
            order_penalty = (self.out_of_order_count / self.message_count) * 20
            score -= order_penalty
        
        # Penalize corruption
        if self.message_count > 0:
            corruption_penalty = (self.corruption_count / self.message_count) * 40
            score -= corruption_penalty
        
        # Penalize high latency
        if self.latency_us > 1000:  # > 1ms
            latency_penalty = min(30, (self.latency_us - 1000) / 100)
            score -= latency_penalty
        
        self.quality_score = max(0.0, score)
        return self.quality_score


class FeedValidator:
    """Market data feed validator"""
    
    def __init__(self, feed_name: str, exchange_name: str):
        self.feed_name = feed_name
        self.exchange_name = exchange_name
        self.logger = get_logger()
        
        # Validation state
        self.last_sequence = 0
        self.expected_sequence = 1
        self.message_timestamps = deque(maxlen=1000)
        self.seen_messages = set()
        
        # Statistics
        self.total_messages = 0
        self.validation_errors = 0
        
    def validate_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a market data message
        
        Args:
            message_data: Message data dictionary
            
        Returns:
            Validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "sequence_number": None,
            "timestamp": time.time()
        }
        
        try:
            # Extract sequence number
            sequence = message_data.get("sequence_number")
            if sequence is not None:
                validation_result["sequence_number"] = sequence
                
                # Check for gaps
                if sequence != self.expected_sequence:
                    if sequence > self.expected_sequence:
                        gap_size = sequence - self.expected_sequence
                        validation_result["errors"].append(f"Gap detected: missing {gap_size} messages")
                        validation_result["is_valid"] = False
                    elif sequence < self.expected_sequence:
                        validation_result["warnings"].append("Out of order message")
                
                # Check for duplicates
                if sequence in self.seen_messages:
                    validation_result["errors"].append("Duplicate message")
                    validation_result["is_valid"] = False
                else:
                    self.seen_messages.add(sequence)
                    # Keep only recent sequences to prevent memory growth
                    if len(self.seen_messages) > 10000:
                        self.seen_messages.clear()
                
                self.last_sequence = sequence
                self.expected_sequence = max(self.expected_sequence, sequence + 1)
            
            # Validate timestamp
            msg_timestamp = message_data.get("timestamp")
            if msg_timestamp:
                current_time = time.time()
                age_seconds = current_time - msg_timestamp
                
                if age_seconds > 1.0:  # Message older than 1 second
                    validation_result["warnings"].append(f"Stale message: {age_seconds:.3f}s old")
                elif age_seconds < 0:  # Future timestamp
                    validation_result["errors"].append("Future timestamp detected")
                    validation_result["is_valid"] = False
            
            # Validate required fields
            required_fields = ["symbol", "price", "quantity"]
            for field in required_fields:
                if field not in message_data:
                    validation_result["errors"].append(f"Missing required field: {field}")
                    validation_result["is_valid"] = False
            
            # Validate data types and ranges
            if "price" in message_data:
                try:
                    price = float(message_data["price"])
                    if price <= 0:
                        validation_result["errors"].append("Invalid price: must be positive")
                        validation_result["is_valid"] = False
                except (ValueError, TypeError):
                    validation_result["errors"].append("Invalid price format")
                    validation_result["is_valid"] = False
            
            if "quantity" in message_data:
                try:
                    quantity = int(message_data["quantity"])
                    if quantity < 0:
                        validation_result["errors"].append("Invalid quantity: must be non-negative")
                        validation_result["is_valid"] = False
                except (ValueError, TypeError):
                    validation_result["errors"].append("Invalid quantity format")
                    validation_result["is_valid"] = False
            
            self.total_messages += 1
            if not validation_result["is_valid"]:
                self.validation_errors += 1
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Validation exception: {str(e)}")
            self.logger.error(f"Message validation error: {e}")
        
        return validation_result
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics"""
        error_rate = self.validation_errors / self.total_messages if self.total_messages > 0 else 0
        
        return {
            "feed_name": self.feed_name,
            "exchange_name": self.exchange_name,
            "total_messages": self.total_messages,
            "validation_errors": self.validation_errors,
            "error_rate": error_rate,
            "last_sequence": self.last_sequence,
            "expected_sequence": self.expected_sequence
        }


class MarketDataAnalyzer:
    """
    Market data quality analyzer
    
    Monitors and analyzes market data feed quality in real-time,
    providing quality metrics and alerts for HFT environments.
    """
    
    def __init__(self, 
                 quality_threshold: float = 95.0,
                 latency_threshold_us: float = 1000.0,
                 monitoring_interval: float = 1.0):
        """
        Initialize market data analyzer
        
        Args:
            quality_threshold: Minimum acceptable quality score
            latency_threshold_us: Maximum acceptable latency in microseconds
            monitoring_interval: Monitoring update interval in seconds
        """
        self.quality_threshold = quality_threshold
        self.latency_threshold_us = latency_threshold_us
        self.monitoring_interval = monitoring_interval
        
        # Components
        self.logger = get_logger()
        self.metrics_collector = get_metrics_collector()
        
        # Feed tracking
        self.feeds: Dict[str, FeedValidator] = {}
        self.quality_metrics: Dict[str, QualityMetrics] = {}
        self.quality_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Monitoring
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self.quality_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Statistics
        self.start_time = time.time()
        self.total_messages_processed = 0
        
    def add_feed(self, feed_name: str, exchange_name: str) -> None:
        """Add market data feed for monitoring"""
        feed_key = f"{exchange_name}:{feed_name}"
        
        self.feeds[feed_key] = FeedValidator(feed_name, exchange_name)
        self.quality_metrics[feed_key] = QualityMetrics(
            timestamp=time.time(),
            feed_name=feed_name,
            exchange_name=exchange_name
        )
        
        self.logger.info(f"Added market data feed: {feed_key}")
    
    def remove_feed(self, feed_name: str, exchange_name: str) -> None:
        """Remove market data feed from monitoring"""
        feed_key = f"{exchange_name}:{feed_name}"
        
        if feed_key in self.feeds:
            del self.feeds[feed_key]
            del self.quality_metrics[feed_key]
            if feed_key in self.quality_history:
                del self.quality_history[feed_key]
            
            self.logger.info(f"Removed market data feed: {feed_key}")
    
    def process_message(self, feed_name: str, exchange_name: str, 
                       message_data: Dict[str, Any], 
                       receive_timestamp: Optional[float] = None) -> None:
        """
        Process market data message
        
        Args:
            feed_name: Name of the market data feed
            exchange_name: Name of the exchange
            message_data: Message data dictionary
            receive_timestamp: Message receive timestamp
        """
        feed_key = f"{exchange_name}:{feed_name}"
        receive_timestamp = receive_timestamp or time.time()
        
        if feed_key not in self.feeds:
            self.add_feed(feed_name, exchange_name)
        
        try:
            # Validate message
            validator = self.feeds[feed_key]
            validation_result = validator.validate_message(message_data)
            
            # Update quality metrics
            metrics = self.quality_metrics[feed_key]
            metrics.timestamp = receive_timestamp
            metrics.message_count += 1
            
            # Calculate latency
            msg_timestamp = message_data.get("timestamp")
            if msg_timestamp:
                latency_us = (receive_timestamp - msg_timestamp) * 1_000_000
                metrics.latency_us = latency_us
                
                # Update jitter calculation
                if hasattr(metrics, '_last_latency'):
                    jitter = abs(latency_us - metrics._last_latency)
                    metrics.jitter_us = jitter
                metrics._last_latency = latency_us
            
            # Update error counts
            if not validation_result["is_valid"]:
                for error in validation_result["errors"]:
                    if "gap" in error.lower():
                        metrics.gap_count += 1
                    elif "duplicate" in error.lower():
                        metrics.duplicate_count += 1
                    elif "corruption" in error.lower():
                        metrics.corruption_count += 1
            
            if validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    if "out of order" in warning.lower():
                        metrics.out_of_order_count += 1
            
            # Calculate quality score
            metrics.calculate_quality_score()
            
            # Record metrics
            self.metrics_collector.record_gauge(
                f"market_data.quality.{feed_key}", 
                metrics.quality_score
            )
            self.metrics_collector.record_gauge(
                f"market_data.latency.{feed_key}", 
                metrics.latency_us
            )
            self.metrics_collector.record_counter(
                f"market_data.messages.{feed_key}"
            )
            
            # Check quality thresholds
            if metrics.quality_score < self.quality_threshold:
                self._trigger_quality_alert(feed_key, metrics)
            
            # Check latency thresholds
            if metrics.latency_us > self.latency_threshold_us:
                self._trigger_latency_alert(feed_key, metrics)
            
            # Store quality history
            self.quality_history[feed_key].append({
                "timestamp": receive_timestamp,
                "quality_score": metrics.quality_score,
                "latency_us": metrics.latency_us,
                "message_count": metrics.message_count
            })
            
            # Call quality callbacks
            for callback in self.quality_callbacks:
                try:
                    callback(feed_key, metrics, validation_result)
                except Exception as e:
                    self.logger.error(f"Quality callback error: {e}")
            
            self.total_messages_processed += 1
            
        except Exception as e:
            self.logger.error(f"Error processing message for {feed_key}: {e}")
            raise MarketDataQualityError(f"Message processing failed: {e}", feed_key)
    
    def _trigger_quality_alert(self, feed_key: str, metrics: QualityMetrics) -> None:
        """Trigger quality alert"""
        alert_data = {
            "type": "market_data_quality",
            "severity": "HIGH" if metrics.quality_score < 80 else "MEDIUM",
            "feed_key": feed_key,
            "quality_score": metrics.quality_score,
            "threshold": self.quality_threshold,
            "metrics": metrics
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def _trigger_latency_alert(self, feed_key: str, metrics: QualityMetrics) -> None:
        """Trigger latency alert"""
        alert_data = {
            "type": "market_data_latency",
            "severity": "HIGH" if metrics.latency_us > self.latency_threshold_us * 2 else "MEDIUM",
            "feed_key": feed_key,
            "latency_us": metrics.latency_us,
            "threshold_us": self.latency_threshold_us,
            "metrics": metrics
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def start_monitoring(self) -> None:
        """Start quality monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._stop_event.clear()
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("Started market data quality monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop quality monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Stopped market data quality monitoring")
    
    def _monitoring_loop(self) -> None:
        """Quality monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self._update_quality_metrics()
                self._stop_event.wait(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in quality monitoring loop: {e}")
                time.sleep(1)
    
    def _update_quality_metrics(self) -> None:
        """Update quality metrics"""
        current_time = time.time()
        
        for feed_key, metrics in self.quality_metrics.items():
            # Calculate message rate
            time_window = 60.0  # 1 minute window
            recent_history = [
                h for h in self.quality_history[feed_key]
                if current_time - h["timestamp"] <= time_window
            ]
            
            if len(recent_history) >= 2:
                time_span = recent_history[-1]["timestamp"] - recent_history[0]["timestamp"]
                message_span = recent_history[-1]["message_count"] - recent_history[0]["message_count"]
                
                if time_span > 0:
                    metrics.message_rate = message_span / time_span
            
            # Record updated metrics
            self.metrics_collector.record_gauge(
                f"market_data.message_rate.{feed_key}",
                metrics.message_rate
            )
    
    def get_quality_report(self, feed_name: Optional[str] = None, 
                          exchange_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get quality report
        
        Args:
            feed_name: Optional feed name filter
            exchange_name: Optional exchange name filter
            
        Returns:
            Quality report dictionary
        """
        current_time = time.time()
        report = {
            "timestamp": current_time,
            "uptime_seconds": current_time - self.start_time,
            "total_messages_processed": self.total_messages_processed,
            "feeds": {}
        }
        
        for feed_key, metrics in self.quality_metrics.items():
            exchange, feed = feed_key.split(":", 1)
            
            # Apply filters
            if feed_name and feed != feed_name:
                continue
            if exchange_name and exchange != exchange_name:
                continue
            
            # Get validation statistics
            validator = self.feeds[feed_key]
            validation_stats = validator.get_validation_statistics()
            
            # Calculate recent statistics
            recent_history = [
                h for h in self.quality_history[feed_key]
                if current_time - h["timestamp"] <= 3600  # Last hour
            ]
            
            quality_scores = [h["quality_score"] for h in recent_history]
            latencies = [h["latency_us"] for h in recent_history]
            
            feed_report = {
                "exchange_name": exchange,
                "feed_name": feed,
                "current_quality_score": metrics.quality_score,
                "current_latency_us": metrics.latency_us,
                "message_count": metrics.message_count,
                "message_rate": metrics.message_rate,
                "gap_count": metrics.gap_count,
                "duplicate_count": metrics.duplicate_count,
                "out_of_order_count": metrics.out_of_order_count,
                "corruption_count": metrics.corruption_count,
                "validation_stats": validation_stats
            }
            
            # Add statistics if we have history
            if quality_scores:
                feed_report["quality_stats"] = {
                    "min": min(quality_scores),
                    "max": max(quality_scores),
                    "avg": statistics.mean(quality_scores),
                    "median": statistics.median(quality_scores)
                }
            
            if latencies:
                feed_report["latency_stats"] = {
                    "min_us": min(latencies),
                    "max_us": max(latencies),
                    "avg_us": statistics.mean(latencies),
                    "median_us": statistics.median(latencies)
                }
            
            report["feeds"][feed_key] = feed_report
        
        return report
    
    def add_quality_callback(self, callback: Callable) -> None:
        """Add quality callback"""
        self.quality_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get analyzer statistics"""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_messages_processed": self.total_messages_processed,
            "feeds_monitored": len(self.feeds),
            "is_monitoring": self.is_monitoring,
            "quality_threshold": self.quality_threshold,
            "latency_threshold_us": self.latency_threshold_us
        } 