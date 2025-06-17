#!/usr/bin/env python3
"""
Exceptions Module

Custom exception classes for HFT-PacketFilter package.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

from typing import Optional, Dict, Any


class HFTPacketFilterError(Exception):
    """
    Base exception class for HFT-PacketFilter package
    
    All custom exceptions in the package inherit from this base class.
    """
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        """
        Initialize HFT-PacketFilter exception
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            details: Optional additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "E010"  # Unknown Error
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "details": self.details
        }
    
    def __str__(self) -> str:
        """String representation of the exception"""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigurationError(HFTPacketFilterError):
    """
    Exception raised for configuration-related errors
    
    This includes invalid configuration files, missing required settings,
    or incompatible configuration values.
    """
    
    def __init__(self, message: str, config_file: Optional[str] = None,
                 config_key: Optional[str] = None):
        """
        Initialize configuration error
        
        Args:
            message: Error message
            config_file: Configuration file that caused the error
            config_key: Specific configuration key that caused the error
        """
        details = {}
        if config_file:
            details["config_file"] = config_file
        if config_key:
            details["config_key"] = config_key
        
        super().__init__(message, "E001", details)
        self.config_file = config_file
        self.config_key = config_key


class ExchangeConnectionError(HFTPacketFilterError):
    """
    Exception raised for exchange connection errors
    
    This includes connection failures, authentication errors,
    and network-related issues with trading exchanges.
    """
    
    def __init__(self, message: str, exchange_name: Optional[str] = None,
                 host: Optional[str] = None, port: Optional[int] = None):
        """
        Initialize exchange connection error
        
        Args:
            message: Error message
            exchange_name: Name of the exchange
            host: Exchange host address
            port: Exchange port number
        """
        details = {}
        if exchange_name:
            details["exchange_name"] = exchange_name
        if host:
            details["host"] = host
        if port:
            details["port"] = port
        
        super().__init__(message, "E002", details)
        self.exchange_name = exchange_name
        self.host = host
        self.port = port


class AuthenticationError(HFTPacketFilterError):
    """
    Exception raised for authentication and authorization errors
    
    This includes invalid credentials, expired tokens,
    and insufficient permissions.
    """
    
    def __init__(self, message: str, username: Optional[str] = None,
                 auth_method: Optional[str] = None):
        """
        Initialize authentication error
        
        Args:
            message: Error message
            username: Username that failed authentication
            auth_method: Authentication method used
        """
        details = {}
        if username:
            details["username"] = username
        if auth_method:
            details["auth_method"] = auth_method
        
        super().__init__(message, "E003", details)
        self.username = username
        self.auth_method = auth_method


class PermissionError(HFTPacketFilterError):
    """
    Exception raised for permission and access control errors
    
    This includes insufficient privileges for operations,
    file system permissions, and network access restrictions.
    """
    
    def __init__(self, message: str, operation: Optional[str] = None,
                 resource: Optional[str] = None):
        """
        Initialize permission error
        
        Args:
            message: Error message
            operation: Operation that was denied
            resource: Resource that access was denied to
        """
        details = {}
        if operation:
            details["operation"] = operation
        if resource:
            details["resource"] = resource
        
        super().__init__(message, "E004", details)
        self.operation = operation
        self.resource = resource


class TimeoutError(HFTPacketFilterError):
    """
    Exception raised for timeout-related errors
    
    This includes connection timeouts, read/write timeouts,
    and operation timeouts.
    """
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None,
                 operation: Optional[str] = None):
        """
        Initialize timeout error
        
        Args:
            message: Error message
            timeout_seconds: Timeout value that was exceeded
            operation: Operation that timed out
        """
        details = {}
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds
        if operation:
            details["operation"] = operation
        
        super().__init__(message, "E005", details)
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class ProtocolError(HFTPacketFilterError):
    """
    Exception raised for protocol-related errors
    
    This includes invalid protocol messages, unsupported protocol versions,
    and protocol parsing errors.
    """
    
    def __init__(self, message: str, protocol: Optional[str] = None,
                 message_type: Optional[str] = None, raw_data: Optional[bytes] = None):
        """
        Initialize protocol error
        
        Args:
            message: Error message
            protocol: Protocol name (e.g., "FIX", "TCP")
            message_type: Type of protocol message
            raw_data: Raw data that caused the error
        """
        details = {}
        if protocol:
            details["protocol"] = protocol
        if message_type:
            details["message_type"] = message_type
        if raw_data:
            details["raw_data_length"] = len(raw_data)
        
        super().__init__(message, "E006", details)
        self.protocol = protocol
        self.message_type = message_type
        self.raw_data = raw_data


