#!/usr/bin/env python3
"""
AK-Bypass and Packet Filtering - Demonstration Script

This script demonstrates the basic functionality of the packet filtering
and parsing system.

Usage:
    python3 demo.py

Note: For actual packet capture, run with sudo:
    sudo python3 demo.py --capture

Author: Tanzil github://@tanzil7890
License: Educational/Research Use Only
"""

import sys
import os
import argparse
import time
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.packet_filter import PacketFilter, FilterRule, FilterAction
    from core.packet_parser import PacketParser
    from scapy.all import Ether, IP, TCP, UDP, ICMP, Raw
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the project root directory")
    print("and that all dependencies are installed.")
    sys.exit(1)


def create_demo_packets():
    """Create some demo packets for testing"""
    packets = []
    
    # HTTP request packet
    http_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                   IP(src="192.168.1.100", dst="93.184.216.34") /
                   TCP(sport=12345, dport=80, flags="PA") /
                   Raw(load=b"GET / HTTP/1.1\r\nHost: example.com\r\n\r\n"))
    packets.append(("HTTP Request", http_packet))
    
    # HTTPS packet
    https_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                    IP(src="192.168.1.100", dst="8.8.8.8") /
                    TCP(sport=54321, dport=443, flags="PA") /
                    Raw(load=b"\x16\x03\x01\x00\x01\x01\x00"))  # TLS handshake
    packets.append(("HTTPS Traffic", https_packet))
    
    # SSH packet
    ssh_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                  IP(src="192.168.1.100", dst="10.0.0.1") /
                  TCP(sport=55555, dport=22, flags="S"))  # SYN packet
    packets.append(("SSH Connection", ssh_packet))
    
    # DNS query packet
    dns_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                  IP(src="192.168.1.100", dst="8.8.8.8") /
                  UDP(sport=53000, dport=53) /
                  Raw(load=b"\x12\x34\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"))
    packets.append(("DNS Query", dns_packet))
    
    # ICMP ping packet
    icmp_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                   IP(src="192.168.1.100", dst="8.8.8.8") /
                   ICMP(type=8, code=0))  # Echo request
    packets.append(("ICMP Ping", icmp_packet))
    
    # Suspicious packet (port scan)
    scan_packet = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                   IP(src="10.0.0.50", dst="192.168.1.100") /
                   TCP(sport=12345, dport=22, flags=""))  # NULL scan
    packets.append(("Port Scan (Suspicious)", scan_packet))
    
    return packets


