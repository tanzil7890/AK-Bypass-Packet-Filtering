#!/usr/bin/env python3
"""
Exchange Configuration Module

Defines configuration classes for trading exchange connections.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import ipaddress
import socket


@dataclass
class ExchangeConfig:
    """
    Configuration for trading exchange connections
    
    This class defines the connection parameters and settings for
    connecting to and monitoring trading exchanges.
    
    Attributes:
        name: Exchange name (e.g., "NYSE", "NASDAQ")
        host: Exchange hostname or IP address
        ports: List of ports to monitor
        protocol: Protocol type ("FIX/TCP", "UDP", "WebSocket", etc.)
        latency_target_us: Target latency in microseconds
        is_primary: Whether this is a primary connection
        region: Geographic region of the exchange
        session_times: Trading session times
        credentials: Authentication credentials (if needed)
        ssl_config: SSL/TLS configuration
        rate_limits: Rate limiting configuration
        custom_settings: Exchange-specific custom settings
    """
    
    name: str
    host: str
    ports: List[int]
    protocol: str
    latency_target_us: float
    is_primary: bool = True
    region: str = "US"
    session_times: Optional[Dict[str, str]] = None
    credentials: Optional[Dict[str, str]] = None
    ssl_config: Optional[Dict[str, Any]] = None
    rate_limits: Optional[Dict[str, int]] = None
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation"""
        self.validate()
    
    def validate(self) -> None:
        """
        Validate exchange configuration
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Validate name
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Exchange name must be a non-empty string")
        
        # Validate host
        if not self.host:
            raise ValueError("Exchange host must be specified")
        
        # Validate host format (IP or hostname)
        try:
            # Try to parse as IP address
            ipaddress.ip_address(self.host)
        except ValueError:
            # Not an IP, validate as hostname
            if not self._is_valid_hostname(self.host):
                raise ValueError(f"Invalid hostname: {self.host}")
        
        # Validate ports
        if not self.ports or not isinstance(self.ports, list):
            raise ValueError("Ports must be a non-empty list")
        
        for port in self.ports:
            if not isinstance(port, int) or not (1 <= port <= 65535):
                raise ValueError(f"Invalid port: {port}")
        
        # Validate protocol
        valid_protocols = ["FIX/TCP", "TCP", "UDP", "WebSocket", "HTTP", "HTTPS"]
        if self.protocol not in valid_protocols:
            raise ValueError(f"Protocol must be one of: {valid_protocols}")
        
        # Validate latency target
        if not isinstance(self.latency_target_us, (int, float)) or self.latency_target_us <= 0:
            raise ValueError("Latency target must be a positive number")
        
        # Validate session times format
        if self.session_times:
            required_keys = ["market_open", "market_close"]
            for key in required_keys:
                if key not in self.session_times:
                    raise ValueError(f"Session times must include {key}")
    
    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname is valid"""
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            # Could be a valid hostname that's not resolvable in current environment
            # Basic format validation
            if len(hostname) > 253:
                return False
            
            labels = hostname.split('.')
            for label in labels:
                if not label or len(label) > 63:
                    return False
                if not all(c.isalnum() or c == '-' for c in label):
                    return False
                if label.startswith('-') or label.endswith('-'):
                    return False
            
            return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'name': self.name,
            'host': self.host,
            'ports': self.ports,
            'protocol': self.protocol,
            'latency_target_us': self.latency_target_us,
            'is_primary': self.is_primary,
            'region': self.region,
            'session_times': self.session_times,
            'credentials': self.credentials,
            'ssl_config': self.ssl_config,
            'rate_limits': self.rate_limits,
            'custom_settings': self.custom_settings
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExchangeConfig':
        """Create from dictionary representation"""
        return cls(**data)
    
    def get_connection_string(self) -> str:
        """Get connection string representation"""
        return f"{self.protocol}://{self.host}:{self.ports[0]}"
    
    def is_trading_hours(self) -> bool:
        """
        Check if current time is within trading hours
        
        Returns:
            True if within trading hours, False otherwise
        """
        if not self.session_times:
            return True  # Assume 24/7 if no session times specified
        
        from datetime import datetime, time
        import pytz
        
        # Get current time in exchange timezone
        # This is simplified - in production, you'd use proper timezone handling
        now = datetime.now().time()
        
        try:
            market_open = datetime.strptime(self.session_times['market_open'], '%H:%M').time()
            market_close = datetime.strptime(self.session_times['market_close'], '%H:%M').time()
            
            if market_open <= market_close:
                # Same day session
                return market_open <= now <= market_close
            else:
                # Overnight session
                return now >= market_open or now <= market_close
                
        except (ValueError, KeyError):
            return True  # Default to always open if parsing fails
    
    def get_primary_port(self) -> int:
        """Get primary port for this exchange"""
        return self.ports[0] if self.ports else None
    
    def supports_ssl(self) -> bool:
        """Check if SSL/TLS is configured"""
        return self.ssl_config is not None and self.ssl_config.get('enabled', False)
    
    def get_rate_limit(self, limit_type: str) -> Optional[int]:
        """
        Get rate limit for specific type
        
        Args:
            limit_type: Type of rate limit ('orders_per_second', 'messages_per_second', etc.)
            
        Returns:
            Rate limit value or None if not configured
        """
        if not self.rate_limits:
            return None
        return self.rate_limits.get(limit_type)
    
    def __str__(self) -> str:
        """String representation"""
        return f"ExchangeConfig({self.name}, {self.host}:{self.ports}, {self.protocol})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"ExchangeConfig(name='{self.name}', host='{self.host}', "
                f"ports={self.ports}, protocol='{self.protocol}', "
                f"latency_target_us={self.latency_target_us})")