class DataValidationError(HFTPacketFilterError):
    """
    Exception raised for data validation errors
    
    This includes invalid data formats, missing required fields,
    and data integrity violations.
    """
    
    def __init__(self, message: str, field_name: Optional[str] = None,
                 expected_type: Optional[str] = None, actual_value: Optional[Any] = None):
        """
        Initialize data validation error
        
        Args:
            message: Error message
            field_name: Name of the field that failed validation
            expected_type: Expected data type
            actual_value: Actual value that failed validation
        """
        details = {}
        if field_name:
            details["field_name"] = field_name
        if expected_type:
            details["expected_type"] = expected_type
        if actual_value is not None:
            details["actual_value"] = str(actual_value)
            details["actual_type"] = type(actual_value).__name__
        
        super().__init__(message, "E007", details)
        self.field_name = field_name
        self.expected_type = expected_type
        self.actual_value = actual_value


class ResourceLimitExceededError(HFTPacketFilterError):
    """
    Exception raised when system resource limits are exceeded
    
    This includes memory limits, CPU limits, network bandwidth limits,
    and file descriptor limits.
    """
    
    def __init__(self, message: str, resource_type: Optional[str] = None,
                 limit_value: Optional[float] = None, current_value: Optional[float] = None):
        """
        Initialize resource limit exceeded error
        
        Args:
            message: Error message
            resource_type: Type of resource (e.g., "memory", "cpu", "network")
            limit_value: Resource limit that was exceeded
            current_value: Current resource usage
        """
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if limit_value is not None:
            details["limit_value"] = limit_value
        if current_value is not None:
            details["current_value"] = current_value
        
        super().__init__(message, "E008", details)
        self.resource_type = resource_type
        self.limit_value = limit_value
        self.current_value = current_value


class LatencyThresholdExceededError(HFTPacketFilterError):
    """
    Exception raised when latency thresholds are exceeded
    
    This is a specialized exception for HFT environments where
    latency violations are critical.
    """
    
    def __init__(self, message: str, exchange_name: str, 
                 actual_latency_us: float, threshold_latency_us: float):
        """
        Initialize latency threshold exceeded error
        
        Args:
            message: Error message
            exchange_name: Name of the exchange
            actual_latency_us: Actual latency in microseconds
            threshold_latency_us: Latency threshold in microseconds
        """
        details = {
            "exchange_name": exchange_name,
            "actual_latency_us": actual_latency_us,
            "threshold_latency_us": threshold_latency_us,
            "excess_latency_us": actual_latency_us - threshold_latency_us
        }
        
        super().__init__(message, "E005", details)
        self.exchange_name = exchange_name
        self.actual_latency_us = actual_latency_us
        self.threshold_latency_us = threshold_latency_us


class ComplianceViolationError(HFTPacketFilterError):
    """
    Exception raised for regulatory compliance violations
    
    This includes violations of trading regulations, audit requirements,
    and reporting obligations.
    """
    
    def __init__(self, message: str, regulation: str, 
                 violation_type: str, severity: str = "HIGH"):
        """
        Initialize compliance violation error
        
        Args:
            message: Error message
            regulation: Regulation that was violated (e.g., "MiFID_II")
            violation_type: Type of violation
            severity: Severity level of the violation
        """
        details = {
            "regulation": regulation,
            "violation_type": violation_type,
            "severity": severity
        }
        
        super().__init__(message, "E007", details)
        self.regulation = regulation
        self.violation_type = violation_type
        self.severity = severity


class PacketCaptureError(HFTPacketFilterError):
    """
    Exception raised for packet capture errors
    
    This includes interface errors, permission issues,
    and capture configuration problems.
    """
    
    def __init__(self, message: str, interface: Optional[str] = None,
                 capture_filter: Optional[str] = None):
        """
        Initialize packet capture error
        
        Args:
            message: Error message
            interface: Network interface name
            capture_filter: Capture filter expression
        """
        details = {}
        if interface:
            details["interface"] = interface
        if capture_filter:
            details["capture_filter"] = capture_filter
        
        super().__init__(message, "E009", details)
        self.interface = interface
        self.capture_filter = capture_filter


