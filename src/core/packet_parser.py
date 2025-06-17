#!/usr/bin/env python3
"""
AK-Bypass Packet Parser Module

This module provides detailed packet parsing and analysis capabilities
for various network protocols.

Author: Tanzil github://@tanzil7890
License: Educational/Research Use Only
"""

import struct
import socket
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from scapy.all import *
    from scapy.layers.inet import IP, TCP, UDP, ICMP
    from scapy.layers.inet6 import IPv6
    from scapy.layers.l2 import Ether, ARP
    from scapy.layers.dns import DNS, DNSQR, DNSRR
    from scapy.layers.http import HTTP, HTTPRequest, HTTPResponse
except ImportError as e:
    print(f"Error importing Scapy: {e}")
    exit(1)


@dataclass
class ParsedPacket:
    """Represents a parsed network packet with extracted information"""
    timestamp: float
    size: int
    
    # Layer 2 (Data Link)
    eth_src: Optional[str] = None
    eth_dst: Optional[str] = None
    eth_type: Optional[str] = None
    
    # Layer 3 (Network)
    ip_version: Optional[int] = None
    ip_src: Optional[str] = None
    ip_dst: Optional[str] = None
    ip_protocol: Optional[str] = None
    ip_ttl: Optional[int] = None
    ip_flags: Optional[str] = None
    
    # Layer 4 (Transport)
    src_port: Optional[int] = None
    dst_port: Optional[int] = None
    tcp_flags: Optional[str] = None
    tcp_seq: Optional[int] = None
    tcp_ack: Optional[int] = None
    tcp_window: Optional[int] = None
    
    # Application Layer
    payload_size: int = 0
    payload_preview: Optional[str] = None
    
    # Protocol-specific data
    dns_query: Optional[str] = None
    dns_response: Optional[List[str]] = None
    http_method: Optional[str] = None
    http_host: Optional[str] = None
    http_uri: Optional[str] = None
    http_user_agent: Optional[str] = None
    
    # Analysis flags
    is_encrypted: bool = False
    is_fragmented: bool = False
    suspicious_flags: List[str] = None
    
    def __post_init__(self):
        if self.suspicious_flags is None:
            self.suspicious_flags = []


