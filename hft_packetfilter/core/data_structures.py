#!/usr/bin/env python3
"""
Data Structures Module

Core data structures for HFT-PacketFilter package.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EventType(Enum):
    """Event type enumeration"""
    LATENCY_ALERT = "latency_alert"
    LATENCY_VIOLATION = "latency_violation"
    PACKET_LOSS = "packet_loss"
    SECURITY_THREAT = "security_threat"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ERROR = "system_error"
    ARBITRAGE_OPPORTUNITY = "arbitrage_opportunity"
    MARKET_DATA_QUALITY = "market_data_quality"


class ExchangeStatus(Enum):
    """Exchange connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    ERROR = "error"
    MAINTENANCE = "maintenance"


@dataclass
class TradingMetrics:
    """
    Trading performance metrics for an exchange
    
    Attributes:
        exchange_name: Name of the exchange
        timestamp: Timestamp of metrics collection
        latency_us: Average latency in microseconds
        jitter_us: Latency jitter in microseconds
        packet_loss: Packet loss percentage (0.0-1.0)
        throughput_mbps: Throughput in Mbps
        order_rate: Orders per second
        market_data_rate: Market data messages per second
        connection_uptime: Connection uptime in seconds
        error_count: Number of errors in measurement period
    """
    
    exchange_name: str
    timestamp: float = field(default_factory=time.time)
    latency_us: float = 0.0
    jitter_us: float = 0.0
    packet_loss: float = 0.0
    throughput_mbps: float = 0.0
    order_rate: float = 0.0
    market_data_rate: float = 0.0
    connection_uptime: float = 0.0
    error_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'exchange_name': self.exchange_name,
            'timestamp': self.timestamp,
            'latency_us': self.latency_us,
            'jitter_us': self.jitter_us,
            'packet_loss': self.packet_loss,
            'throughput_mbps': self.throughput_mbps,
            'order_rate': self.order_rate,
            'market_data_rate': self.market_data_rate,
            'connection_uptime': self.connection_uptime,
            'error_count': self.error_count
        }
    
    def is_healthy(self, latency_threshold_us: float = 1000) -> bool:
        """Check if metrics indicate healthy connection"""
        return (
            self.latency_us < latency_threshold_us and
            self.packet_loss < 0.01 and  # Less than 1% packet loss
            self.error_count == 0
        )


@dataclass
class LatencyMeasurement:
    """
    Individual latency measurement
    
    Attributes:
        timestamp: Measurement timestamp
        exchange_name: Exchange name
        latency_us: Latency in microseconds
        packet_size: Size of packet in bytes
        sequence_number: Packet sequence number
        round_trip: Whether this is round-trip latency
        source_ip: Source IP address
        destination_ip: Destination IP address
        protocol: Network protocol used
    """
    
    timestamp: float
    exchange_name: str
    latency_us: float
    packet_size: int = 0
    sequence_number: Optional[int] = None
    round_trip: bool = False
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    protocol: str = "TCP"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'exchange_name': self.exchange_name,
            'latency_us': self.latency_us,
            'packet_size': self.packet_size,
            'sequence_number': self.sequence_number,
            'round_trip': self.round_trip,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'protocol': self.protocol
        }


@dataclass
class RiskEvent:
    """
    Risk management event
    
    Attributes:
        timestamp: Event timestamp
        event_type: Type of risk event
        severity: Risk severity level
        source_ip: Source IP address
        destination_ip: Destination IP address
        description: Event description
        exchange_name: Associated exchange (if applicable)
        rule_triggered: Security rule that triggered the event
        mitigation_action: Action taken to mitigate risk
        resolved: Whether the event has been resolved
        metadata: Additional event metadata
    """
    
    timestamp: float
    event_type: str
    severity: str
    source_ip: str
    destination_ip: str
    description: str
    exchange_name: Optional[str] = None
    rule_triggered: Optional[str] = None
    mitigation_action: Optional[str] = None
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'severity': self.severity,
            'source_ip': self.source_ip,
            'destination_ip': self.destination_ip,
            'description': self.description,
            'exchange_name': self.exchange_name,
            'rule_triggered': self.rule_triggered,
            'mitigation_action': self.mitigation_action,
            'resolved': self.resolved,
            'metadata': self.metadata
        }
    
    def is_critical(self) -> bool:
        """Check if this is a critical risk event"""
        return self.severity in ["HIGH", "CRITICAL"]


