#!/usr/bin/env python3
"""
Alert System Module

Real-time alert and notification system for HFT-PacketFilter package.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import time
import json
import threading
import requests
import smtplib
from typing import Dict, List, Any, Optional, Callable
from collections import deque
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    timestamp: float
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "tags": self.tags,
            "metadata": self.metadata,
            "acknowledged": self.acknowledged,
            "resolved": self.resolved,
            "human_timestamp": datetime.fromtimestamp(self.timestamp).isoformat()
        }
    
    def is_critical(self) -> bool:
        """Check if alert is critical"""
        return self.severity in ["CRITICAL", "HIGH"]


class AlertSystem:
    """
    Real-time alert and notification system
    
    Features:
    - Multiple delivery methods (webhook, email, console)
    - Alert throttling and deduplication
    - Severity-based routing
    - Alert acknowledgment and resolution
    - Historical alert tracking
    """
    
    def __init__(self, 
                 webhook_url: Optional[str] = None,
                 email_config: Optional[Dict[str, str]] = None,
                 throttle_interval: int = 300):
        """
        Initialize alert system
        
        Args:
            webhook_url: Webhook URL for alert delivery
            email_config: Email configuration for SMTP delivery
            throttle_interval: Throttle interval in seconds
        """
        self.webhook_url = webhook_url
        self.email_config = email_config or {}
        self.throttle_interval = throttle_interval
        
        # Alert storage
        self.alerts: deque = deque(maxlen=10000)
        self.alert_history: Dict[str, Alert] = {}
        
        # Throttling
        self.last_alert_time: Dict[str, float] = {}
        self.alert_counts: Dict[str, int] = {}
        
        # Callbacks
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Statistics
        self.total_alerts_sent = 0
        self.total_alerts_throttled = 0
        self.start_time = time.time()
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    def add_callback(self, callback: Callable[[Alert], None]):
        """Add alert callback function"""
        with self._lock:
            self.alert_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Alert], None]):
        """Remove alert callback function"""
        with self._lock:
            if callback in self.alert_callbacks:
                self.alert_callbacks.remove(callback)
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """
        Send alert
        
        Args:
            alert_data: Alert data dictionary
            
        Returns:
            True if alert was sent, False if throttled
        """
        # Create alert object
        alert = Alert(
            id=self._generate_alert_id(),
            timestamp=time.time(),
            alert_type=alert_data.get("type", "unknown"),
            severity=alert_data.get("severity", "MEDIUM"),
            title=alert_data.get("title", "Alert"),
            message=alert_data.get("message", ""),
            source=alert_data.get("source", "HFT-PacketFilter"),
            tags=alert_data.get("tags", {}),
            metadata=alert_data.get("metadata", {})
        )
        
        return self._process_alert(alert)
    
    def send_latency_alert(self, exchange: str, latency_us: float, 
                          threshold_us: float) -> bool:
        """Send latency threshold alert"""
        alert_data = {
            "type": "latency_alert",
            "severity": "HIGH" if latency_us > threshold_us * 2 else "MEDIUM",
            "title": f"Latency Threshold Exceeded - {exchange}",
            "message": f"Latency {latency_us:.1f}μs exceeds threshold {threshold_us:.1f}μs",
            "source": "LatencyMonitor",
            "tags": {"exchange": exchange},
            "metadata": {
                "latency_us": latency_us,
                "threshold_us": threshold_us,
                "excess_us": latency_us - threshold_us
            }
        }
        return self.send_alert(alert_data)
    
    def send_risk_alert(self, event_type: str, severity: str, 
                       source_ip: str, description: str) -> bool:
        """Send risk management alert"""
        alert_data = {
            "type": "security_threat",
            "severity": severity,
            "title": f"Security Risk Detected - {event_type}",
            "message": f"Risk event from {source_ip}: {description}",
            "source": "RiskManager",
            "tags": {"source_ip": source_ip, "event_type": event_type},
            "metadata": {
                "event_type": event_type,
                "source_ip": source_ip,
                "description": description
            }
        }
        return self.send_alert(alert_data)
    
    def send_compliance_alert(self, regulation: str, violation_type: str, 
                            severity: str = "HIGH") -> bool:
        """Send compliance violation alert"""
        alert_data = {
            "type": "compliance_violation",
            "severity": severity,
            "title": f"Compliance Violation - {regulation}",
            "message": f"{regulation} violation: {violation_type}",
            "source": "ComplianceMonitor",
            "tags": {"regulation": regulation, "violation_type": violation_type},
            "metadata": {
                "regulation": regulation,
                "violation_type": violation_type
            }
        }
        return self.send_alert(alert_data)
    
    def send_arbitrage_alert(self, symbol: str, buy_exchange: str, 
                           sell_exchange: str, spread_percentage: float,
                           estimated_profit: float) -> bool:
        """Send arbitrage opportunity alert"""
        alert_data = {
            "type": "arbitrage_opportunity",
            "severity": "LOW",
            "title": f"Arbitrage Opportunity - {symbol}",
            "message": f"Buy {symbol} on {buy_exchange}, sell on {sell_exchange} "
                      f"for {spread_percentage:.2f}% spread",
            "source": "ArbitrageDetector",
            "tags": {"symbol": symbol, "buy_exchange": buy_exchange, "sell_exchange": sell_exchange},
            "metadata": {
                "symbol": symbol,
                "buy_exchange": buy_exchange,
                "sell_exchange": sell_exchange,
                "spread_percentage": spread_percentage,
                "estimated_profit": estimated_profit
            }
        }
        return self.send_alert(alert_data)
    
    def send_system_alert(self, component: str, message: str, 
                         severity: str = "MEDIUM") -> bool:
        """Send system alert"""
        alert_data = {
            "type": "system_error",
            "severity": severity,
            "title": f"System Alert - {component}",
            "message": message,
            "source": component,
            "tags": {"component": component},
            "metadata": {"component": component}
        }
        return self.send_alert(alert_data)
    
    def _process_alert(self, alert: Alert) -> bool:
        """Process and deliver alert"""
        with self._lock:
            # Check throttling
            throttle_key = f"{alert.alert_type}:{alert.source}"
            current_time = time.time()
            
            if self._should_throttle(throttle_key, current_time):
                self.total_alerts_throttled += 1
                return False
            
            # Update throttling
            self.last_alert_time[throttle_key] = current_time
            self.alert_counts[throttle_key] = self.alert_counts.get(throttle_key, 0) + 1
            
            # Store alert
            self.alerts.append(alert)
            self.alert_history[alert.id] = alert
            
            # Deliver alert
            self._deliver_alert(alert)
            
            # Call callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Alert callback error: {e}")
            
            self.total_alerts_sent += 1
            return True
    
    def _should_throttle(self, throttle_key: str, current_time: float) -> bool:
        """Check if alert should be throttled"""
        if throttle_key not in self.last_alert_time:
            return False
        
        time_since_last = current_time - self.last_alert_time[throttle_key]
        return time_since_last < self.throttle_interval
    
    def _deliver_alert(self, alert: Alert):
        """Deliver alert via configured methods"""
        # Console delivery (always enabled)
        self._deliver_console(alert)
        
        # Webhook delivery
        if self.webhook_url:
            self._deliver_webhook(alert)
        
        # Email delivery
        if self.email_config:
            self._deliver_email(alert)
    
    def _deliver_console(self, alert: Alert):
        """Deliver alert to console"""
        timestamp = datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        severity_color = {
            "LOW": "\033[92m",      # Green
            "MEDIUM": "\033[93m",   # Yellow
            "HIGH": "\033[91m",     # Red
            "CRITICAL": "\033[95m"  # Magenta
        }.get(alert.severity, "\033[0m")
        
        reset_color = "\033[0m"
        
        print(f"{severity_color}[{alert.severity}] {timestamp} - {alert.title}{reset_color}")
        print(f"  {alert.message}")
        if alert.tags:
            tags_str = " | ".join([f"{k}={v}" for k, v in alert.tags.items()])
            print(f"  Tags: {tags_str}")
        print()
    
    def _deliver_webhook(self, alert: Alert):
        """Deliver alert via webhook"""
        try:
            payload = {
                "alert": alert.to_dict(),
                "timestamp": alert.timestamp,
                "severity": alert.severity,
                "type": alert.alert_type
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code != 200:
                self.logger.warning(f"Webhook delivery failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Webhook delivery error: {e}")
    
    def _deliver_email(self, alert: Alert):
        """Deliver alert via email"""
        try:
            # Only send email for high severity alerts
            if alert.severity not in ["HIGH", "CRITICAL"]:
                return
            
            smtp_server = self.email_config.get("smtp_server")
            smtp_port = self.email_config.get("smtp_port", 587)
            username = self.email_config.get("username")
            password = self.email_config.get("password")
            from_email = self.email_config.get("from_email")
            to_emails = self.email_config.get("to_emails", [])
            
            if not all([smtp_server, username, password, from_email, to_emails]):
                return
            
            # Create message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = f"[{alert.severity}] {alert.title}"
            
            # Email body
            body = f"""
