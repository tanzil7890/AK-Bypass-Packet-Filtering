#!/usr/bin/env python3
"""
HFT Network Analyzer Module

This module provides specialized functionality for High-Frequency Trading
network analysis and monitoring.

Author: Tanzil github://@tanzil7890
License: Educational/Research Use Only
"""

import time
import json
import statistics
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.packet_filter import PacketFilter, FilterRule, FilterAction
from core.packet_parser import PacketParser, ParsedPacket


@dataclass
class TradingMetrics:
    """Trading-specific network metrics"""
    latency_us: float  # Microseconds
    jitter_us: float   # Latency variation
    packet_loss: float # Percentage
    throughput_mbps: float
    order_rate: float  # Orders per second
    market_data_rate: float  # Messages per second


@dataclass
class ExchangeConnection:
    """Exchange connection information"""
    name: str
    ip_address: str
    ports: List[int]
    protocol: str
    latency_target_us: float
    is_primary: bool = True


class HFTNetworkAnalyzer:
    """
    High-Frequency Trading Network Analyzer
    
    Specialized packet analysis for HFT environments including:
    - Latency measurement and optimization
    - Market data feed analysis
    - Order flow monitoring
    - Exchange connectivity tracking
    - Risk management controls
    """
    
    def __init__(self):
        """Initialize HFT analyzer"""
        self.packet_filter = PacketFilter()
        self.packet_parser = PacketParser()
        
        # HFT-specific tracking
        self.exchange_connections = {}
        self.latency_measurements = defaultdict(deque)
        self.order_flow = defaultdict(list)
        self.market_data_stats = defaultdict(dict)
        self.risk_metrics = {}
        
        # Performance tracking
        self.packet_timestamps = deque(maxlen=10000)
        self.trading_sessions = []
        
        # Common HFT ports and protocols
        self.hft_ports = {
            4001: 'FIX_Trading',
            4002: 'FIX_MarketData', 
            9001: 'NYSE_MarketData',
            9002: 'NASDAQ_MarketData',
            8080: 'REST_API',
            8443: 'WebSocket_Trading',
            1234: 'Proprietary_Protocol'
        }
        
        # Setup callbacks
        self.packet_filter.add_packet_callback(self._analyze_hft_packet)
    
    def add_exchange_connection(self, exchange: ExchangeConnection) -> None:
        """Add exchange connection for monitoring"""
        self.exchange_connections[exchange.name] = exchange
        
        # Add monitoring rules for this exchange
        for port in exchange.ports:
            rule = FilterRule(
                name=f"{exchange.name}_{port}",
                dst_ip=exchange.ip_address,
                dst_port=port,
                action=FilterAction.LOG,
                description=f"Monitor {exchange.name} on port {port}"
            )
            self.packet_filter.add_rule(rule)
    
    def _analyze_hft_packet(self, packet, action, rule) -> None:
        """Analyze packet for HFT-specific metrics"""
        parsed = self.packet_parser.parse_packet(packet)
        
        # Record timestamp for latency analysis
        self.packet_timestamps.append(parsed.timestamp)
        
        # Analyze by packet type
        if self._is_trading_packet(parsed):
            self._analyze_trading_packet(parsed)
        elif self._is_market_data_packet(parsed):
            self._analyze_market_data_packet(parsed)
        elif self._is_risk_relevant(parsed):
            self._analyze_risk_packet(parsed)
    
    def _is_trading_packet(self, parsed: ParsedPacket) -> bool:
        """Check if packet is trading-related"""
        trading_ports = [4001, 4002, 8080, 8443]
        return (parsed.dst_port in trading_ports or 
                parsed.src_port in trading_ports)
    
    def _is_market_data_packet(self, parsed: ParsedPacket) -> bool:
        """Check if packet contains market data"""
        market_data_ports = [9001, 9002, 9003, 9004]
        return (parsed.dst_port in market_data_ports or
                parsed.src_port in market_data_ports)
    
    def _is_risk_relevant(self, parsed: ParsedPacket) -> bool:
        """Check if packet is relevant for risk monitoring"""
        return (parsed.suspicious_flags or 
                parsed.size > 1400 or  # Large packets
                parsed.dst_port in [22, 23, 3389])  # Admin ports
    
    def _analyze_trading_packet(self, parsed: ParsedPacket) -> None:
        """Analyze trading-specific packets"""
        # Track order flow
        if parsed.dst_port == 4001:  # FIX trading
            self.order_flow[parsed.ip_dst].append({
                'timestamp': parsed.timestamp,
                'size': parsed.size,
                'source': parsed.ip_src
            })
        
        # Measure trading latency
        if parsed.ip_dst in [conn.ip_address for conn in self.exchange_connections.values()]:
            self._measure_latency(parsed)
    
    def _analyze_market_data_packet(self, parsed: ParsedPacket) -> None:
        """Analyze market data packets"""
        exchange_ip = parsed.ip_src
        
        if exchange_ip not in self.market_data_stats:
            self.market_data_stats[exchange_ip] = {
                'packet_count': 0,
                'total_bytes': 0,
                'last_timestamp': 0,
                'gaps_detected': 0
            }
        
        stats = self.market_data_stats[exchange_ip]
        stats['packet_count'] += 1
        stats['total_bytes'] += parsed.size
        
        # Detect potential gaps in market data
        if stats['last_timestamp'] > 0:
            gap = parsed.timestamp - stats['last_timestamp']
            if gap > 0.1:  # 100ms gap threshold
                stats['gaps_detected'] += 1
        
        stats['last_timestamp'] = parsed.timestamp
    
    def _analyze_risk_packet(self, parsed: ParsedPacket) -> None:
        """Analyze packets for risk management"""
        if parsed.suspicious_flags:
            risk_event = {
                'timestamp': parsed.timestamp,
                'source': parsed.ip_src,
                'destination': parsed.ip_dst,
                'flags': parsed.suspicious_flags,
                'severity': self._calculate_risk_severity(parsed)
            }
            
            if 'risk_events' not in self.risk_metrics:
                self.risk_metrics['risk_events'] = []
            
            self.risk_metrics['risk_events'].append(risk_event)
    
    def _calculate_risk_severity(self, parsed: ParsedPacket) -> str:
        """Calculate risk severity based on packet characteristics"""
        if 'NULL_SCAN' in parsed.suspicious_flags:
            return 'HIGH'
        elif 'SYN_ONLY' in parsed.suspicious_flags:
            return 'MEDIUM'
        elif parsed.size > 1400:
            return 'LOW'
        else:
            return 'INFO'
    
    def _measure_latency(self, parsed: ParsedPacket) -> None:
        """Measure network latency for trading packets"""
        # Simplified latency measurement
        # In real implementation, would correlate request/response pairs
        current_time = time.time()
        latency_us = (current_time - parsed.timestamp) * 1000000
        
        exchange_name = self._get_exchange_name(parsed.ip_dst)
        if exchange_name:
            self.latency_measurements[exchange_name].append(latency_us)
            
            # Keep only recent measurements
            if len(self.latency_measurements[exchange_name]) > 1000:
                self.latency_measurements[exchange_name].popleft()
    
    def _get_exchange_name(self, ip_address: str) -> Optional[str]:
        """Get exchange name from IP address"""
        for name, conn in self.exchange_connections.items():
            if conn.ip_address == ip_address:
                return name
        return None
    
    def get_trading_metrics(self) -> Dict[str, TradingMetrics]:
        """Get comprehensive trading metrics"""
        metrics = {}
        
        for exchange_name, latencies in self.latency_measurements.items():
            if latencies:
                latency_list = list(latencies)
                metrics[exchange_name] = TradingMetrics(
                    latency_us=statistics.mean(latency_list),
                    jitter_us=statistics.stdev(latency_list) if len(latency_list) > 1 else 0,
                    packet_loss=0.0,  # Would calculate from missing sequences
                    throughput_mbps=self._calculate_throughput(exchange_name),
                    order_rate=self._calculate_order_rate(exchange_name),
                    market_data_rate=self._calculate_market_data_rate(exchange_name)
                )
        
        return metrics
    
    def _calculate_throughput(self, exchange_name: str) -> float:
        """Calculate throughput for exchange connection"""
        # Simplified calculation
        if exchange_name in self.market_data_stats:
            stats = self.market_data_stats[exchange_name]
            return (stats['total_bytes'] * 8) / (1024 * 1024)  # Mbps
        return 0.0
    
    def _calculate_order_rate(self, exchange_name: str) -> float:
        """Calculate order submission rate"""
        exchange_ip = None
        for name, conn in self.exchange_connections.items():
            if name == exchange_name:
                exchange_ip = conn.ip_address
                break
        
        if exchange_ip and exchange_ip in self.order_flow:
            orders = self.order_flow[exchange_ip]
            if len(orders) > 1:
                time_span = orders[-1]['timestamp'] - orders[0]['timestamp']
                return len(orders) / time_span if time_span > 0 else 0
        
        return 0.0
    
    def _calculate_market_data_rate(self, exchange_name: str) -> float:
        """Calculate market data message rate"""
        exchange_ip = None
        for name, conn in self.exchange_connections.items():
            if name == exchange_name:
                exchange_ip = conn.ip_address
                break
        
        if exchange_ip and exchange_ip in self.market_data_stats:
            stats = self.market_data_stats[exchange_ip]
            # Simplified rate calculation
            return stats['packet_count'] / 60.0  # Messages per second (assuming 1 minute window)
        
        return 0.0
    
    def detect_latency_anomalies(self, threshold_us: float = 1000) -> Dict[str, List]:
        """Detect latency anomalies above threshold"""
        anomalies = {}
        
        for exchange_name, latencies in self.latency_measurements.items():
            exchange_anomalies = []
            for latency in latencies:
                if latency > threshold_us:
                    exchange_anomalies.append({
                        'latency_us': latency,
                        'threshold_us': threshold_us,
                        'severity': 'HIGH' if latency > threshold_us * 2 else 'MEDIUM'
                    })
            
            if exchange_anomalies:
                anomalies[exchange_name] = exchange_anomalies
        
        return anomalies
    
    def generate_hft_report(self) -> Dict:
        """Generate comprehensive HFT network report"""
        metrics = self.get_trading_metrics()
        anomalies = self.detect_latency_anomalies()
        
        report = {
            'timestamp': time.time(),
            'summary': {
                'exchanges_monitored': len(self.exchange_connections),
                'total_packets_analyzed': len(self.packet_timestamps),
                'risk_events': len(self.risk_metrics.get('risk_events', [])),
                'latency_anomalies': sum(len(a) for a in anomalies.values())
            },
            'exchange_metrics': {
                name: {
                    'latency_us': m.latency_us,
                    'jitter_us': m.jitter_us,
                    'throughput_mbps': m.throughput_mbps,
                    'order_rate': m.order_rate,
                    'market_data_rate': m.market_data_rate
                } for name, m in metrics.items()
            },
            'latency_anomalies': anomalies,
            'risk_summary': self.risk_metrics,
            'market_data_quality': {
                ip: {
                    'packets': stats['packet_count'],
                    'gaps': stats['gaps_detected'],
                    'quality_score': max(0, 100 - (stats['gaps_detected'] / max(1, stats['packet_count']) * 100))
                } for ip, stats in self.market_data_stats.items()
            }
        }
        
        return report
    
    def start_monitoring(self, duration_seconds: int = 60) -> None:
        """Start HFT network monitoring"""
        print(f"Starting HFT network monitoring for {duration_seconds} seconds...")
        print(f"Monitoring {len(self.exchange_connections)} exchange connections")
        
        try:
            self.packet_filter.start_capture(timeout=duration_seconds)
        except PermissionError:
            print("ERROR: Packet capture requires sudo privileges")
            print("Run with: sudo python3 hft_analyzer.py")
        except Exception as e:
            print(f"Error during monitoring: {e}")
    
    def export_hft_data(self, filename: str) -> None:
        """Export HFT analysis data"""
        report = self.generate_hft_report()
        
        with open(f"{filename}_hft_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"HFT analysis exported to {filename}_hft_report.json")


# Example usage for HFT monitoring
if __name__ == "__main__":
    # Initialize HFT analyzer
    hft_analyzer = HFTNetworkAnalyzer()
    
    # Add exchange connections
    nyse_connection = ExchangeConnection(
        name="NYSE",
        ip_address="198.51.100.10",  # Example IP
        ports=[4001, 9001],
        protocol="FIX/TCP",
        latency_target_us=500,
        is_primary=True
    )
    
    nasdaq_connection = ExchangeConnection(
        name="NASDAQ",
        ip_address="203.0.113.20",  # Example IP
        ports=[4002, 9002],
        protocol="FIX/TCP", 
        latency_target_us=600,
        is_primary=True
    )
    
    hft_analyzer.add_exchange_connection(nyse_connection)
    hft_analyzer.add_exchange_connection(nasdaq_connection)
    
    print("HFT Network Analyzer initialized")
    print("Exchange connections configured:")
    for name, conn in hft_analyzer.exchange_connections.items():
        print(f"  - {name}: {conn.ip_address} (ports: {conn.ports})")
    
    # For demo purposes, analyze some synthetic packets
    print("\nRunning HFT analysis demo...")
    
    # Generate sample report
    report = hft_analyzer.generate_hft_report()
    print("\nHFT Analysis Report:")
    print(json.dumps(report, indent=2))
    
    print("\nTo run live monitoring:")
    print("  sudo python3 src/tools/hft_analyzer.py") 