class MetricsCollectionError(HFTPacketFilterError):
    """
    Exception raised for metrics collection errors
    
    This includes metrics export failures, storage issues,
    and aggregation problems.
    """
    
    def __init__(self, message: str, metric_name: Optional[str] = None,
                 export_format: Optional[str] = None):
        """
        Initialize metrics collection error
        
        Args:
            message: Error message
            metric_name: Name of the metric that failed
            export_format: Export format that failed
        """
        details = {}
        if metric_name:
            details["metric_name"] = metric_name
        if export_format:
            details["export_format"] = export_format
        
        super().__init__(message, "E009", details)
        self.metric_name = metric_name
        self.export_format = export_format


class AlertSystemError(HFTPacketFilterError):
    """
    Exception raised for alert system errors
    
    This includes alert delivery failures, configuration issues,
    and notification problems.
    """
    
    def __init__(self, message: str, alert_type: Optional[str] = None,
                 delivery_method: Optional[str] = None):
        """
        Initialize alert system error
        
        Args:
            message: Error message
            alert_type: Type of alert that failed
            delivery_method: Alert delivery method (e.g., "webhook", "email")
        """
        details = {}
        if alert_type:
            details["alert_type"] = alert_type
        if delivery_method:
            details["delivery_method"] = delivery_method
        
        super().__init__(message, "E009", details)
        self.alert_type = alert_type
        self.delivery_method = delivery_method


class ArbitrageDetectionError(HFTPacketFilterError):
    """
    Exception raised for arbitrage detection errors
    
    This includes price feed issues, calculation errors,
    and opportunity validation problems.
    """
    
    def __init__(self, message: str, symbol: Optional[str] = None,
                 exchanges: Optional[list] = None):
        """
        Initialize arbitrage detection error
        
        Args:
            message: Error message
            symbol: Trading symbol
            exchanges: List of exchanges involved
        """
        details = {}
        if symbol:
            details["symbol"] = symbol
        if exchanges:
            details["exchanges"] = exchanges
        
        super().__init__(message, "E009", details)
        self.symbol = symbol
        self.exchanges = exchanges


class MarketDataQualityError(HFTPacketFilterError):
    """
    Exception raised for market data quality issues
    
    This includes feed quality problems, data integrity issues,
    and validation failures.
    """
    
    def __init__(self, message: str, feed_name: Optional[str] = None,
                 quality_score: Optional[float] = None):
        """
        Initialize market data quality error
        
        Args:
            message: Error message
            feed_name: Name of the market data feed
            quality_score: Quality score that triggered the error
        """
        details = {}
        if feed_name:
            details["feed_name"] = feed_name
        if quality_score is not None:
            details["quality_score"] = quality_score
        
        super().__init__(message, "E009", details)
        self.feed_name = feed_name
        self.quality_score = quality_score


# Exception hierarchy for easy catching
class CriticalError(HFTPacketFilterError):
    """Base class for critical errors that require immediate attention"""
    pass


class WarningError(HFTPacketFilterError):
    """Base class for warning-level errors that should be logged but don't stop operation"""
    pass


# Make critical errors inherit from CriticalError
class CriticalLatencyError(LatencyThresholdExceededError, CriticalError):
    """Critical latency threshold violation"""
    pass


class CriticalComplianceError(ComplianceViolationError, CriticalError):
    """Critical compliance violation"""
    pass


class CriticalConnectionError(ExchangeConnectionError, CriticalError):
    """Critical exchange connection failure"""
    pass


# Utility functions for exception handling
def is_critical_error(exception: Exception) -> bool:
    """Check if an exception is critical"""
    return isinstance(exception, CriticalError)


def is_warning_error(exception: Exception) -> bool:
    """Check if an exception is a warning"""
    return isinstance(exception, WarningError)


def get_error_code(exception: Exception) -> str:
    """Get error code from exception"""
    if isinstance(exception, HFTPacketFilterError):
        return exception.error_code
    return "E010"  # Unknown Error


def format_exception_for_logging(exception: Exception) -> Dict[str, Any]:
    """Format exception for structured logging"""
    if isinstance(exception, HFTPacketFilterError):
        return exception.to_dict()
    
    return {
        "error_type": type(exception).__name__,
        "message": str(exception),
        "error_code": "E010",
        "details": {}
    } 