HFT-PacketFilter Alert

Severity: {alert.severity}
Type: {alert.alert_type}
Source: {alert.source}
Time: {datetime.fromtimestamp(alert.timestamp).strftime("%Y-%m-%d %H:%M:%S")}

Message:
{alert.message}

Tags:
{json.dumps(alert.tags, indent=2)}

Metadata:
{json.dumps(alert.metadata, indent=2)}

Alert ID: {alert.id}
            """
            
            msg.attach(MIMEText(body, "plain"))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
                
        except Exception as e:
            self.logger.error(f"Email delivery error: {e}")
    
    def _generate_alert_id(self) -> str:
        """Generate unique alert ID"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        with self._lock:
            if alert_id in self.alert_history:
                self.alert_history[alert_id].acknowledged = True
                return True
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self._lock:
            if alert_id in self.alert_history:
                alert = self.alert_history[alert_id]
                alert.resolved = True
                alert.acknowledged = True
                return True
            return False
    
    def get_recent_alerts(self, alert_type: Optional[str] = None,
                         severity: Optional[str] = None,
                         limit: int = 100) -> List[Alert]:
        """Get recent alerts with optional filtering"""
        with self._lock:
            alerts = list(self.alerts)
            
            # Filter by type
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]
            
            # Filter by severity
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            # Sort by timestamp (newest first) and limit
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            return alerts[:limit]
    
    def get_unresolved_alerts(self) -> List[Alert]:
        """Get all unresolved alerts"""
        with self._lock:
            return [alert for alert in self.alerts if not alert.resolved]
    
    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical alerts"""
        with self._lock:
            return [alert for alert in self.alerts if alert.is_critical()]
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert system statistics"""
        with self._lock:
            uptime = time.time() - self.start_time
            
            # Count by severity
            severity_counts = {}
            for alert in self.alerts:
                severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
            
            # Count by type
            type_counts = {}
            for alert in self.alerts:
                type_counts[alert.alert_type] = type_counts.get(alert.alert_type, 0) + 1
            
            return {
                "uptime_seconds": uptime,
                "total_alerts_sent": self.total_alerts_sent,
                "total_alerts_throttled": self.total_alerts_throttled,
                "alerts_per_hour": (self.total_alerts_sent / uptime) * 3600 if uptime > 0 else 0,
                "current_alerts": len(self.alerts),
                "unresolved_alerts": len(self.get_unresolved_alerts()),
                "critical_alerts": len(self.get_critical_alerts()),
                "severity_distribution": severity_counts,
                "type_distribution": type_counts,
                "throttle_interval": self.throttle_interval,
                "webhook_configured": bool(self.webhook_url),
                "email_configured": bool(self.email_config)
            }
    
    def export_alerts(self, format: str = "json") -> str:
        """Export alerts in specified format"""
        with self._lock:
            alerts_data = [alert.to_dict() for alert in self.alerts]
            
            if format == "json":
                return json.dumps({
                    "export_time": time.time(),
                    "total_alerts": len(alerts_data),
                    "alerts": alerts_data
                }, indent=2)
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Header
                writer.writerow([
                    "id", "timestamp", "alert_type", "severity", "title", 
                    "message", "source", "acknowledged", "resolved"
                ])
                
                # Data
                for alert_dict in alerts_data:
                    writer.writerow([
                        alert_dict["id"],
                        alert_dict["timestamp"],
                        alert_dict["alert_type"],
                        alert_dict["severity"],
                        alert_dict["title"],
                        alert_dict["message"],
                        alert_dict["source"],
                        alert_dict["acknowledged"],
                        alert_dict["resolved"]
                    ])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
    
    def clear_resolved_alerts(self):
        """Clear all resolved alerts"""
        with self._lock:
            # Remove resolved alerts from deque
            self.alerts = deque(
                [alert for alert in self.alerts if not alert.resolved],
                maxlen=self.alerts.maxlen
            )
            
            # Remove from history
            resolved_ids = [
                alert_id for alert_id, alert in self.alert_history.items()
                if alert.resolved
            ]
            for alert_id in resolved_ids:
                del self.alert_history[alert_id]
    
    def configure_webhook(self, webhook_url: str):
        """Configure webhook URL"""
        self.webhook_url = webhook_url
    
    def configure_email(self, email_config: Dict[str, Any]):
        """Configure email settings"""
        self.email_config = email_config
    
    def test_delivery(self) -> Dict[str, bool]:
        """Test alert delivery methods"""
        test_alert = Alert(
            id="test-alert",
            timestamp=time.time(),
            alert_type="test",
            severity="LOW",
            title="Test Alert",
            message="This is a test alert to verify delivery methods",
            source="AlertSystem"
        )
        
        results = {"console": True}  # Console always works
        
        # Test webhook
        if self.webhook_url:
            try:
                self._deliver_webhook(test_alert)
                results["webhook"] = True
            except Exception:
                results["webhook"] = False
        else:
            results["webhook"] = None
        
        # Test email
        if self.email_config:
            try:
                self._deliver_email(test_alert)
                results["email"] = True
            except Exception:
                results["email"] = False
        else:
            results["email"] = None
        
        return results


# Global alert system instance
_global_alert_system: Optional[AlertSystem] = None


def get_alert_system() -> AlertSystem:
    """Get or create global alert system"""
    global _global_alert_system
    if _global_alert_system is None:
        _global_alert_system = AlertSystem()
    return _global_alert_system


def configure_alert_system(webhook_url: Optional[str] = None,
                          email_config: Optional[Dict[str, str]] = None,
                          throttle_interval: int = 300):
    """Configure global alert system"""
    global _global_alert_system
    _global_alert_system = AlertSystem(
        webhook_url=webhook_url,
        email_config=email_config,
        throttle_interval=throttle_interval
    )


# Convenience functions for global alert system
def send_alert(alert_data: Dict[str, Any]) -> bool:
    """Send alert using global alert system"""
    return get_alert_system().send_alert(alert_data)


def send_latency_alert(exchange: str, latency_us: float, threshold_us: float) -> bool:
    """Send latency alert using global alert system"""
    return get_alert_system().send_latency_alert(exchange, latency_us, threshold_us)


def send_risk_alert(event_type: str, severity: str, source_ip: str, description: str) -> bool:
    """Send risk alert using global alert system"""
    return get_alert_system().send_risk_alert(event_type, severity, source_ip, description) 