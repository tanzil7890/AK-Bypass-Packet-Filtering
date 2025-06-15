#!/usr/bin/env python3
"""
HFT-PacketFilter Core Module

Core functionality for High-Frequency Trading network analysis.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

# Core classes
from .hft_analyzer import HFTAnalyzer
from .exchange_config import ExchangeConfig, CommonExchanges
from .production_config import ProductionConfig
from .data_structures import (
    TradingMetrics,
    LatencyMeasurement,
    RiskEvent,
    MarketDataQuality,
    ArbitrageOpportunity,
    ExchangeConnection,
    SystemMetrics,
    ComplianceEvent,
    RiskLevel,
    EventType,
    ExchangeStatus
)
from .constants import (
    DEFAULT_LATENCY_TARGET_US,
    DEFAULT_PACKET_BUFFER_SIZE,
    SUPPORTED_EXCHANGES,
    SUPPORTED_PROTOCOLS,
    COMPLIANCE_REGULATIONS,
    PERFORMANCE_MODES,
    RISK_SEVERITY_LEVELS,
    ALERT_TYPES,
    FIX_MESSAGE_TYPES,
    TRADING_SESSIONS,
    ARBITRAGE_THRESHOLDS,
    SYSTEM_LIMITS
)
from .exceptions import (
    HFTPacketFilterError,
    ExchangeConnectionError,
    LatencyThresholdExceededError,
    ComplianceViolationError,
    ConfigurationError,
    AuthenticationError,
    PermissionError,
    TimeoutError,
    ProtocolError,
    DataValidationError,
    ResourceLimitExceededError,
    PacketCaptureError,
    MetricsCollectionError,
    AlertSystemError,
    ArbitrageDetectionError,
    MarketDataQualityError,
    CriticalError,
    WarningError,
    CriticalLatencyError,
    CriticalComplianceError,
    CriticalConnectionError,
    is_critical_error,
    is_warning_error,
    get_error_code,
    format_exception_for_logging
)

__all__ = [
    # Main analyzer
    "HFTAnalyzer",
    
    # Configuration
    "ExchangeConfig",
    "CommonExchanges", 
    "ProductionConfig",
    
    # Data structures
    "TradingMetrics",
    "LatencyMeasurement",
    "RiskEvent",
    "MarketDataQuality",
    "ArbitrageOpportunity",
    "ExchangeConnection",
    "SystemMetrics",
    "ComplianceEvent",
    
    # Enums
    "RiskLevel",
    "EventType",
    "ExchangeStatus",
    
    # Constants
    "DEFAULT_LATENCY_TARGET_US",
    "DEFAULT_PACKET_BUFFER_SIZE",
    "SUPPORTED_EXCHANGES",
    "SUPPORTED_PROTOCOLS",
    "COMPLIANCE_REGULATIONS",
    "PERFORMANCE_MODES",
    "RISK_SEVERITY_LEVELS",
    "ALERT_TYPES",
    "FIX_MESSAGE_TYPES",
    "TRADING_SESSIONS",
    "ARBITRAGE_THRESHOLDS",
    "SYSTEM_LIMITS",
    
    # Exceptions
    "HFTPacketFilterError",
    "ExchangeConnectionError",
    "LatencyThresholdExceededError",
    "ComplianceViolationError",
    "ConfigurationError",
    "AuthenticationError",
    "PermissionError",
    "TimeoutError",
    "ProtocolError",
    "DataValidationError",
    "ResourceLimitExceededError",
    "PacketCaptureError",
    "MetricsCollectionError",
    "AlertSystemError",
    "ArbitrageDetectionError",
    "MarketDataQualityError",
    "CriticalError",
    "WarningError",
    "CriticalLatencyError",
    "CriticalComplianceError",
    "CriticalConnectionError",
    
    # Exception utilities
    "is_critical_error",
    "is_warning_error",
    "get_error_code",
    "format_exception_for_logging",
]