@dataclass
class MarketDataQuality:
    """
    Market data quality assessment
    
    Attributes:
        timestamp: Assessment timestamp
        exchange_name: Exchange name
        feed_name: Market data feed name
        quality_score: Overall quality score (0-100)
        gap_count: Number of message gaps detected
        sequence_errors: Number of sequence errors
        latency_us: Feed latency in microseconds
        message_rate: Messages per second
        duplicate_count: Number of duplicate messages
        corruption_count: Number of corrupted messages
        uptime_percentage: Feed uptime percentage
        last_message_time: Timestamp of last received message
    """
    
    timestamp: float
    exchange_name: str
    feed_name: str
    quality_score: float = 100.0
    gap_count: int = 0
    sequence_errors: int = 0
    latency_us: float = 0.0
    message_rate: float = 0.0
    duplicate_count: int = 0
    corruption_count: int = 0
    uptime_percentage: float = 100.0
    last_message_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'exchange_name': self.exchange_name,
            'feed_name': self.feed_name,
            'quality_score': self.quality_score,
            'gap_count': self.gap_count,
            'sequence_errors': self.sequence_errors,
            'latency_us': self.latency_us,
            'message_rate': self.message_rate,
            'duplicate_count': self.duplicate_count,
            'corruption_count': self.corruption_count,
            'uptime_percentage': self.uptime_percentage,
            'last_message_time': self.last_message_time
        }
    
    def is_acceptable_quality(self, min_score: float = 95.0) -> bool:
        """Check if quality meets minimum standards"""
        return self.quality_score >= min_score


@dataclass
class ArbitrageOpportunity:
    """
    Cross-exchange arbitrage opportunity
    
    Attributes:
        timestamp: Opportunity timestamp
        symbol: Trading symbol
        buy_exchange: Exchange to buy from
        sell_exchange: Exchange to sell to
        buy_price: Buy price
        sell_price: Sell price
        spread: Price spread (sell_price - buy_price)
        spread_percentage: Spread as percentage of buy price
        volume: Available volume
        estimated_profit: Estimated profit after fees
        execution_time_us: Estimated execution time in microseconds
        confidence: Confidence level (0.0-1.0)
        expires_at: Opportunity expiration timestamp
    """
    
    timestamp: float
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float
    spread_percentage: float
    volume: float
    estimated_profit: float = 0.0
    execution_time_us: float = 0.0
    confidence: float = 1.0
    expires_at: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.spread = self.sell_price - self.buy_price
        self.spread_percentage = (self.spread / self.buy_price) * 100 if self.buy_price > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'symbol': self.symbol,
            'buy_exchange': self.buy_exchange,
            'sell_exchange': self.sell_exchange,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'spread': self.spread,
            'spread_percentage': self.spread_percentage,
            'volume': self.volume,
            'estimated_profit': self.estimated_profit,
            'execution_time_us': self.execution_time_us,
            'confidence': self.confidence,
            'expires_at': self.expires_at
        }
    
    def is_profitable(self, min_spread_percentage: float = 0.1) -> bool:
        """Check if opportunity is profitable"""
        return self.spread_percentage >= min_spread_percentage and self.estimated_profit > 0
    
    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


