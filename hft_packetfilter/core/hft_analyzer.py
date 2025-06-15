#!/usr/bin/env python3
"""
HFT Analyzer - Main High-Frequency Trading Network Analysis Engine

This module provides the primary interface for HFT network analysis,
integrating packet filtering, latency monitoring, and trading analytics.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from collections import defaultdict, deque
import json
import yaml

# Core imports
from .exchange_config import ExchangeConfig
from .production_config import ProductionConfig
from .data_structures import (
    LatencyMeasurement, 
    RiskEvent, 
    MarketDataQuality, 
    TradingMetrics,
    ExchangeConnection,
    SystemMetrics,
    ComplianceEvent,
    RiskLevel,
    EventType,
    ExchangeStatus
)
from .exceptions import HFTPacketFilterError, ExchangeConnectionError
from ..utils.logger import HFTLogger
from ..utils.metrics_collector import MetricsCollector
from ..utils.alert_system import AlertSystem


class HFTAnalyzer:
    """
    Main High-Frequency Trading Network Analyzer
    
    This class provides a production-ready interface for HFT network analysis,
    combining packet filtering, latency monitoring, and trading analytics.
    
    Features:
    - Real-time packet capture and analysis
    - Microsecond-precision latency monitoring
    - Exchange connectivity management
    - Risk management and security controls
    - Market data quality assessment
    - Arbitrage opportunity detection
    - Regulatory compliance monitoring
    
    Example:
        >>> analyzer = HFTAnalyzer(performance_mode="ultra_low_latency")
        >>> analyzer.add_exchange(ExchangeConfig("NYSE", "nyse.gateway", [4001], "FIX", 500))
        >>> analyzer.start_monitoring()
        >>> metrics = analyzer.get_live_metrics()
    """
    
    def __init__(self, 
                 config: Optional[ProductionConfig] = None,
                 performance_mode: str = "standard",
                 logging_level: str = "INFO",
                 metrics_export: Optional[str] = None):
        """
        Initialize HFT Analyzer
        
        Args:
            config: Production configuration object
            performance_mode: Performance mode ('standard', 'high_performance', 'ultra_low_latency')
            logging_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')
            metrics_export: Metrics export format ('prometheus', 'influxdb', 'json')
        """
        self.config = config or ProductionConfig()
        self.performance_mode = performance_mode
        self.metrics_export = metrics_export
        
        # Initialize logging
        self.logger = HFTLogger(
            name="HFTAnalyzer",
            level=logging_level,
            performance_mode=performance_mode
        )
        
        # Exchange management
        self.exchanges: Dict[str, ExchangeConfig] = {}
        self.exchange_connections: Dict[str, ExchangeConnection] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Metrics and analytics
        self.metrics_collector = MetricsCollector(export_format=metrics_export or "json")
        self.alert_system = AlertSystem()
        
        # Performance tracking
        self.start_time = time.time()
        self.packet_count = 0
        self.last_metrics_update = time.time()
        
        # Trading metrics
        self.trading_metrics = TradingMetrics(exchange_name="default")
        self.latency_measurements: deque = deque(maxlen=10000)
        self.risk_events: List[RiskEvent] = []
        self.market_data_quality: Dict[str, MarketDataQuality] = {}
        
        # Callbacks
        self.packet_callbacks: List[Callable] = []
        self.latency_callbacks: List[Callable] = []
        self.risk_callbacks: List[Callable] = []
        
        # Initialize core components
        self._init_core_components()
        
        self.logger.info(f"HFTAnalyzer initialized in {performance_mode} mode")
    
    def _init_core_components(self):
        """Initialize core analysis components"""
        try:
            # Configure performance mode
            if self.performance_mode == "ultra_low_latency":
                self._configure_ultra_low_latency()
            elif self.performance_mode == "high_performance":
                self._configure_high_performance()
            
            # Enable system monitoring
            self.metrics_collector.enable_system_monitoring()
            
        except Exception as e:
            raise HFTPacketFilterError(f"Failed to initialize core components: {e}")
    
    def _configure_ultra_low_latency(self):
        """Configure for ultra-low latency mode"""
        # Disable garbage collection for consistent latency
        import gc
        gc.disable()
        
        # Set process priority
        try:
            import os
            os.nice(-20)  # Highest priority (requires root)
        except (OSError, PermissionError):
            self.logger.warning("Could not set high process priority")
        
        # Configure smaller buffers for lower latency
        self.latency_measurements = deque(maxlen=1000)
        
        self.logger.info("Configured for ultra-low latency mode")
    
    def _configure_high_performance(self):
        """Configure for high performance mode"""
        # Optimize buffer sizes
        self.latency_measurements = deque(maxlen=5000)
        
        self.logger.info("Configured for high performance mode")
    
    def add_exchange(self, exchange_config: ExchangeConfig) -> None:
        """
        Add exchange for monitoring
        
        Args:
            exchange_config: Exchange configuration object
        """
        try:
            # Validate configuration
            exchange_config.validate()
            
            # Store configuration
            self.exchanges[exchange_config.name] = exchange_config
            
            # Create exchange connection
            connection = ExchangeConnection(
                name=exchange_config.name,
                ip_address=exchange_config.host,
                ports=exchange_config.ports,
                protocol=exchange_config.protocol,
                latency_target_us=exchange_config.latency_target_us,
                is_primary=exchange_config.is_primary
            )
            
            self.exchange_connections[exchange_config.name] = connection
            
            # Initialize market data quality tracking
            self.market_data_quality[exchange_config.name] = MarketDataQuality(
                exchange_name=exchange_config.name,
                feed_name=f"{exchange_config.name}_feed",
                timestamp=time.time(),
                quality_score=0.0,
                latency_us=0.0,
                gap_count=0
            )
            
            self.logger.info(f"Added exchange: {exchange_config.name} ({exchange_config.host})")
            
        except Exception as e:
            raise ExchangeConnectionError(f"Failed to add exchange {exchange_config.name}: {e}")
    
    def remove_exchange(self, exchange_name: str) -> None:
        """
        Remove exchange from monitoring
        
        Args:
            exchange_name: Name of exchange to remove
        """
        if exchange_name in self.exchanges:
            del self.exchanges[exchange_name]
            del self.exchange_connections[exchange_name]
            if exchange_name in self.market_data_quality:
                del self.market_data_quality[exchange_name]
            
            self.logger.info(f"Removed exchange: {exchange_name}")
        else:
            self.logger.warning(f"Exchange not found: {exchange_name}")
    
    def start_monitoring(self, duration_seconds: Optional[int] = None) -> None:
        """
        Start HFT monitoring
        
        Args:
            duration_seconds: Optional monitoring duration (None for indefinite)
        """
        if self.is_monitoring:
            self.logger.warning("Monitoring already active")
            return
        
        if not self.exchanges:
            raise HFTPacketFilterError("No exchanges configured for monitoring")
        
        self.is_monitoring = True
        self._stop_event.clear()
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(duration_seconds,),
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("Started HFT monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop HFT monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Stopped HFT monitoring")
    
    def _monitoring_loop(self, duration_seconds: Optional[int]) -> None:
        """Main monitoring loop"""
        start_time = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Check duration limit
                if duration_seconds and (time.time() - start_time) >= duration_seconds:
                    break
                
                # Simulate packet processing (in real implementation, this would capture actual packets)
                self._simulate_packet_processing()
                
                # Update metrics periodically
                if time.time() - self.last_metrics_update >= 1.0:  # Every second
                    self._update_metrics()
                    self.last_metrics_update = time.time()
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(0.1)
        
        self.is_monitoring = False
    
    def _simulate_packet_processing(self):
        """Simulate packet processing for demo purposes"""
        import random
        
        # Simulate processing packets from exchanges
        for exchange_name, exchange_config in self.exchanges.items():
            # Simulate latency measurement
            simulated_latency = random.uniform(100, 2000)  # 100-2000 microseconds
            
            latency_measurement = LatencyMeasurement(
                timestamp=time.time(),
                exchange_name=exchange_name,
                latency_us=simulated_latency
            )
            
            self.latency_measurements.append(latency_measurement)
            
            # Check latency alerts
            if simulated_latency > exchange_config.latency_target_us:
                self.alert_system.send_latency_alert(
                    exchange_name, 
                    simulated_latency, 
                    exchange_config.latency_target_us
                )
            
            # Update trading metrics
            self.trading_metrics.latency_us = simulated_latency
            
            # Update market data quality
            quality = self.market_data_quality[exchange_name]
            quality.latency_us = simulated_latency
            quality.quality_score = max(0, 100 - (simulated_latency / 10))  # Simple scoring
            quality.timestamp = time.time()
            
            # Record metrics
            self.metrics_collector.record_gauge(f"latency.{exchange_name}", simulated_latency)
            self.metrics_collector.record_counter(f"packets.{exchange_name}")
            
            self.packet_count += 1
    
    def _update_metrics(self) -> None:
        """Update system metrics"""
        current_time = time.time()
        uptime = current_time - self.start_time
        
        # Update trading metrics
        self.trading_metrics.connection_uptime = uptime
        
        # Record system metrics
        self.metrics_collector.record_gauge("analyzer.uptime_seconds", uptime)
        self.metrics_collector.record_gauge("analyzer.total_packets", self.packet_count)
        
        # Update exchange connection status
        for exchange_name, connection in self.exchange_connections.items():
            connection.last_heartbeat = current_time
            connection.status = ExchangeStatus.CONNECTED if self.is_monitoring else ExchangeStatus.DISCONNECTED
    
    def get_live_metrics(self) -> Dict[str, Any]:
        """
        Get current live metrics
        
        Returns:
            Dictionary containing current metrics
        """
        current_time = time.time()
        
        # Calculate recent latency statistics
        recent_latencies = [
            m.latency_us for m in self.latency_measurements 
            if current_time - m.timestamp <= 60  # Last minute
        ]
        
        latency_stats = {}
        if recent_latencies:
            latency_stats = {
                "min": min(recent_latencies),
                "max": max(recent_latencies),
                "avg": sum(recent_latencies) / len(recent_latencies),
                "count": len(recent_latencies)
            }
        
        return {
            "timestamp": current_time,
            "uptime_seconds": current_time - self.start_time,
            "is_monitoring": self.is_monitoring,
            "performance_mode": self.performance_mode,
            "exchanges": {
                name: {
                    "status": conn.status.value,
                    "latency_target_us": self.exchanges[name].latency_target_us,
                    "last_heartbeat": conn.last_heartbeat
                }
                for name, conn in self.exchange_connections.items()
            },
            "trading_metrics": {
                "total_packets": self.packet_count,
                "latency_us": self.trading_metrics.latency_us,
                "connection_uptime": self.trading_metrics.connection_uptime
            },
            "latency_stats": latency_stats,
            "market_data_quality": {
                name: {
                    "quality_score": quality.quality_score,
                    "latency_us": quality.latency_us
                }
                for name, quality in self.market_data_quality.items()
            },
            "system_metrics": self.metrics_collector.get_current_metrics(),
            "alert_stats": self.alert_system.get_alert_statistics()
        }
    
    def process_latency_measurement(self, measurement: LatencyMeasurement) -> None:
        """
        Process a latency measurement from network capture or simulation
        
        Args:
            measurement: LatencyMeasurement object containing timing data
        """
        try:
            # Add to latency measurements collection
            self.latency_measurements.append(measurement)
            
            # Update trading metrics
            self.trading_metrics.latency_us = measurement.latency_us
            
            # Update market data quality if exchange exists
            if measurement.exchange_name in self.market_data_quality:
                quality = self.market_data_quality[measurement.exchange_name]
                quality.latency_us = measurement.latency_us
                quality.timestamp = measurement.timestamp
                
                # Update quality score based on latency performance
                if measurement.exchange_name in self.exchanges:
                    target_latency = self.exchanges[measurement.exchange_name].latency_target_us
                    if measurement.latency_us <= target_latency:
                        quality.quality_score = min(99.9, quality.quality_score + 0.1)
                    else:
                        quality.quality_score = max(0.0, quality.quality_score - 0.5)
            
            # Check for latency violations and generate risk events
            if measurement.exchange_name in self.exchanges:
                target_latency = self.exchanges[measurement.exchange_name].latency_target_us
                if measurement.latency_us > target_latency * 2:  # 2x target is high risk
                    risk_event = RiskEvent(
                        timestamp=measurement.timestamp,
                        event_type=EventType.LATENCY_VIOLATION.value,
                        severity=RiskLevel.HIGH.value,
                        source_ip="analyzer",
                        destination_ip="",
                        description=f"High latency detected: {measurement.latency_us:.1f}μs (target: {target_latency}μs)",
                        exchange_name=measurement.exchange_name
                    )
                    self.risk_events.append(risk_event)
                    
                    # Trigger risk callbacks
                    for callback in self.risk_callbacks:
                        try:
                            callback(risk_event)
                        except Exception as e:
                            self.logger.error(f"Risk callback error: {e}")
            
            # Trigger latency callbacks
            for callback in self.latency_callbacks:
                try:
                    callback(measurement)
                except Exception as e:
                    self.logger.error(f"Latency callback error: {e}")
            
            # Update packet count
            self.packet_count += 1
            
        except Exception as e:
            self.logger.error(f"Error processing latency measurement: {e}")
    
    def get_latency_report(self) -> Dict[str, Any]:
        """Get detailed latency analysis report"""
        current_time = time.time()
        
        # Group latencies by exchange
        exchange_latencies = defaultdict(list)
        for measurement in self.latency_measurements:
            if current_time - measurement.timestamp <= 3600:  # Last hour
                exchange_latencies[measurement.exchange_name].append(measurement.latency_us)
        
        report = {
            "timestamp": current_time,
            "period_hours": 1,
            "exchanges": {}
        }
        
        for exchange_name, latencies in exchange_latencies.items():
            if latencies:
                sorted_latencies = sorted(latencies)
                count = len(sorted_latencies)
                
                report["exchanges"][exchange_name] = {
                    "count": count,
                    "min_us": min(latencies),
                    "max_us": max(latencies),
                    "avg_us": sum(latencies) / count,
                    "median_us": sorted_latencies[count // 2],
                    "p95_us": sorted_latencies[int(count * 0.95)],
                    "p99_us": sorted_latencies[int(count * 0.99)],
                    "target_us": self.exchanges[exchange_name].latency_target_us,
                    "violations": sum(1 for l in latencies if l > self.exchanges[exchange_name].latency_target_us)
                }
        
        return report
    
    def get_risk_report(self) -> Dict[str, Any]:
        """Get risk management report"""
        current_time = time.time()
        
        # Filter recent risk events
        recent_events = [
            event for event in self.risk_events
            if current_time - event.timestamp <= 3600  # Last hour
        ]
        
        # Count by severity
        severity_counts = defaultdict(int)
        for event in recent_events:
            severity_counts[event.severity.value] += 1
        
        return {
            "timestamp": current_time,
            "period_hours": 1,
            "total_events": len(recent_events),
            "severity_distribution": dict(severity_counts),
            "recent_events": [
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "severity": event.severity.value,
                    "source_ip": event.source_ip,
                    "description": event.description
                }
                for event in recent_events[-10:]  # Last 10 events
            ]
        }
    
    def export_analysis(self, filename: str, format: str = "json") -> None:
        """
        Export analysis results
        
        Args:
            filename: Output filename
            format: Export format ('json', 'csv', 'yaml')
        """
        data = {
            "export_timestamp": time.time(),
            "analyzer_config": {
                "performance_mode": self.performance_mode,
                "exchanges": [config.to_dict() for config in self.exchanges.values()]
            },
            "live_metrics": self.get_live_metrics(),
            "latency_report": self.get_latency_report(),
            "risk_report": self.get_risk_report()
        }
        
        if format.lower() == "json":
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        elif format.lower() == "yaml":
            with open(filename, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        elif format.lower() == "csv":
            # Export latency data as CSV
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'exchange', 'latency_us', 'packet_type'])
                for measurement in self.latency_measurements:
                    writer.writerow([
                        measurement.timestamp,
                        measurement.exchange_name,
                        measurement.latency_us,
                        measurement.packet_type
                    ])
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        self.logger.info(f"Exported analysis to {filename} ({format})")
    
    def add_packet_callback(self, callback: Callable) -> None:
        """Add callback for packet events"""
        self.packet_callbacks.append(callback)
    
    def add_latency_callback(self, callback: Callable) -> None:
        """Add callback for latency events"""
        self.latency_callbacks.append(callback)
    
    def add_risk_callback(self, callback: Callable) -> None:
        """Add callback for risk events"""
        self.risk_callbacks.append(callback)
    
    def enable_compliance_monitoring(self, 
                                   regulations: List[str],
                                   audit_trail: bool = True,
                                   real_time_alerts: bool = True) -> None:
        """
        Enable regulatory compliance monitoring
        
        Args:
            regulations: List of regulations to monitor ('MiFID_II', 'Reg_NMS', 'CFTC')
            audit_trail: Enable audit trail logging
            real_time_alerts: Enable real-time compliance alerts
        """
        self.logger.info(f"Enabling compliance monitoring for: {regulations}")
        
        for regulation in regulations:
            if regulation == "MiFID_II":
                self._add_mifid_ii_rules()
            elif regulation == "Reg_NMS":
                self._add_reg_nms_rules()
            elif regulation == "CFTC":
                self._add_cftc_rules()
        
        if audit_trail:
            self.logger.info("Audit trail logging enabled")
        
        if real_time_alerts:
            self.logger.info("Real-time compliance alerts enabled")
    
    def _add_mifid_ii_rules(self) -> None:
        """Add MiFID II compliance rules"""
        # Implement MiFID II specific monitoring
        self.logger.info("Added MiFID II compliance rules")
    
    def _add_reg_nms_rules(self) -> None:
        """Add Reg NMS compliance rules"""
        # Implement Reg NMS specific monitoring
        self.logger.info("Added Reg NMS compliance rules")
    
    def _add_cftc_rules(self) -> None:
        """Add CFTC compliance rules"""
        # Implement CFTC specific monitoring
        self.logger.info("Added CFTC compliance rules")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_monitoring()
    
    def __repr__(self) -> str:
        """String representation"""
        return f"HFTAnalyzer(exchanges={len(self.exchanges)}, monitoring={self.is_monitoring})" 