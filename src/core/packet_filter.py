#!/usr/bin/env python3
"""
AK-Bypass Packet Filter Module

This module provides core packet filtering functionality for network traffic analysis
and security research purposes.

Author: Tanzil github://@tanzil7890
License: Educational/Research Use Only
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum

try:
    from scapy.all import sniff, get_if_list, conf
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.layers.l2 import Ether
except ImportError as e:
    print(f"Error importing Scapy: {e}")
    print("Please ensure Scapy is installed: pip install scapy")
    exit(1)

import psutil
import netifaces


class FilterAction(Enum):
    """Actions that can be taken on filtered packets"""
    ALLOW = "allow"
    BLOCK = "block"
    LOG = "log"
    MODIFY = "modify"


@dataclass
class FilterRule:
    """Represents a packet filtering rule"""
    name: str
    protocol: Optional[str] = None  # tcp, udp, icmp, etc.
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    action: FilterAction = FilterAction.LOG
    priority: int = 100
    enabled: bool = True
    description: str = ""


class PacketFilter:
    """
    Core packet filtering engine for network traffic analysis
    
    This class provides functionality to:
    - Capture network packets
    - Apply filtering rules
    - Log and analyze traffic
    - Implement basic bypass detection
    """
    
    def __init__(self, interface: Optional[str] = None):
        """
        Initialize the packet filter
        
        Args:
            interface: Network interface to monitor (auto-detect if None)
        """
        self.interface = interface or self._get_default_interface()
        self.rules: List[FilterRule] = []
        self.is_running = False
        self.packet_count = 0
        self.captured_packets = []
        self.logger = self._setup_logging()
        self.packet_callbacks: List[Callable] = []
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_packets': 0,
            'allowed_packets': 0,
            'blocked_packets': 0,
            'logged_packets': 0,
            'protocols': {},
            'top_sources': {},
            'top_destinations': {}
        }
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('PacketFilter')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _get_default_interface(self) -> str:
        """Get the default network interface"""
        try:
            # Get all network interfaces
            interfaces = netifaces.interfaces()
            
            # Filter out loopback and inactive interfaces
            active_interfaces = []
            for iface in interfaces:
                if iface.startswith('lo'):  # Skip loopback
                    continue
                
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:  # Has IPv4 address
                    active_interfaces.append(iface)
            
            if active_interfaces:
                # Prefer WiFi (en0) or Ethernet (en1) on macOS
                for preferred in ['en0', 'en1', 'eth0', 'wlan0']:
                    if preferred in active_interfaces:
                        return preferred
                return active_interfaces[0]
            
            return 'en0'  # Default fallback
            
        except Exception as e:
            self.logger.warning(f"Could not detect interface: {e}")
            return 'en0'
    
    def add_rule(self, rule: FilterRule) -> None:
        """Add a filtering rule"""
        with self._lock:
            self.rules.append(rule)
            # Sort rules by priority (lower number = higher priority)
            self.rules.sort(key=lambda r: r.priority)
        
        self.logger.info(f"Added rule: {rule.name}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove a filtering rule by name"""
        with self._lock:
            for i, rule in enumerate(self.rules):
                if rule.name == rule_name:
                    del self.rules[i]
                    self.logger.info(f"Removed rule: {rule_name}")
                    return True
        return False
    
    def get_rules(self) -> List[FilterRule]:
        """Get all filtering rules"""
        with self._lock:
            return self.rules.copy()
    
    def add_packet_callback(self, callback: Callable) -> None:
        """Add a callback function to be called for each packet"""
        self.packet_callbacks.append(callback)
    
    def _match_rule(self, packet, rule: FilterRule) -> bool:
        """Check if a packet matches a filtering rule"""
        if not rule.enabled:
            return False
        
        # Check protocol
        if rule.protocol:
            if rule.protocol.lower() == 'tcp' and not packet.haslayer(TCP):
                return False
            elif rule.protocol.lower() == 'udp' and not packet.haslayer(UDP):
                return False
            elif rule.protocol.lower() == 'icmp' and not packet.haslayer(ICMP):
                return False
        
        # Check IP layer
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            
            # Check source IP
            if rule.src_ip and rule.src_ip != ip_layer.src:
                return False
            
            # Check destination IP
            if rule.dst_ip and rule.dst_ip != ip_layer.dst:
                return False
        
        # Check ports for TCP/UDP
        if packet.haslayer(TCP):
            tcp_layer = packet[TCP]
            if rule.src_port and rule.src_port != tcp_layer.sport:
                return False
            if rule.dst_port and rule.dst_port != tcp_layer.dport:
                return False
        elif packet.haslayer(UDP):
            udp_layer = packet[UDP]
            if rule.src_port and rule.src_port != udp_layer.sport:
                return False
            if rule.dst_port and rule.dst_port != udp_layer.dport:
                return False
        
        return True
    
    def _process_packet(self, packet) -> None:
        """Process a captured packet through the filtering rules"""
        with self._lock:
            self.packet_count += 1
            self.stats['total_packets'] += 1
        
        # Update protocol statistics
        if packet.haslayer(IP):
            protocol = packet[IP].proto
            protocol_name = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}.get(protocol, f'Proto-{protocol}')
            self.stats['protocols'][protocol_name] = self.stats['protocols'].get(protocol_name, 0) + 1
            
            # Update source/destination statistics
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            self.stats['top_sources'][src_ip] = self.stats['top_sources'].get(src_ip, 0) + 1
            self.stats['top_destinations'][dst_ip] = self.stats['top_destinations'].get(dst_ip, 0) + 1
        
        # Apply filtering rules
        action_taken = FilterAction.ALLOW  # Default action
        matched_rule = None
        
        for rule in self.rules:
            if self._match_rule(packet, rule):
                action_taken = rule.action
                matched_rule = rule
                break
        
        # Update statistics
        if action_taken == FilterAction.ALLOW:
            self.stats['allowed_packets'] += 1
        elif action_taken == FilterAction.BLOCK:
            self.stats['blocked_packets'] += 1
        elif action_taken == FilterAction.LOG:
            self.stats['logged_packets'] += 1
        
        # Log the action
        if matched_rule:
            self.logger.info(
                f"Packet {self.packet_count}: {action_taken.value} "
                f"(Rule: {matched_rule.name}) - {self._packet_summary(packet)}"
            )
        
        # Store packet if logging or for analysis
        if action_taken in [FilterAction.LOG, FilterAction.ALLOW]:
            self.captured_packets.append({
                'packet': packet,
                'timestamp': time.time(),
                'action': action_taken,
                'rule': matched_rule.name if matched_rule else None
            })
        
        # Call registered callbacks
        for callback in self.packet_callbacks:
            try:
                callback(packet, action_taken, matched_rule)
            except Exception as e:
                self.logger.error(f"Error in packet callback: {e}")
    
    def _packet_summary(self, packet) -> str:
        """Generate a summary string for a packet"""
        summary = ""
        
        if packet.haslayer(Ether):
            summary += f"Eth: {packet[Ether].src} -> {packet[Ether].dst} "
        
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            summary += f"IP: {ip_layer.src} -> {ip_layer.dst} "
            
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                summary += f"TCP: {tcp_layer.sport} -> {tcp_layer.dport}"
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                summary += f"UDP: {udp_layer.sport} -> {udp_layer.dport}"
            elif packet.haslayer(ICMP):
                summary += "ICMP"
        
        return summary
    
    def start_capture(self, count: int = 0, timeout: Optional[int] = None) -> None:
        """
        Start packet capture
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
        """
        if self.is_running:
            self.logger.warning("Packet capture is already running")
            return
        
        self.is_running = True
        self.logger.info(f"Starting packet capture on interface: {self.interface}")
        
        try:
            # Start packet capture
            sniff(
                iface=self.interface,
                prn=self._process_packet,
                count=count,
                timeout=timeout,
                stop_filter=lambda x: not self.is_running
            )
        except PermissionError:
            self.logger.error(
                "Permission denied. Packet capture requires root/administrator privileges."
            )
        except Exception as e:
            self.logger.error(f"Error during packet capture: {e}")
        finally:
            self.is_running = False
            self.logger.info("Packet capture stopped")
    
    def stop_capture(self) -> None:
        """Stop packet capture"""
        self.is_running = False
        self.logger.info("Stopping packet capture...")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get capture and filtering statistics"""
        with self._lock:
            return {
                'capture_stats': {
                    'total_packets': self.stats['total_packets'],
                    'allowed_packets': self.stats['allowed_packets'],
                    'blocked_packets': self.stats['blocked_packets'],
                    'logged_packets': self.stats['logged_packets']
                },
                'protocol_distribution': dict(list(self.stats['protocols'].items())[:10]),
                'top_sources': dict(list(self.stats['top_sources'].items())[:10]),
                'top_destinations': dict(list(self.stats['top_destinations'].items())[:10]),
                'active_rules': len([r for r in self.rules if r.enabled]),
                'total_rules': len(self.rules)
            }
    
    def clear_statistics(self) -> None:
        """Clear all statistics"""
        with self._lock:
            self.stats = {
                'total_packets': 0,
                'allowed_packets': 0,
                'blocked_packets': 0,
                'logged_packets': 0,
                'protocols': {},
                'top_sources': {},
                'top_destinations': {}
            }
            self.captured_packets.clear()
            self.packet_count = 0
        
        self.logger.info("Statistics cleared")
    
    def export_packets(self, filename: str, format: str = 'pcap') -> None:
        """
        Export captured packets to file
        
        Args:
            filename: Output filename
            format: Export format ('pcap', 'json', 'csv')
        """
        if format == 'pcap':
            from scapy.utils import wrpcap
            packets = [p['packet'] for p in self.captured_packets]
            wrpcap(filename, packets)
            self.logger.info(f"Exported {len(packets)} packets to {filename}")
        else:
            self.logger.error(f"Export format '{format}' not yet implemented")


# Example usage and testing
if __name__ == "__main__":
    # Create packet filter instance
    pf = PacketFilter()
    
    # Add some example rules
    pf.add_rule(FilterRule(
        name="Block SSH",
        protocol="tcp",
        dst_port=22,
        action=FilterAction.BLOCK,
        description="Block SSH traffic"
    ))
    
    pf.add_rule(FilterRule(
        name="Log HTTP",
        protocol="tcp",
        dst_port=80,
        action=FilterAction.LOG,
        description="Log HTTP traffic"
    ))
    
    pf.add_rule(FilterRule(
        name="Log HTTPS",
        protocol="tcp",
        dst_port=443,
        action=FilterAction.LOG,
        description="Log HTTPS traffic"
    ))
    
    print(f"Packet filter initialized on interface: {pf.interface}")
    print(f"Active rules: {len(pf.get_rules())}")
    
    # Start capture for 30 seconds or 100 packets
    try:
        pf.start_capture(count=100, timeout=30)
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")
    
    # Print statistics
    stats = pf.get_statistics()
    print("\nCapture Statistics:")
    for key, value in stats['capture_stats'].items():
        print(f"  {key}: {value}")
    
    print("\nTop Protocols:")
    for proto, count in stats['protocol_distribution'].items():
        print(f"  {proto}: {count}") 