@dataclass
class ExchangeConnection:
    """
    Exchange connection information
    
    Attributes:
        name: Exchange name
        ip_address: IP address
        ports: List of ports
        protocol: Connection protocol
        status: Connection status
        latency_target_us: Target latency in microseconds
        is_primary: Whether this is primary connection
        connected_at: Connection timestamp
        last_heartbeat: Last heartbeat timestamp
        error_count: Number of connection errors
        reconnect_count: Number of reconnection attempts
    """
    
    name: str
    ip_address: str
    ports: List[int]
    protocol: str
    status: ExchangeStatus = ExchangeStatus.DISCONNECTED
    latency_target_us: float = 1000.0
    is_primary: bool = True
    connected_at: Optional[float] = None
    last_heartbeat: Optional[float] = None
    error_count: int = 0
    reconnect_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'ip_address': self.ip_address,
            'ports': self.ports,
            'protocol': self.protocol,
            'status': self.status.value,
            'latency_target_us': self.latency_target_us,
            'is_primary': self.is_primary,
            'connected_at': self.connected_at,
            'last_heartbeat': self.last_heartbeat,
            'error_count': self.error_count,
            'reconnect_count': self.reconnect_count
        }
    
    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.status == ExchangeStatus.CONNECTED
    
    def get_uptime(self) -> float:
        """Get connection uptime in seconds"""
        if self.connected_at is None:
            return 0.0
        return time.time() - self.connected_at


@dataclass
class SystemMetrics:
    """
    System performance metrics
    
    Attributes:
        timestamp: Metrics timestamp
        cpu_usage_percent: CPU usage percentage
        memory_usage_percent: Memory usage percentage
        network_rx_mbps: Network receive rate in Mbps
        network_tx_mbps: Network transmit rate in Mbps
        disk_usage_percent: Disk usage percentage
        packet_processing_rate: Packets processed per second
        active_connections: Number of active connections
        thread_count: Number of active threads
        gc_collections: Garbage collection count
    """
    
    timestamp: float = field(default_factory=time.time)
    cpu_usage_percent: float = 0.0
    memory_usage_percent: float = 0.0
    network_rx_mbps: float = 0.0
    network_tx_mbps: float = 0.0
    disk_usage_percent: float = 0.0
    packet_processing_rate: float = 0.0
    active_connections: int = 0
    thread_count: int = 0
    gc_collections: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_percent': self.memory_usage_percent,
            'network_rx_mbps': self.network_rx_mbps,
            'network_tx_mbps': self.network_tx_mbps,
            'disk_usage_percent': self.disk_usage_percent,
            'packet_processing_rate': self.packet_processing_rate,
            'active_connections': self.active_connections,
            'thread_count': self.thread_count,
            'gc_collections': self.gc_collections
        }
    
    def is_healthy(self) -> bool:
        """Check if system metrics are healthy"""
        return (
            self.cpu_usage_percent < 80.0 and
            self.memory_usage_percent < 85.0 and
            self.disk_usage_percent < 90.0
        )


@dataclass
class ComplianceEvent:
    """
    Regulatory compliance event
    
    Attributes:
        timestamp: Event timestamp
        regulation: Regulation name (e.g., "MiFID_II", "Reg_NMS")
        event_type: Type of compliance event
        severity: Event severity
        description: Event description
        exchange_name: Associated exchange
        order_id: Associated order ID
        symbol: Trading symbol
        action_required: Whether action is required
        deadline: Compliance deadline
        metadata: Additional compliance data
    """
    
    timestamp: float
    regulation: str
    event_type: str
    severity: str
    description: str
    exchange_name: Optional[str] = None
    order_id: Optional[str] = None
    symbol: Optional[str] = None
    action_required: bool = False
    deadline: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'regulation': self.regulation,
            'event_type': self.event_type,
            'severity': self.severity,
            'description': self.description,
            'exchange_name': self.exchange_name,
            'order_id': self.order_id,
            'symbol': self.symbol,
            'action_required': self.action_required,
            'deadline': self.deadline,
            'metadata': self.metadata
        }
    
    def is_overdue(self) -> bool:
        """Check if compliance deadline is overdue"""
        if self.deadline is None:
            return False
        return time.time() > self.deadline 