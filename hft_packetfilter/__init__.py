#!/usr/bin/env python3
"""
HFT-PacketFilter: High-Frequency Trading Network Analysis Package

A specialized Python package for High-Frequency Trading environments,
providing real-time network packet filtering, analysis, and optimization.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

# Version information
__version__ = "1.0.0"
__author__ = "HFT-PacketFilter Development Team"
__email__ = "dev@hft-packetfilter.com"
__license__ = "Apache License 2.0"
__description__ = "High-Frequency Trading Network Analysis Package"

# Core imports
from .core.hft_analyzer import HFTAnalyzer
from .core.exchange_config import ExchangeConfig, CommonExchanges
from .core.production_config import ProductionConfig

# Utility imports
from .utils.logger import HFTLogger, get_logger, configure_global_logger
from .utils.metrics_collector import MetricsCollector, get_metrics_collector, configure_metrics_collector
from .utils.alert_system import AlertSystem, get_alert_system, configure_alert_system

# Data structures
from .core.data_structures import (
    TradingMetrics,
    ExchangeConnection,
    LatencyMeasurement,
    RiskEvent,
    MarketDataQuality,
    ArbitrageOpportunity,
    SystemMetrics,
    ComplianceEvent,
    RiskLevel,
    EventType,
    ExchangeStatus
)

# Constants
from .core.constants import (
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

# Exceptions
from .core.exceptions import (
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

# Main API classes for easy access
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    
    # Core classes
    "HFTAnalyzer",
    "ExchangeConfig", 
    "CommonExchanges",
    "ProductionConfig",
    
    # Utilities
    "HFTLogger",
    "MetricsCollector",
    "AlertSystem",
    "get_logger",
    "get_metrics_collector",
    "get_alert_system",
    "configure_global_logger",
    "configure_metrics_collector",
    "configure_alert_system",
    
    # Data structures
    "TradingMetrics",
    "ExchangeConnection",
    "LatencyMeasurement",
    "RiskEvent",
    "MarketDataQuality",
    "ArbitrageOpportunity",
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
    "is_critical_error",
    "is_warning_error",
    "get_error_code",
    "format_exception_for_logging",
]

# Package-level configuration
import logging
import os

# Set up default logging
logging.getLogger(__name__).addHandler(logging.NullHandler())

# Environment variable configuration
HFT_CONFIG_PATH = os.environ.get("HFT_CONFIG_PATH", "~/.hft-packetfilter")
HFT_LOG_LEVEL = os.environ.get("HFT_LOG_LEVEL", "INFO")
HFT_PERFORMANCE_MODE = os.environ.get("HFT_PERFORMANCE_MODE", "standard")

# Package initialization message
def _init_package():
    """Initialize package with environment-specific settings"""
    if HFT_PERFORMANCE_MODE == "ultra_low_latency":
        # Configure for ultra-low latency mode
        import gc
        gc.disable()  # Disable garbage collection for consistent latency
        
        # Set CPU affinity if specified
        cpu_affinity = os.environ.get("HFT_CPU_AFFINITY")
        if cpu_affinity:
            try:
                import psutil
                cpu_list = [int(x) for x in cpu_affinity.split(",")]
                psutil.Process().cpu_affinity(cpu_list)
            except (ImportError, ValueError):
                pass

# Initialize package
_init_package()

# Quick start function
def quick_start(exchange_configs=None, performance_mode="standard"):
    """
    Quick start function for immediate HFT monitoring
    
    Args:
        exchange_configs: List of ExchangeConfig objects
        performance_mode: Performance mode ('standard', 'high_performance', 'ultra_low_latency')
    
    Returns:
        HFTAnalyzer: Configured analyzer ready for monitoring
    
    Example:
        >>> import hft_packetfilter as hft
        >>> analyzer = hft.quick_start()
        >>> analyzer.start_monitoring()
    """
    analyzer = HFTAnalyzer(performance_mode=performance_mode)
    
    if exchange_configs:
        for config in exchange_configs:
            analyzer.add_exchange(config)
    else:
        # Add default demo exchanges
        demo_exchanges = [
            ExchangeConfig("NYSE", "demo.nyse.com", [4001, 9001], "FIX/TCP", 500),
            ExchangeConfig("NASDAQ", "demo.nasdaq.com", [4002, 9002], "FIX/TCP", 600),
        ]
        for config in demo_exchanges:
            analyzer.add_exchange(config)
    
    return analyzer

# Add quick_start to __all__
__all__.append("quick_start")

# Package metadata for introspection
PACKAGE_INFO = {
    "name": "hft-packetfilter",
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "license": __license__,
    "python_requires": ">=3.8",
    "keywords": ["hft", "trading", "network", "packet", "analysis", "finance"],
    "classifiers": [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Office/Business :: Financial",
        "Topic :: System :: Networking :: Monitoring",
    ]
} 