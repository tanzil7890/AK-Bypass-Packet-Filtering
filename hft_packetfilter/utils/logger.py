#!/usr/bin/env python3
"""
HFT Logger Module

High-performance logging utility for HFT-PacketFilter package.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import logging
import logging.handlers
import sys
import os
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
import threading


class HFTLogger:
    """
    High-performance logger optimized for HFT environments
    
    Features:
    - Ultra-low latency logging
    - Structured logging support
    - Performance mode optimization
    - Thread-safe operations
    - Configurable output formats
    """
    
    def __init__(self, 
                 name: str = "HFTPacketFilter",
                 level: str = "INFO",
                 performance_mode: str = "standard",
                 log_file: Optional[str] = None,
                 format_type: str = "structured"):
        """
        Initialize HFT Logger
        
        Args:
            name: Logger name
            level: Logging level
            performance_mode: Performance optimization mode
            log_file: Optional log file path
            format_type: Log format ('simple', 'structured', 'json')
        """
        self.name = name
        self.level = level.upper()
        self.performance_mode = performance_mode
        self.log_file = log_file
        self.format_type = format_type
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, self.level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Configure logger based on performance mode
        self._configure_logger()
        
        # Performance tracking
        self.log_count = 0
        self.start_time = time.time()
        self._lock = threading.Lock()
    
    def _configure_logger(self):
        """Configure logger based on performance mode"""
        if self.performance_mode == "ultra_low_latency":
            self._configure_ultra_low_latency()
        elif self.performance_mode == "high_performance":
            self._configure_high_performance()
        else:
            self._configure_standard()
    
    def _configure_ultra_low_latency(self):
        """Configure for ultra-low latency logging"""
        # Use memory handler for batching
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            memory_handler = logging.handlers.MemoryHandler(
                capacity=1000,
                target=file_handler,
                flushLevel=logging.ERROR
            )
            self.logger.addHandler(memory_handler)
        
        # Minimal console output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        self.logger.addHandler(console_handler)
        
        # Ultra-fast formatter
        formatter = logging.Formatter('%(asctime)s|%(levelname)s|%(message)s')
        for handler in self.logger.handlers:
            if hasattr(handler, 'target'):
                handler.target.setFormatter(formatter)
            else:
                handler.setFormatter(formatter)
    
    def _configure_high_performance(self):
        """Configure for high performance logging"""
        # Buffered file handler
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file, mode='a', buffering=8192)
            self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(console_handler)
        
        # Optimized formatter
        if self.format_type == "json":
            formatter = JSONFormatter()
        elif self.format_type == "structured":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def _configure_standard(self):
        """Configure for standard logging"""
        # Standard file handler with rotation
        if self.log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                self.log_file,
                maxBytes=100*1024*1024,  # 100MB
                backupCount=5
            )
            self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        self.logger.addHandler(console_handler)
        
        # Full-featured formatter
        if self.format_type == "json":
            formatter = JSONFormatter()
        elif self.format_type == "structured":
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with performance tracking"""
        if self.performance_mode == "ultra_low_latency":
            # Minimal overhead logging
            self.logger.log(level, message)
        else:
            # Enhanced logging with context
            if kwargs:
                if self.format_type == "json":
                    extra = {"context": kwargs}
                    self.logger.log(level, message, extra=extra)
                else:
                    context_str = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
                    self.logger.log(level, f"{message} | {context_str}")
            else:
                self.logger.log(level, message)
        
        # Performance tracking
        with self._lock:
            self.log_count += 1
    
    def log_latency(self, exchange: str, latency_us: float, threshold_us: float):
        """Log latency measurement"""
        if latency_us > threshold_us:
            self.warning(
                "Latency threshold exceeded",
                exchange=exchange,
                latency_us=latency_us,
                threshold_us=threshold_us,
                excess_us=latency_us - threshold_us
            )
        else:
            self.debug(
                "Latency measurement",
                exchange=exchange,
                latency_us=latency_us
            )
    
    def log_packet(self, src_ip: str, dst_ip: str, protocol: str, size: int):
        """Log packet information"""
        self.debug(
            "Packet processed",
            src_ip=src_ip,
            dst_ip=dst_ip,
            protocol=protocol,
            size=size
        )
    
    def log_risk_event(self, event_type: str, severity: str, source_ip: str, description: str):
        """Log risk management event"""
        if severity in ["HIGH", "CRITICAL"]:
            self.error(
                "Risk event detected",
                event_type=event_type,
                severity=severity,
                source_ip=source_ip,
                description=description
            )
        else:
            self.warning(
                "Risk event detected",
                event_type=event_type,
                severity=severity,
                source_ip=source_ip,
                description=description
            )
    
    def log_compliance_event(self, regulation: str, violation_type: str, severity: str):
        """Log compliance event"""
        self.error(
            "Compliance violation",
            regulation=regulation,
            violation_type=violation_type,
            severity=severity
        )
    
    def log_arbitrage_opportunity(self, symbol: str, buy_exchange: str, sell_exchange: str, 
                                 spread_percentage: float, estimated_profit: float):
        """Log arbitrage opportunity"""
        self.info(
            "Arbitrage opportunity detected",
            symbol=symbol,
            buy_exchange=buy_exchange,
            sell_exchange=sell_exchange,
            spread_percentage=spread_percentage,
            estimated_profit=estimated_profit
        )
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics"""
        self.info("Performance metrics", **metrics)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        uptime = time.time() - self.start_time
        return {
            "log_count": self.log_count,
            "uptime_seconds": uptime,
            "logs_per_second": self.log_count / uptime if uptime > 0 else 0,
            "performance_mode": self.performance_mode,
            "level": self.level
        }
    
    def flush(self):
        """Flush all handlers"""
        for handler in self.logger.handlers:
            handler.flush()
    
    def close(self):
        """Close all handlers"""
        for handler in self.logger.handlers:
            handler.close()


class StructuredFormatter(logging.Formatter):
    """Structured log formatter for better parsing"""
    
    def format(self, record):
        """Format log record with structured data"""
        # Base format
        formatted = super().format(record)
        
        # Add structured context if available
        if hasattr(record, 'context'):
            context_str = " | ".join([f"{k}={v}" for k, v in record.context.items()])
            formatted = f"{formatted} | {context_str}"
        
        return formatted


class JSONFormatter(logging.Formatter):
    """JSON log formatter for machine parsing"""
    
    def format(self, record):
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add context if available
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class PerformanceLogger:
    """Ultra-high performance logger for critical paths"""
    
    def __init__(self, buffer_size: int = 10000):
        """
        Initialize performance logger
        
        Args:
            buffer_size: Size of in-memory buffer
        """
        self.buffer_size = buffer_size
        self.buffer = []
        self.buffer_lock = threading.Lock()
        self.dropped_count = 0
    
    def log(self, level: str, message: str, **kwargs):
        """Log message to buffer"""
        timestamp = time.time()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            **kwargs
        }
        
        with self.buffer_lock:
            if len(self.buffer) < self.buffer_size:
                self.buffer.append(entry)
            else:
                self.dropped_count += 1
    
    def flush_to_file(self, filename: str):
        """Flush buffer to file"""
        with self.buffer_lock:
            if self.buffer:
                with open(filename, 'a') as f:
                    for entry in self.buffer:
                        f.write(json.dumps(entry) + '\n')
                self.buffer.clear()
    
    def get_buffer_status(self) -> Dict[str, Any]:
        """Get buffer status"""
        with self.buffer_lock:
            return {
                "buffer_size": len(self.buffer),
                "max_buffer_size": self.buffer_size,
                "dropped_count": self.dropped_count,
                "buffer_full": len(self.buffer) >= self.buffer_size
            }


# Global logger instance
_global_logger: Optional[HFTLogger] = None


def get_logger(name: str = "HFTPacketFilter") -> HFTLogger:
    """Get or create global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = HFTLogger(name)
    return _global_logger


def configure_global_logger(level: str = "INFO", 
                          performance_mode: str = "standard",
                          log_file: Optional[str] = None,
                          format_type: str = "structured"):
    """Configure global logger"""
    global _global_logger
    _global_logger = HFTLogger(
        name="HFTPacketFilter",
        level=level,
        performance_mode=performance_mode,
        log_file=log_file,
        format_type=format_type
    ) 