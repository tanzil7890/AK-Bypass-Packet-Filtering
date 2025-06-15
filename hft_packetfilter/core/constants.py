#!/usr/bin/env python3
"""
Constants Module

Package-wide constants and configuration values for HFT-PacketFilter.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

from typing import Dict, List, Any

# Package Information
PACKAGE_NAME = "hft-packetfilter"
PACKAGE_VERSION = "1.0.0"
PACKAGE_DESCRIPTION = "High-Frequency Trading Network Analysis Package"
PACKAGE_AUTHOR = "HFT-PacketFilter Development Team"
PACKAGE_LICENSE = "Apache License 2.0"

# Performance Constants
DEFAULT_LATENCY_TARGET_US = 1000.0  # 1 millisecond default latency target
DEFAULT_PACKET_BUFFER_SIZE = 65536  # 64KB default buffer size
DEFAULT_CAPTURE_TIMEOUT_MS = 1000   # 1 second capture timeout
DEFAULT_METRICS_INTERVAL_SEC = 60   # 1 minute metrics collection interval

# Memory and Performance
ULTRA_LOW_LATENCY_BUFFER_SIZE = 1048576    # 1MB for ultra-low latency
HIGH_PERFORMANCE_BUFFER_SIZE = 524288      # 512KB for high performance
STANDARD_BUFFER_SIZE = 65536               # 64KB for standard mode

# Network Constants
DEFAULT_CAPTURE_INTERFACE = "any"
DEFAULT_PROMISCUOUS_MODE = False
MAX_PACKET_SIZE = 9000  # Jumbo frame size
MIN_PACKET_SIZE = 64    # Minimum Ethernet frame size

# Supported Exchanges
SUPPORTED_EXCHANGES = [
    "NYSE",
    "NASDAQ", 
    "CBOE",
    "CME",
    "ICE",
    "LSE",
    "EUREX",
    "TSE",
    "HKEX",
    "ASX"
]

# Exchange Default Ports
EXCHANGE_DEFAULT_PORTS: Dict[str, List[int]] = {
    "NYSE": [4001, 9001],
    "NASDAQ": [4002, 9002],
    "CBOE": [4003, 9003],
    "CME": [4004, 9004],
    "ICE": [4005, 9005],
    "LSE": [4006, 9006],
    "EUREX": [4007, 9007],
    "TSE": [4008, 9008],
    "HKEX": [4009, 9009],
    "ASX": [4010, 9010]
}

# Supported Protocols
SUPPORTED_PROTOCOLS = [
    "FIX/TCP",
    "TCP",
    "UDP",
    "WebSocket",
    "HTTP",
    "HTTPS",
    "BINARY"
]

# FIX Protocol Versions
SUPPORTED_FIX_VERSIONS = [
    "FIX.4.0",
    "FIX.4.1", 
    "FIX.4.2",
    "FIX.4.3",
    "FIX.4.4",
    "FIXT.1.1",
    "FIX.5.0",
    "FIX.5.0SP1",
    "FIX.5.0SP2"
]

# Market Data Feed Types
MARKET_DATA_FEED_TYPES = [
    "Level1",
    "Level2", 
    "Level3",
    "OrderBook",
    "Trades",
    "OHLC",
    "Statistics"
]

# Compliance Regulations
COMPLIANCE_REGULATIONS = [
    "MiFID_II",
    "Reg_NMS",
    "CFTC_Rules",
    "ESMA_Guidelines",
    "FCA_Rules",
    "SEC_Rules",
    "FINRA_Rules",
    "IIROC_Rules"
]

# Risk Management Constants
RISK_SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
DEFAULT_RISK_THRESHOLDS: Dict[str, float] = {
    "latency_threshold_us": 1000.0,
    "packet_loss_threshold": 0.01,  # 1%
    "cpu_usage_threshold": 80.0,    # 80%
    "memory_usage_threshold": 85.0, # 85%
    "disk_usage_threshold": 90.0,   # 90%
    "error_rate_threshold": 0.05    # 5%
}

# Alert Types
ALERT_TYPES = [
    "latency_alert",
    "packet_loss_alert",
    "security_threat",
    "compliance_violation",
    "system_error",
    "connection_failure",
    "arbitrage_opportunity",
    "market_data_quality"
]

# Performance Modes
PERFORMANCE_MODES = [
    "standard",
    "high_performance", 
    "ultra_low_latency"
]

# Logging Constants
LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LOG_FORMATS = ["simple", "structured", "json"]
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "structured"

# Metrics Export Formats
METRICS_EXPORT_FORMATS = ["json", "prometheus", "influxdb", "csv"]
DEFAULT_METRICS_FORMAT = "json"

# File Extensions
SUPPORTED_CONFIG_FORMATS = [".yaml", ".yml", ".json"]
SUPPORTED_EXPORT_FORMATS = [".json", ".yaml", ".csv", ".xlsx"]

# Directory Structure
DEFAULT_DATA_DIRECTORIES = [
    "logs",
    "metrics", 
    "exports",
    "backups",
    "config",
    "temp"
]

# Trading Session Times (UTC)
TRADING_SESSIONS: Dict[str, Dict[str, str]] = {
    "NYSE": {
        "pre_market": "09:00",
        "market_open": "14:30",  # 9:30 AM EST
        "market_close": "21:00", # 4:00 PM EST
        "after_hours": "01:00"   # 8:00 PM EST
    },
    "NASDAQ": {
        "pre_market": "09:00",
        "market_open": "14:30",
        "market_close": "21:00",
        "after_hours": "01:00"
    },
    "LSE": {
        "market_open": "08:00",
        "market_close": "16:30"
    },
    "TSE": {
        "morning_open": "00:00",   # 9:00 AM JST
        "morning_close": "02:30",  # 11:30 AM JST
        "afternoon_open": "03:30", # 12:30 PM JST
        "afternoon_close": "06:00" # 3:00 PM JST
    }
}

# Currency Codes
SUPPORTED_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RUB", "CNY",
    "HKD", "SGD", "KRW", "INR", "BRL", "MXN", "ZAR", "TRY"
]

# Asset Classes
ASSET_CLASSES = [
    "Equities",
    "Fixed_Income",
    "Derivatives",
    "Commodities", 
    "FX",
    "Crypto",
    "ETFs",
    "Options",
    "Futures",
    "Swaps"
]

# Order Types
ORDER_TYPES = [
    "Market",
    "Limit",
    "Stop",
    "Stop_Limit",
    "IOC",  # Immediate or Cancel
    "FOK",  # Fill or Kill
    "GTC",  # Good Till Cancel
    "GTD",  # Good Till Date
    "MOO",  # Market on Open
    "MOC",  # Market on Close
    "LOO",  # Limit on Open
    "LOC"   # Limit on Close
]

# Message Types (FIX Protocol)
FIX_MESSAGE_TYPES = {
    "0": "Heartbeat",
    "1": "Test_Request",
    "2": "Resend_Request", 
    "3": "Reject",
    "4": "Sequence_Reset",
    "5": "Logout",
    "6": "IOI",
    "7": "Advertisement",
    "8": "Execution_Report",
    "9": "Order_Cancel_Reject",
    "A": "Logon",
    "B": "News",
    "C": "Email",
    "D": "New_Order_Single",
    "E": "New_Order_List",
    "F": "Order_Cancel_Request",
    "G": "Order_Cancel_Replace_Request",
    "H": "Order_Status_Request",
    "J": "Allocation_Instruction",
    "K": "List_Cancel_Request",
    "L": "List_Execute",
    "M": "List_Status_Request",
    "N": "List_Status",
    "P": "Allocation_Instruction_Ack",
    "Q": "Dont_Know_Trade",
    "R": "Quote_Request",
    "S": "Quote",
    "T": "Settlement_Instructions",
    "V": "Market_Data_Request",
    "W": "Market_Data_Snapshot_Full_Refresh",
    "X": "Market_Data_Incremental_Refresh",
    "Y": "Market_Data_Request_Reject",
    "Z": "Quote_Cancel",
    "a": "Quote_Status_Request",
    "b": "Mass_Quote_Acknowledgement",
    "c": "Security_Definition_Request",
    "d": "Security_Definition",
    "e": "Security_Status_Request",
    "f": "Security_Status",
    "g": "Trading_Session_Status_Request",
    "h": "Trading_Session_Status"
}

# Quality Score Thresholds
QUALITY_SCORE_THRESHOLDS = {
    "excellent": 98.0,
    "good": 95.0,
    "acceptable": 90.0,
    "poor": 80.0,
    "unacceptable": 70.0
}

# Arbitrage Constants
ARBITRAGE_THRESHOLDS = {
    "min_spread_percentage": 0.1,    # 0.1% minimum spread
    "max_execution_time_us": 10000,  # 10ms maximum execution time
    "min_volume": 100,               # Minimum volume for opportunity
    "min_profit_usd": 10.0          # Minimum profit in USD
}

# System Resource Limits
SYSTEM_LIMITS = {
    "max_memory_usage_percent": 85.0,
    "max_cpu_usage_percent": 80.0,
    "max_disk_usage_percent": 90.0,
    "max_network_utilization_percent": 80.0,
    "max_open_files": 65536,
    "max_threads": 1000
}

# Timeout Constants (in seconds)
TIMEOUTS = {
    "connection_timeout": 30,
    "read_timeout": 10,
    "write_timeout": 10,
    "heartbeat_interval": 30,
    "reconnect_interval": 5,
    "health_check_interval": 60,
    "metrics_collection_interval": 60,
    "alert_throttle_interval": 300  # 5 minutes
}

# Retry Constants
RETRY_SETTINGS = {
    "max_retries": 3,
    "retry_delay": 1.0,
    "backoff_multiplier": 2.0,
    "max_retry_delay": 60.0
}

# Compression Settings
COMPRESSION_SETTINGS = {
    "enabled": True,
    "algorithm": "gzip",  # gzip, lz4, zstd
    "level": 6,           # Compression level (1-9)
    "threshold_bytes": 1024  # Minimum size to compress
}

# Encryption Settings
ENCRYPTION_SETTINGS = {
    "algorithm": "AES-256-GCM",
    "key_rotation_hours": 24,
    "iv_length": 12
}

# Database Constants (if using database storage)
DATABASE_SETTINGS = {
    "connection_pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,  # 1 hour
    "echo": False
}

# API Constants
API_SETTINGS = {
    "default_port": 8080,
    "max_request_size": 10485760,  # 10MB
    "rate_limit_requests": 1000,
    "rate_limit_window": 3600,     # 1 hour
    "cors_enabled": True,
    "api_version": "v1"
}

# Monitoring Constants
MONITORING_SETTINGS = {
    "health_check_endpoints": [
        "/health",
        "/metrics", 
        "/status"
    ],
    "prometheus_metrics_path": "/metrics",
    "dashboard_refresh_interval": 5,  # seconds
    "alert_aggregation_window": 300   # 5 minutes
}

# Feature Flags
FEATURE_FLAGS = {
    "enable_machine_learning": False,
    "enable_advanced_analytics": True,
    "enable_real_time_dashboard": False,
    "enable_compliance_monitoring": True,
    "enable_arbitrage_detection": True,
    "enable_market_data_quality": True,
    "enable_risk_management": True,
    "enable_performance_optimization": True
}

# Version Compatibility
MINIMUM_PYTHON_VERSION = "3.9"
SUPPORTED_PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12"]

# Platform Support
SUPPORTED_PLATFORMS = [
    "linux",
    "darwin",  # macOS
    "win32"    # Windows (limited support)
]

# Error Codes
ERROR_CODES = {
    "E001": "Configuration Error",
    "E002": "Connection Error", 
    "E003": "Authentication Error",
    "E004": "Permission Error",
    "E005": "Timeout Error",
    "E006": "Protocol Error",
    "E007": "Data Validation Error",
    "E008": "Resource Limit Exceeded",
    "E009": "System Error",
    "E010": "Unknown Error"
}

# Success Codes
SUCCESS_CODES = {
    "S001": "Operation Successful",
    "S002": "Connection Established",
    "S003": "Data Processed",
    "S004": "Export Completed",
    "S005": "Configuration Updated"
}

# Default Configuration Values
DEFAULT_CONFIG = {
    "performance_mode": "standard",
    "log_level": "INFO",
    "metrics_enabled": True,
    "alerts_enabled": True,
    "audit_enabled": True,
    "ssl_enabled": False,
    "compression_enabled": True,
    "backup_enabled": True,
    "dashboard_enabled": False
} 