class PacketParser:
    """
    Advanced packet parser for network traffic analysis
    
    This class provides functionality to:
    - Parse packets at multiple layers
    - Extract protocol-specific information
    - Detect suspicious patterns
    - Generate detailed packet reports
    """
    
    def __init__(self):
        """Initialize the packet parser"""
        self.protocol_stats = {}
        self.parsed_packets = []
        
        # Protocol mappings
        self.ip_protocols = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
            41: 'IPv6',
            47: 'GRE',
            50: 'ESP',
            51: 'AH',
            89: 'OSPF'
        }
        
        # Common ports
        self.well_known_ports = {
            20: 'FTP-DATA',
            21: 'FTP',
            22: 'SSH',
            23: 'TELNET',
            25: 'SMTP',
            53: 'DNS',
            67: 'DHCP-SERVER',
            68: 'DHCP-CLIENT',
            69: 'TFTP',
            80: 'HTTP',
            110: 'POP3',
            143: 'IMAP',
            443: 'HTTPS',
            993: 'IMAPS',
            995: 'POP3S'
        }
        
        # Suspicious patterns
        self.suspicious_patterns = {
            'port_scan': [],
            'unusual_ports': [],
            'large_packets': [],
            'fragmented_packets': [],
            'malformed_packets': []
        }
    
    def parse_packet(self, packet) -> ParsedPacket:
        """
        Parse a packet and extract detailed information
        
        Args:
            packet: Scapy packet object
            
        Returns:
            ParsedPacket: Parsed packet information
        """
        parsed = ParsedPacket(
            timestamp=time.time(),
            size=len(packet)
        )
        
        # Parse Layer 2 (Ethernet)
        if packet.haslayer(Ether):
            self._parse_ethernet(packet, parsed)
        
        # Parse Layer 3 (IP)
        if packet.haslayer(IP):
            self._parse_ipv4(packet, parsed)
        elif packet.haslayer(IPv6):
            self._parse_ipv6(packet, parsed)
        
        # Parse Layer 4 (Transport)
        if packet.haslayer(TCP):
            self._parse_tcp(packet, parsed)
        elif packet.haslayer(UDP):
            self._parse_udp(packet, parsed)
        elif packet.haslayer(ICMP):
            self._parse_icmp(packet, parsed)
        
        # Parse Application Layer
        self._parse_application_layer(packet, parsed)
        
        # Analyze for suspicious patterns
        self._analyze_suspicious_patterns(packet, parsed)
        
        # Update statistics
        self._update_statistics(parsed)
        
        # Store parsed packet
        self.parsed_packets.append(parsed)
        
        return parsed
    
    def _parse_ethernet(self, packet, parsed: ParsedPacket) -> None:
        """Parse Ethernet layer information"""
        eth = packet[Ether]
        parsed.eth_src = eth.src
        parsed.eth_dst = eth.dst
        parsed.eth_type = f"0x{eth.type:04x}"
    
    def _parse_ipv4(self, packet, parsed: ParsedPacket) -> None:
        """Parse IPv4 layer information"""
        ip = packet[IP]
        parsed.ip_version = 4
        parsed.ip_src = ip.src
        parsed.ip_dst = ip.dst
        parsed.ip_protocol = self.ip_protocols.get(ip.proto, f"Unknown({ip.proto})")
        parsed.ip_ttl = ip.ttl
        
        # Parse IP flags
        flags = []
        if ip.flags & 0x02:  # Don't Fragment
            flags.append("DF")
        if ip.flags & 0x01:  # More Fragments
            flags.append("MF")
            parsed.is_fragmented = True
        parsed.ip_flags = ",".join(flags) if flags else "None"
    
    def _parse_ipv6(self, packet, parsed: ParsedPacket) -> None:
        """Parse IPv6 layer information"""
        ipv6 = packet[IPv6]
        parsed.ip_version = 6
        parsed.ip_src = ipv6.src
        parsed.ip_dst = ipv6.dst
        parsed.ip_protocol = self.ip_protocols.get(ipv6.nh, f"Unknown({ipv6.nh})")
        parsed.ip_ttl = ipv6.hlim
    
    def _parse_tcp(self, packet, parsed: ParsedPacket) -> None:
        """Parse TCP layer information"""
        tcp = packet[TCP]
        parsed.src_port = tcp.sport
        parsed.dst_port = tcp.dport
        parsed.tcp_seq = tcp.seq
        parsed.tcp_ack = tcp.ack
        parsed.tcp_window = tcp.window
        
        # Parse TCP flags
        flags = []
        if tcp.flags & 0x01:  # FIN
            flags.append("FIN")
        if tcp.flags & 0x02:  # SYN
            flags.append("SYN")
        if tcp.flags & 0x04:  # RST
            flags.append("RST")
        if tcp.flags & 0x08:  # PSH
            flags.append("PSH")
        if tcp.flags & 0x10:  # ACK
            flags.append("ACK")
        if tcp.flags & 0x20:  # URG
            flags.append("URG")
        if tcp.flags & 0x40:  # ECE
            flags.append("ECE")
        if tcp.flags & 0x80:  # CWR
            flags.append("CWR")
        
        parsed.tcp_flags = ",".join(flags) if flags else "None"
        
        # Check for encrypted traffic
        if parsed.dst_port in [443, 993, 995] or parsed.src_port in [443, 993, 995]:
            parsed.is_encrypted = True
    
    def _parse_udp(self, packet, parsed: ParsedPacket) -> None:
        """Parse UDP layer information"""
        udp = packet[UDP]
        parsed.src_port = udp.sport
        parsed.dst_port = udp.dport
    
    def _parse_icmp(self, packet, parsed: ParsedPacket) -> None:
        """Parse ICMP layer information"""
        icmp = packet[ICMP]
        # ICMP doesn't have ports, but we can store type and code
        parsed.src_port = icmp.type
        parsed.dst_port = icmp.code
    
    def _parse_application_layer(self, packet, parsed: ParsedPacket) -> None:
        """Parse application layer protocols"""
        # Parse DNS
        if packet.haslayer(DNS):
            self._parse_dns(packet, parsed)
        
        # Parse HTTP
        if packet.haslayer(HTTPRequest) or packet.haslayer(HTTPResponse):
            self._parse_http(packet, parsed)
        
        # Extract payload information
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            parsed.payload_size = len(payload)
            
            # Create a safe preview of the payload
            try:
                preview = payload[:100].decode('utf-8', errors='replace')
                # Replace non-printable characters
                preview = ''.join(c if c.isprintable() else '.' for c in preview)
                parsed.payload_preview = preview
            except:
                parsed.payload_preview = f"<Binary data: {len(payload)} bytes>"
    
    def _parse_dns(self, packet, parsed: ParsedPacket) -> None:
        """Parse DNS protocol information"""
        dns = packet[DNS]
        
        # DNS Query
        if dns.qr == 0 and packet.haslayer(DNSQR):
            query = packet[DNSQR]
            parsed.dns_query = query.qname.decode('utf-8', errors='replace').rstrip('.')
        
        # DNS Response
        elif dns.qr == 1 and packet.haslayer(DNSRR):
            responses = []
            for i in range(dns.ancount):
                if packet.haslayer(DNSRR):
                    rr = packet[DNSRR]
                    if rr.type == 1:  # A record
                        responses.append(rr.rdata)
                    elif rr.type == 28:  # AAAA record
                        responses.append(rr.rdata)
            parsed.dns_response = responses
    
    def _parse_http(self, packet, parsed: ParsedPacket) -> None:
        """Parse HTTP protocol information"""
        if packet.haslayer(HTTPRequest):
            http = packet[HTTPRequest]
            parsed.http_method = http.Method.decode('utf-8', errors='replace')
            parsed.http_host = http.Host.decode('utf-8', errors='replace') if http.Host else None
            parsed.http_uri = http.Path.decode('utf-8', errors='replace') if http.Path else None
            parsed.http_user_agent = http.User_Agent.decode('utf-8', errors='replace') if http.User_Agent else None
    
    def _analyze_suspicious_patterns(self, packet, parsed: ParsedPacket) -> None:
        """Analyze packet for suspicious patterns"""
        # Large packet size
        if parsed.size > 1500:
            parsed.suspicious_flags.append("LARGE_PACKET")
        
        # Fragmented packets
        if parsed.is_fragmented:
            parsed.suspicious_flags.append("FRAGMENTED")
        
        # Unusual port combinations
        if parsed.src_port and parsed.dst_port:
            if (parsed.src_port > 49152 and parsed.dst_port > 49152):
                parsed.suspicious_flags.append("HIGH_PORTS")
        
        # TCP flags analysis
        if parsed.tcp_flags:
            # SYN flood detection
            if "SYN" in parsed.tcp_flags and "ACK" not in parsed.tcp_flags:
                parsed.suspicious_flags.append("SYN_ONLY")
            
            # NULL scan
            if parsed.tcp_flags == "None":
                parsed.suspicious_flags.append("NULL_SCAN")
            
            # XMAS scan
            if all(flag in parsed.tcp_flags for flag in ["FIN", "PSH", "URG"]):
                parsed.suspicious_flags.append("XMAS_SCAN")
        
        # Port scan detection (simplified)
        if parsed.dst_port and parsed.dst_port in [22, 23, 135, 139, 445, 1433, 3389]:
            parsed.suspicious_flags.append("COMMON_TARGET_PORT")
    
    def _update_statistics(self, parsed: ParsedPacket) -> None:
        """Update protocol statistics"""
        protocol = parsed.ip_protocol or "Unknown"
        self.protocol_stats[protocol] = self.protocol_stats.get(protocol, 0) + 1
    
    def get_protocol_statistics(self) -> Dict[str, int]:
        """Get protocol distribution statistics"""
        return self.protocol_stats.copy()
    
    def get_suspicious_packets(self) -> List[ParsedPacket]:
        """Get packets with suspicious flags"""
        return [p for p in self.parsed_packets if p.suspicious_flags]
    
    def get_packets_by_protocol(self, protocol: str) -> List[ParsedPacket]:
        """Get packets filtered by protocol"""
        return [p for p in self.parsed_packets if p.ip_protocol == protocol]
    
    def get_packets_by_port(self, port: int) -> List[ParsedPacket]:
        """Get packets filtered by port (source or destination)"""
        return [p for p in self.parsed_packets 
                if p.src_port == port or p.dst_port == port]
    
    def get_communication_pairs(self) -> Dict[Tuple[str, str], int]:
        """Get communication pairs (src_ip, dst_ip) and their packet counts"""
        pairs = {}
        for packet in self.parsed_packets:
            if packet.ip_src and packet.ip_dst:
                pair = (packet.ip_src, packet.ip_dst)
                pairs[pair] = pairs.get(pair, 0) + 1
        return pairs
    
    def export_to_json(self, filename: str, include_payload: bool = False) -> None:
        """
        Export parsed packets to JSON format
        
        Args:
            filename: Output filename
            include_payload: Whether to include payload data
        """
        export_data = []
        
        for packet in self.parsed_packets:
            packet_dict = asdict(packet)
            
            # Remove payload if not requested
            if not include_payload:
                packet_dict.pop('payload_preview', None)
            
            # Convert timestamp to readable format
            packet_dict['timestamp_readable'] = datetime.fromtimestamp(
                packet.timestamp
            ).isoformat()
            
            export_data.append(packet_dict)
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Exported {len(export_data)} parsed packets to {filename}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of parsed packets"""
        total_packets = len(self.parsed_packets)
        
        if total_packets == 0:
            return {"error": "No packets parsed"}
        
        # Protocol distribution
        protocol_dist = self.get_protocol_statistics()
        
        # Suspicious packets
        suspicious_packets = self.get_suspicious_packets()
        
        # Top communication pairs
        comm_pairs = self.get_communication_pairs()
        top_pairs = sorted(comm_pairs.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Port analysis
        port_usage = {}
        for packet in self.parsed_packets:
            if packet.dst_port:
                service = self.well_known_ports.get(packet.dst_port, f"Port-{packet.dst_port}")
                port_usage[service] = port_usage.get(service, 0) + 1
        
        top_ports = sorted(port_usage.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Size analysis
        sizes = [p.size for p in self.parsed_packets]
        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)
        min_size = min(sizes)
        
        return {
            "summary": {
                "total_packets": total_packets,
                "suspicious_packets": len(suspicious_packets),
                "unique_protocols": len(protocol_dist),
                "unique_comm_pairs": len(comm_pairs)
            },
            "protocol_distribution": dict(list(protocol_dist.items())[:10]),
            "top_communication_pairs": [
                {"src_dst": f"{pair[0]} -> {pair[1]}", "count": count}
                for pair, count in top_pairs
            ],
            "top_services": [
                {"service": service, "count": count}
                for service, count in top_ports
            ],
            "packet_sizes": {
                "average": round(avg_size, 2),
                "maximum": max_size,
                "minimum": min_size
            },
            "suspicious_patterns": {
                pattern: len([p for p in suspicious_packets if pattern in p.suspicious_flags])
                for pattern in ["LARGE_PACKET", "FRAGMENTED", "SYN_ONLY", "NULL_SCAN", "XMAS_SCAN"]
            }
        }
    
    def clear_data(self) -> None:
        """Clear all parsed packet data"""
        self.parsed_packets.clear()
        self.protocol_stats.clear()
        self.suspicious_patterns = {key: [] for key in self.suspicious_patterns}


# Example usage and testing
if __name__ == "__main__":
    parser = PacketParser()
    
    # Example: Parse a simple packet
    # This would normally be called from the packet filter
    print("Packet Parser initialized")
    print("Ready to parse network packets")
    
    # Example of creating a test packet
    test_packet = Ether()/IP(src="192.168.1.100", dst="8.8.8.8")/TCP(sport=12345, dport=80)
    parsed = parser.parse_packet(test_packet)
    
    print(f"\nParsed test packet:")
    print(f"  Source: {parsed.ip_src}:{parsed.src_port}")
    print(f"  Destination: {parsed.ip_dst}:{parsed.dst_port}")
    print(f"  Protocol: {parsed.ip_protocol}")
    print(f"  Size: {parsed.size} bytes")
    
    # Generate summary report
    report = parser.generate_summary_report()
    print(f"\nSummary Report:")
    print(json.dumps(report, indent=2)) 