# Predefined exchange configurations for common exchanges
class CommonExchanges:
    """Predefined configurations for common exchanges"""
    
    @staticmethod
    def nyse(host: str = "demo.nyse.com", latency_target_us: float = 500) -> ExchangeConfig:
        """NYSE configuration"""
        return ExchangeConfig(
            name="NYSE",
            host=host,
            ports=[4001, 9001],
            protocol="FIX/TCP",
            latency_target_us=latency_target_us,
            region="US",
            session_times={
                "market_open": "09:30",
                "market_close": "16:00"
            },
            rate_limits={
                "orders_per_second": 1000,
                "messages_per_second": 5000
            }
        )
    
    @staticmethod
    def nasdaq(host: str = "demo.nasdaq.com", latency_target_us: float = 600) -> ExchangeConfig:
        """NASDAQ configuration"""
        return ExchangeConfig(
            name="NASDAQ",
            host=host,
            ports=[4002, 9002],
            protocol="FIX/TCP",
            latency_target_us=latency_target_us,
            region="US",
            session_times={
                "market_open": "09:30",
                "market_close": "16:00"
            },
            rate_limits={
                "orders_per_second": 1200,
                "messages_per_second": 6000
            }
        )
    
    @staticmethod
    def cboe(host: str = "demo.cboe.com", latency_target_us: float = 800) -> ExchangeConfig:
        """CBOE configuration"""
        return ExchangeConfig(
            name="CBOE",
            host=host,
            ports=[4003, 9003],
            protocol="FIX/TCP",
            latency_target_us=latency_target_us,
            region="US",
            session_times={
                "market_open": "09:30",
                "market_close": "16:00"
            },
            rate_limits={
                "orders_per_second": 800,
                "messages_per_second": 4000
            }
        )
    
    @staticmethod
    def cme(host: str = "demo.cme.com", latency_target_us: float = 400) -> ExchangeConfig:
        """CME configuration"""
        return ExchangeConfig(
            name="CME",
            host=host,
            ports=[4004, 9004],
            protocol="FIX/TCP",
            latency_target_us=latency_target_us,
            region="US",
            session_times={
                "market_open": "17:00",  # Sunday
                "market_close": "16:00"   # Friday
            },
            rate_limits={
                "orders_per_second": 2000,
                "messages_per_second": 10000
            }
        )
    
    @staticmethod
    def lse(host: str = "demo.lse.com", latency_target_us: float = 1000) -> ExchangeConfig:
        """London Stock Exchange configuration"""
        return ExchangeConfig(
            name="LSE",
            host=host,
            ports=[4005, 9005],
            protocol="FIX/TCP",
            latency_target_us=latency_target_us,
            region="EU",
            session_times={
                "market_open": "08:00",
                "market_close": "16:30"
            },
            rate_limits={
                "orders_per_second": 500,
                "messages_per_second": 2500
            }
        )
    
    @staticmethod
    def get_all_demo_exchanges() -> List[ExchangeConfig]:
        """Get all demo exchange configurations"""
        return [
            CommonExchanges.nyse(),
            CommonExchanges.nasdaq(),
            CommonExchanges.cboe(),
            CommonExchanges.cme(),
            CommonExchanges.lse()
        ] 