def demo_packet_filtering():
    """Demonstrate packet filtering functionality"""
    print("=" * 60)
    print("PACKET FILTERING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize packet filter
    pf = PacketFilter()
    print(f"Packet filter initialized on interface: {pf.interface}")
    
    # Add some filtering rules
    rules = [
        FilterRule(
            name="Block SSH",
            protocol="tcp",
            dst_port=22,
            action=FilterAction.BLOCK,
            priority=10,
            description="Block SSH connections"
        ),
        FilterRule(
            name="Log HTTP",
            protocol="tcp",
            dst_port=80,
            action=FilterAction.LOG,
            priority=20,
            description="Log HTTP traffic"
        ),
        FilterRule(
            name="Log HTTPS",
            protocol="tcp",
            dst_port=443,
            action=FilterAction.LOG,
            priority=20,
            description="Log HTTPS traffic"
        ),
        FilterRule(
            name="Allow DNS",
            protocol="udp",
            dst_port=53,
            action=FilterAction.ALLOW,
            priority=30,
            description="Allow DNS queries"
        )
    ]
    
    # Add rules to filter
    for rule in rules:
        pf.add_rule(rule)
    
    print(f"\nAdded {len(rules)} filtering rules:")
    for rule in pf.get_rules():
        print(f"  - {rule.name}: {rule.action.value} {rule.protocol} port {rule.dst_port}")
    
    # Process demo packets
    print("\nProcessing demo packets...")
    demo_packets = create_demo_packets()
    
    for name, packet in demo_packets:
        print(f"\n--- Processing: {name} ---")
        pf._process_packet(packet)
    
    # Show statistics
    print("\n" + "=" * 40)
    print("FILTERING STATISTICS")
    print("=" * 40)
    stats = pf.get_statistics()
    
    print("Packet Counts:")
    for key, value in stats['capture_stats'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nProtocol Distribution:")
    for protocol, count in stats['protocol_distribution'].items():
        print(f"  {protocol}: {count}")
    
    print("\nTop Sources:")
    for src, count in stats['top_sources'].items():
        print(f"  {src}: {count}")
    
    return pf


def demo_packet_parsing():
    """Demonstrate packet parsing functionality"""
    print("\n" + "=" * 60)
    print("PACKET PARSING DEMONSTRATION")
    print("=" * 60)
    
    # Initialize packet parser
    parser = PacketParser()
    print("Packet parser initialized")
    
    # Parse demo packets
    demo_packets = create_demo_packets()
    
    print(f"\nParsing {len(demo_packets)} demo packets...")
    
    for name, packet in demo_packets:
        print(f"\n--- Parsing: {name} ---")
        parsed = parser.parse_packet(packet)
        
        print(f"  Size: {parsed.size} bytes")
        print(f"  Source: {parsed.ip_src}:{parsed.src_port}")
        print(f"  Destination: {parsed.ip_dst}:{parsed.dst_port}")
        print(f"  Protocol: {parsed.ip_protocol}")
        
        if parsed.tcp_flags:
            print(f"  TCP Flags: {parsed.tcp_flags}")
        
        if parsed.is_encrypted:
            print(f"  Encrypted: Yes")
        
        if parsed.suspicious_flags:
            print(f"  Suspicious Flags: {', '.join(parsed.suspicious_flags)}")
        
        if parsed.payload_preview:
            print(f"  Payload Preview: {parsed.payload_preview[:50]}...")
    
    # Generate summary report
    print("\n" + "=" * 40)
    print("PARSING SUMMARY REPORT")
    print("=" * 40)
    
    report = parser.generate_summary_report()
    print(json.dumps(report, indent=2))
    
    return parser


def demo_live_capture():
    """Demonstrate live packet capture (requires sudo)"""
    print("\n" + "=" * 60)
    print("LIVE PACKET CAPTURE DEMONSTRATION")
    print("=" * 60)
    print("Note: This requires sudo privileges for packet capture")
    
    try:
        # Initialize packet filter with parser integration
        pf = PacketFilter()
        parser = PacketParser()
        
        # Add a callback to parse packets
        def parse_callback(packet, action, rule):
            parsed = parser.parse_packet(packet)
            print(f"Captured: {parsed.ip_src}:{parsed.src_port} -> {parsed.ip_dst}:{parsed.dst_port} ({parsed.ip_protocol})")
        
        pf.add_packet_callback(parse_callback)
        
        # Add some basic rules
        pf.add_rule(FilterRule(
            name="Log All Traffic",
            action=FilterAction.LOG,
            priority=100,
            description="Log all network traffic"
        ))
        
        print(f"Starting live capture on {pf.interface} for 10 seconds...")
        print("Press Ctrl+C to stop early")
        
        # Start capture
        pf.start_capture(timeout=10)
        
        # Show results
        stats = pf.get_statistics()
        print(f"\nCaptured {stats['capture_stats']['total_packets']} packets")
        
    except PermissionError:
        print("ERROR: Permission denied. Live capture requires sudo privileges.")
        print("Try running: sudo python3 demo.py --capture")
    except KeyboardInterrupt:
        print("\nCapture interrupted by user")
    except Exception as e:
        print(f"Error during live capture: {e}")


def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description="AK-Bypass Packet Filtering Demo")
    parser.add_argument("--capture", action="store_true", 
                       help="Enable live packet capture (requires sudo)")
    parser.add_argument("--export", type=str, 
                       help="Export demo results to file")
    
    args = parser.parse_args()
    
    print("AK-Bypass and Packet Filtering System")
    print("Educational/Research Use Only")
    print("=" * 60)
    
    # Run demonstrations
    packet_filter = demo_packet_filtering()
    packet_parser = demo_packet_parsing()
    
    # Export results if requested
    if args.export:
        print(f"\nExporting results to {args.export}...")
        try:
            # Export parsed packets
            packet_parser.export_to_json(f"{args.export}_parsed.json")
            
            # Export filter statistics
            stats = packet_filter.get_statistics()
            with open(f"{args.export}_stats.json", 'w') as f:
                json.dump(stats, f, indent=2)
            
            print(f"Results exported to {args.export}_*.json")
        except Exception as e:
            print(f"Error exporting results: {e}")
    
    # Live capture if requested
    if args.capture:
        demo_live_capture()
    else:
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("To test live packet capture, run with sudo:")
        print("  sudo python3 demo.py --capture")
        print("\nTo export results:")
        print("  python3 demo.py --export demo_results")


if __name__ == "__main__":
    main() 