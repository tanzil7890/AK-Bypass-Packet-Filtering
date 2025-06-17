#!/usr/bin/env python3
"""
Production Configuration Module

Manages production environment configurations for HFT-PacketFilter.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import os
import yaml
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


@dataclass
class ProductionConfig:
    """
    Production configuration for HFT-PacketFilter
    
    This class manages all production environment settings including
    performance optimization, logging, monitoring, and deployment configurations.
    """
    
    # Performance settings
    performance_mode: str = "standard"  # standard, high_performance, ultra_low_latency
    cpu_affinity: Optional[List[int]] = None
    memory_pool_size: str = "1GB"
    network_interface: Optional[str] = None
    packet_buffer_size: int = 65536
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "structured"  # simple, structured, json
    log_file: Optional[str] = None
    log_rotation: bool = True
    log_max_size: str = "100MB"
    log_backup_count: int = 5
    
    # Monitoring settings
    metrics_enabled: bool = True
    metrics_export_format: str = "json"  # json, prometheus, influxdb
    metrics_export_interval: int = 60  # seconds
    metrics_retention_days: int = 30
    dashboard_enabled: bool = False
    dashboard_port: int = 8080
    
    # Security settings
    ssl_enabled: bool = False
    ssl_cert_file: Optional[str] = None
    ssl_key_file: Optional[str] = None
    ssl_ca_file: Optional[str] = None
    authentication_enabled: bool = False
    api_key: Optional[str] = None
    
    # Alert configuration
    alerts_enabled: bool = True
    alert_webhook_url: Optional[str] = None
    alert_email_smtp: Optional[Dict[str, str]] = None
    alert_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "latency_threshold_us": 1000,
        "packet_loss_threshold": 0.01,
        "cpu_usage_threshold": 80.0,
        "memory_usage_threshold": 85.0
    })
    
    # Storage settings
    data_directory: str = "/var/lib/hft-packetfilter"
    temp_directory: str = "/tmp/hft-packetfilter"
    backup_enabled: bool = True
    backup_retention_days: int = 90
    compression_enabled: bool = True
    
    # Compliance settings
    audit_enabled: bool = True
    audit_retention_days: int = 2555  # 7 years for financial compliance
    compliance_regulations: List[str] = field(default_factory=list)
    regulatory_reporting_enabled: bool = False
    
    # Network settings
    capture_interface: str = "any"
    capture_filter: Optional[str] = None
    promiscuous_mode: bool = False
    capture_timeout: int = 1000  # milliseconds
    
    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        self.validate()
        self._setup_directories()
    
    def validate(self) -> None:
        """Validate configuration settings"""
        # Validate performance mode
        valid_modes = ["standard", "high_performance", "ultra_low_latency"]
        if self.performance_mode not in valid_modes:
            raise ValueError(f"Performance mode must be one of: {valid_modes}")
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        
        # Validate metrics export format
        valid_formats = ["json", "prometheus", "influxdb", "csv"]
        if self.metrics_export_format not in valid_formats:
            raise ValueError(f"Metrics export format must be one of: {valid_formats}")
        
        # Validate CPU affinity
        if self.cpu_affinity:
            import psutil
            available_cpus = list(range(psutil.cpu_count()))
            for cpu in self.cpu_affinity:
                if cpu not in available_cpus:
                    raise ValueError(f"CPU {cpu} not available. Available CPUs: {available_cpus}")
        
        # Validate memory pool size
        memory_bytes = self._parse_memory_size(self.memory_pool_size)
        if memory_bytes is None:
            raise ValueError(f"Invalid memory pool size format: {self.memory_pool_size}")
        
        # Validate SSL configuration
        if self.ssl_enabled:
            if not self.ssl_cert_file or not self.ssl_key_file:
                raise ValueError("SSL certificate and key files must be specified when SSL is enabled")
            
            if not os.path.exists(self.ssl_cert_file):
                raise ValueError(f"SSL certificate file not found: {self.ssl_cert_file}")
            
            if not os.path.exists(self.ssl_key_file):
                raise ValueError(f"SSL key file not found: {self.ssl_key_file}")
    
    def _parse_memory_size(self, size_str: str) -> Optional[int]:
        """Parse memory size string to bytes"""
        size_str = size_str.upper().strip()
        
        # Check suffixes in order of length (longest first)
        multipliers = [
            ('TB', 1024**4),
            ('GB', 1024**3),
            ('MB', 1024**2),
            ('KB', 1024),
            ('B', 1)
        ]
        
        for suffix, multiplier in multipliers:
            if size_str.endswith(suffix):
                try:
                    number_part = size_str[:-len(suffix)]
                    number = float(number_part)
                    return int(number * multiplier)
                except ValueError:
                    return None
        
        # Try parsing as plain number (bytes)
        try:
            return int(size_str)
        except ValueError:
            return None
    
    def _setup_directories(self) -> None:
        """Create necessary directories"""
        directories = [
            self.data_directory,
            self.temp_directory,
            os.path.join(self.data_directory, "logs"),
            os.path.join(self.data_directory, "metrics"),
            os.path.join(self.data_directory, "exports"),
            os.path.join(self.data_directory, "backups")
        ]
        
        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Log warning but don't fail - might be running in restricted environment
                pass
    
    @classmethod
    def from_file(cls, config_path: str) -> 'ProductionConfig':
        """
        Load configuration from file
        
        Args:
            config_path: Path to configuration file (YAML or JSON)
            
        Returns:
            ProductionConfig instance
        """
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                data = yaml.safe_load(f)
            elif config_path.endswith('.json'):
                data = json.load(f)
            else:
                raise ValueError("Configuration file must be YAML or JSON")
        
        return cls(**data)
    
    @classmethod
    def from_environment(cls) -> 'ProductionConfig':
        """
        Load configuration from environment variables
        
        Returns:
            ProductionConfig instance with environment-based settings
        """
        config_data = {}
        
        # Map environment variables to config fields
        env_mapping = {
            'HFT_PERFORMANCE_MODE': 'performance_mode',
            'HFT_LOG_LEVEL': 'log_level',
            'HFT_LOG_FILE': 'log_file',
            'HFT_METRICS_FORMAT': 'metrics_export_format',
            'HFT_DATA_DIR': 'data_directory',
            'HFT_TEMP_DIR': 'temp_directory',
            'HFT_CAPTURE_INTERFACE': 'capture_interface',
            'HFT_SSL_ENABLED': 'ssl_enabled',
            'HFT_SSL_CERT': 'ssl_cert_file',
            'HFT_SSL_KEY': 'ssl_key_file',
            'HFT_API_KEY': 'api_key',
            'HFT_WEBHOOK_URL': 'alert_webhook_url'
        }
        
        for env_var, config_key in env_mapping.items():
            value = os.environ.get(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ['ssl_enabled', 'alerts_enabled', 'audit_enabled']:
                    config_data[config_key] = value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ['dashboard_port', 'metrics_export_interval']:
                    config_data[config_key] = int(value)
                else:
                    config_data[config_key] = value
        
        # Parse CPU affinity from environment
        cpu_affinity = os.environ.get('HFT_CPU_AFFINITY')
        if cpu_affinity:
            config_data['cpu_affinity'] = [int(x.strip()) for x in cpu_affinity.split(',')]
        
        return cls(**config_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'performance_mode': self.performance_mode,
            'cpu_affinity': self.cpu_affinity,
            'memory_pool_size': self.memory_pool_size,
            'network_interface': self.network_interface,
            'packet_buffer_size': self.packet_buffer_size,
            'log_level': self.log_level,
            'log_format': self.log_format,
            'log_file': self.log_file,
            'log_rotation': self.log_rotation,
            'log_max_size': self.log_max_size,
            'log_backup_count': self.log_backup_count,
            'metrics_enabled': self.metrics_enabled,
            'metrics_export_format': self.metrics_export_format,
            'metrics_export_interval': self.metrics_export_interval,
            'metrics_retention_days': self.metrics_retention_days,
            'dashboard_enabled': self.dashboard_enabled,
            'dashboard_port': self.dashboard_port,
            'ssl_enabled': self.ssl_enabled,
            'ssl_cert_file': self.ssl_cert_file,
            'ssl_key_file': self.ssl_key_file,
            'ssl_ca_file': self.ssl_ca_file,
            'authentication_enabled': self.authentication_enabled,
            'api_key': self.api_key,
            'alerts_enabled': self.alerts_enabled,
            'alert_webhook_url': self.alert_webhook_url,
            'alert_email_smtp': self.alert_email_smtp,
            'alert_thresholds': self.alert_thresholds,
            'data_directory': self.data_directory,
            'temp_directory': self.temp_directory,
            'backup_enabled': self.backup_enabled,
            'backup_retention_days': self.backup_retention_days,
            'compression_enabled': self.compression_enabled,
            'audit_enabled': self.audit_enabled,
            'audit_retention_days': self.audit_retention_days,
            'compliance_regulations': self.compliance_regulations,
            'regulatory_reporting_enabled': self.regulatory_reporting_enabled,
            'capture_interface': self.capture_interface,
            'capture_filter': self.capture_filter,
            'promiscuous_mode': self.promiscuous_mode,
            'capture_timeout': self.capture_timeout,
            'custom_settings': self.custom_settings
        }
    
    def save_to_file(self, config_path: str, format: str = "yaml") -> None:
        """
        Save configuration to file
        
        Args:
            config_path: Path to save configuration
            format: File format ('yaml' or 'json')
        """
        data = self.to_dict()
        
        with open(config_path, 'w') as f:
            if format.lower() == 'yaml':
                yaml.dump(data, f, default_flow_style=False, indent=2)
            elif format.lower() == 'json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError("Format must be 'yaml' or 'json'")
    
    def get_memory_pool_bytes(self) -> int:
        """Get memory pool size in bytes"""
        return self._parse_memory_size(self.memory_pool_size)
    
    def is_ultra_low_latency(self) -> bool:
        """Check if running in ultra-low latency mode"""
        return self.performance_mode == "ultra_low_latency"
    
    def is_high_performance(self) -> bool:
        """Check if running in high performance mode"""
        return self.performance_mode in ["high_performance", "ultra_low_latency"]
    
    def get_log_file_path(self) -> Optional[str]:
        """Get full path to log file"""
        if self.log_file:
            if os.path.isabs(self.log_file):
                return self.log_file
            else:
                return os.path.join(self.data_directory, "logs", self.log_file)
        return None
    
    def get_metrics_directory(self) -> str:
        """Get metrics storage directory"""
        return os.path.join(self.data_directory, "metrics")
    
    def get_export_directory(self) -> str:
        """Get export directory"""
        return os.path.join(self.data_directory, "exports")
    
    def __str__(self) -> str:
        """String representation"""
        return f"ProductionConfig(mode={self.performance_mode}, log_level={self.log_level})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"ProductionConfig(performance_mode='{self.performance_mode}', "
                f"log_level='{self.log_level}', metrics_enabled={self.metrics_enabled})") 