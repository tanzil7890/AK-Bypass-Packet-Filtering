#!/usr/bin/env python3
"""
Network Packet Capture for HFT-PacketFilter Testing

Captures real network traffic and processes it through the HFT analyzer.
Supports both live capture and PCAP file analysis.
"""

import time
import socket
import struct
import threading
from typing import Dict, List, Optional, Tuple
import argparse
import sys

try:
    import scapy.all as scapy
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("⚠️ Scapy not available. Install with: pip install scapy")

from hft_packetfilter import HFTAnalyzer
from hft_packetfilter.core.exchange_config import CommonExchanges
from hft_packetfilter.core.data_structures import LatencyMeasurement, RiskEvent
from hft_packetfilter.protocols.fix_parser import FIXParser


class NetworkCaptureTest:
    """
    Network packet capture and analysis for HFT testing
    
    Features:
    - Live network packet capture
    - PCAP file analysis
    - FIX protocol detection
    - Latency measurement
    - Traffic pattern analysis
    - Exchange identification
    """
    
    def __init__(self, analyzer: HFTAnalyzer):
        self.analyzer = analyzer
        self.fix_parser = FIXParser()
        self.running = False
        
        # Capture statistics
        self.packets_captured = 0
        self.fix_messages_found = 0
        self.exchanges_detected = set()
        self.start_time = None
        
        # Known exchange ports and IPs (for demo purposes)
        self.exchange_ports = {
            4001: 'NYSE',
            4002: 'NASDAQ', 
            4003: 'CBOE',
            9001: 'NYSE_ALT',
            9002: 'NASDAQ_ALT',
            9003: 'CBOE_ALT',
            443: 'HTTPS_EXCHANGE',
            8080: 'HTTP_EXCHANGE'
        }
        
        # Exchange IP ranges (demo/simulation)
        self.exchange_ips = {
            '192.168.1.': 'NYSE_SIM',
            '192.168.2.': 'NASDAQ_SIM',
            '192.168.3.': 'CBOE_SIM',
            '10.0.1.': 'EXCHANGE_A',
            '10.0.2.': 'EXCHANGE_B'
        }
        
        print("🔍 Network Capture Test initialized")
        print(f"📡 Monitoring ports: {list(self.exchange_ports.keys())}")
    
    def capture_live_traffic(self, interface: str = "any", duration: int = 60, 
                           filter_expr: str = "tcp"):
        """Capture live network traffic"""
        if not SCAPY_AVAILABLE:
            print("❌ Scapy required for live capture. Using simulation mode.")
            self._simulate_network_traffic(duration)
            return
        
        print(f"🚀 Starting live capture on {interface} for {duration}s")
        print(f"🔍 Filter: {filter_expr}")
        
        self.running = True
        self.start_time = time.time()
        
        try:
            # Start packet capture
            scapy.sniff(
                iface=interface if interface != "any" else None,
                filter=filter_expr,
                prn=self._process_packet,
                timeout=duration,
                store=False
            )
            
        except PermissionError:
            print("❌ Permission denied. Try running with sudo:")
            print("   sudo python3 network_capture_test.py --live")
            
        except Exception as e:
            print(f"❌ Capture error: {e}")
            print("💡 Falling back to simulation mode...")
            self._simulate_network_traffic(duration)
        
        finally:
            self.running = False
            self._print_capture_statistics()
    
    def analyze_pcap_file(self, pcap_file: str):
        """Analyze existing PCAP file"""
        if not SCAPY_AVAILABLE:
            print("❌ Scapy required for PCAP analysis")
            return
        
        print(f"📁 Analyzing PCAP file: {pcap_file}")
        
        self.running = True
        self.start_time = time.time()
        
        try:
            packets = scapy.rdpcap(pcap_file)
            print(f"📦 Loaded {len(packets)} packets from {pcap_file}")
            
            for packet in packets:
                if self.running:
                    self._process_packet(packet)
                    
        except FileNotFoundError:
            print(f"❌ PCAP file not found: {pcap_file}")
            
        except Exception as e:
            print(f"❌ PCAP analysis error: {e}")
        
        finally:
            self.running = False
            self._print_capture_statistics()
    
    def _process_packet(self, packet):
        """Process captured network packet"""
        try:
            self.packets_captured += 1
            
            # Extract packet information
            packet_info = self._extract_packet_info(packet)
            if not packet_info:
                return
            
            src_ip, dst_ip, src_port, dst_port, payload = packet_info
            
            # Identify exchange
            exchange = self._identify_exchange(src_ip, dst_ip, src_port, dst_port)
            if exchange:
                self.exchanges_detected.add(exchange)
            
            # Check for FIX protocol
            if payload and self._is_fix_message(payload):
                self._process_fix_message(payload, exchange, src_ip, dst_ip)
            
            # Simulate latency measurement
            if exchange:
                latency = self._calculate_latency(packet)
                measurement = LatencyMeasurement(
                    timestamp=time.time(),
                    exchange_name=exchange,
                    latency_us=latency,
                    packet_size=len(packet) if hasattr(packet, '__len__') else 64
                )
                self.analyzer.process_latency_measurement(measurement)
            
            # Print progress every 1000 packets
            if self.packets_captured % 1000 == 0:
                elapsed = time.time() - self.start_time
                rate = self.packets_captured / elapsed if elapsed > 0 else 0
                print(f"📊 Processed {self.packets_captured:,} packets ({rate:.1f}/sec)")
                
        except Exception as e:
            print(f"❌ Packet processing error: {e}")
    
    def _extract_packet_info(self, packet) -> Optional[Tuple]:
        """Extract IP and port information from packet"""
        try:
            if SCAPY_AVAILABLE and hasattr(packet, 'haslayer'):
                # Scapy packet
                if packet.haslayer(scapy.IP) and packet.haslayer(scapy.TCP):
                    ip_layer = packet[scapy.IP]
                    tcp_layer = packet[scapy.TCP]
                    
                    payload = bytes(tcp_layer.payload) if tcp_layer.payload else b''
                    
                    return (
                        ip_layer.src,
                        ip_layer.dst, 
                        tcp_layer.sport,
                        tcp_layer.dport,
                        payload
                    )
            else:
                # Raw packet processing (simplified)
                return self._parse_raw_packet(packet)
                
        except Exception as e:
            print(f"❌ Packet extraction error: {e}")
            
        return None
    
    def _parse_raw_packet(self, packet_data) -> Optional[Tuple]:
        """Parse raw packet data (simplified implementation)"""
        try:
            # This is a simplified parser - in production you'd use proper libraries
            if len(packet_data) < 40:  # Minimum IP + TCP header size
                return None
            
            # Extract IP header (simplified)
            ip_header = packet_data[14:34]  # Skip Ethernet header
            src_ip = socket.inet_ntoa(ip_header[12:16])
            dst_ip = socket.inet_ntoa(ip_header[16:20])
            
            # Extract TCP header (simplified)
            tcp_header = packet_data[34:54]
            src_port = struct.unpack('!H', tcp_header[0:2])[0]
            dst_port = struct.unpack('!H', tcp_header[2:4])[0]
            
            # Extract payload
            payload = packet_data[54:]
            
            return (src_ip, dst_ip, src_port, dst_port, payload)
            
        except Exception as e:
            print(f"❌ Raw packet parsing error: {e}")
            return None
    
    def _identify_exchange(self, src_ip: str, dst_ip: str, 
                          src_port: int, dst_port: int) -> Optional[str]:
        """Identify exchange based on IP and port"""
        # Check known exchange ports
        for port in [src_port, dst_port]:
            if port in self.exchange_ports:
                return self.exchange_ports[port]
        
        # Check known exchange IP ranges
        for ip in [src_ip, dst_ip]:
            for ip_prefix, exchange in self.exchange_ips.items():
                if ip.startswith(ip_prefix):
                    return exchange
        
        # Check for common trading ports
        trading_ports = [443, 8080, 8443, 9000, 9001, 9002, 9003]
        for port in [src_port, dst_port]:
            if port in trading_ports:
                return f"EXCHANGE_PORT_{port}"
        
        return None
    
    def _is_fix_message(self, payload: bytes) -> bool:
        """Check if payload contains FIX protocol message"""
        try:
            if len(payload) < 10:
                return False
            
            # Look for FIX protocol markers
            payload_str = payload.decode('ascii', errors='ignore')
            
            # Check for FIX version strings
            fix_markers = ['8=FIX', '8=FIXT', 'FIX.4.', 'FIXT.1.']
            for marker in fix_markers:
                if marker in payload_str:
                    return True
            
            # Check for SOH (Start of Header) character
            if b'\x01' in payload:
                return True
                
        except Exception:
            pass
        
        return False
    
    def _process_fix_message(self, payload: bytes, exchange: str, 
                           src_ip: str, dst_ip: str):
        """Process detected FIX message"""
        try:
            self.fix_messages_found += 1
            
            # Try to parse FIX message
            payload_str = payload.decode('ascii', errors='ignore')
            fix_message = self.fix_parser.parse_message(payload_str)
            
            if fix_message:
                print(f"📨 FIX Message from {exchange or 'Unknown'}")
                print(f"   Type: {fix_message.msg_type}")
                print(f"   Fields: {len(fix_message.fields)}")
                print(f"   Source: {src_ip} → {dst_ip}")
                
                # Check for specific message types
                if fix_message.msg_type == 'D':  # New Order Single
                    print("   🔥 Order detected!")
                elif fix_message.msg_type == '8':  # Execution Report
                    print("   ✅ Execution detected!")
                elif fix_message.msg_type == 'W':  # Market Data Snapshot
                    print("   📊 Market data detected!")
                    
        except Exception as e:
            print(f"❌ FIX processing error: {e}")
    
    def _calculate_latency(self, packet) -> float:
        """Calculate or estimate packet latency"""
        try:
            # In real implementation, you'd use packet timestamps
            # For simulation, we'll generate realistic latency
            base_latency = 500  # microseconds
            jitter = 1.0 + (hash(str(packet)) % 100) / 500  # Deterministic jitter
            return base_latency * jitter
            
        except Exception:
            return 500.0  # Default latency
    
    def _simulate_network_traffic(self, duration: int):
        """Simulate network traffic when live capture isn't available"""
        print("🎭 Simulating network traffic...")
        
        self.running = True
        self.start_time = time.time()
        
        # Simulate different types of traffic
        exchanges = ['NYSE', 'NASDAQ', 'CBOE']
        message_types = ['D', '8', 'W', 'A', '5']  # Various FIX message types
        
        end_time = time.time() + duration
        
        while self.running and time.time() < end_time:
            try:
                # Simulate packet
                exchange = exchanges[self.packets_captured % len(exchanges)]
                self.exchanges_detected.add(exchange)
                
                # Simulate FIX message occasionally
                if self.packets_captured % 10 == 0:
                    self.fix_messages_found += 1
                    msg_type = message_types[self.packets_captured % len(message_types)]
                    print(f"📨 Simulated FIX {msg_type} from {exchange}")
                
                # Simulate latency measurement
                latency = 400 + (self.packets_captured % 200)  # 400-600 μs
                measurement = LatencyMeasurement(
                    timestamp=time.time(),
                    exchange_name=exchange,
                    latency_us=latency,
                    packet_size=64 + (self.packets_captured % 1400)
                )
                self.analyzer.process_latency_measurement(measurement)
                
                self.packets_captured += 1
                
                # Print progress
                if self.packets_captured % 500 == 0:
                    elapsed = time.time() - self.start_time
                    rate = self.packets_captured / elapsed if elapsed > 0 else 0
                    print(f"📊 Simulated {self.packets_captured:,} packets ({rate:.1f}/sec)")
                
                # Simulate realistic packet timing
                time.sleep(0.001)  # 1ms between packets
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Simulation error: {e}")
                break
        
        self.running = False
        self._print_capture_statistics()
    
    def _print_capture_statistics(self):
        """Print capture session statistics"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        avg_rate = self.packets_captured / elapsed if elapsed > 0 else 0
        
        print(f"\n📈 Capture Session Results")
        print(f"=" * 50)
        print(f"Duration: {elapsed:.1f} seconds")
        print(f"Packets Captured: {self.packets_captured:,}")
        print(f"Average Rate: {avg_rate:.1f} packets/second")
        print(f"FIX Messages: {self.fix_messages_found:,}")
        print(f"Exchanges Detected: {', '.join(sorted(self.exchanges_detected))}")
        
        if self.fix_messages_found > 0:
            fix_percentage = (self.fix_messages_found / self.packets_captured) * 100
            print(f"FIX Traffic: {fix_percentage:.2f}% of total packets")


def main():
    """Main function for network capture testing"""
    parser = argparse.ArgumentParser(description="HFT Network Capture Test")
    parser.add_argument('--live', action='store_true', 
                       help='Capture live network traffic')
    parser.add_argument('--pcap', type=str, 
                       help='Analyze PCAP file')
    parser.add_argument('--interface', type=str, default='any',
                       help='Network interface for live capture')
    parser.add_argument('--duration', type=int, default=60,
                       help='Capture duration in seconds')
    parser.add_argument('--filter', type=str, default='tcp',
                       help='Packet filter expression')
    
    args = parser.parse_args()
    
    print("🔍 HFT-PacketFilter Network Capture Test")
    print("=" * 60)
    
    # Initialize HFT Analyzer
    analyzer = HFTAnalyzer(performance_mode='ultra_low_latency')
    
    # Add exchange configurations
    exchanges = [
        CommonExchanges.nyse(),
        CommonExchanges.nasdaq(), 
        CommonExchanges.cboe()
    ]
    
    for exchange in exchanges:
        analyzer.add_exchange(exchange)
        print(f"✅ Added exchange: {exchange.name}")
    
    # Create capture test
    capture_test = NetworkCaptureTest(analyzer)
    
    try:
        if args.pcap:
            # Analyze PCAP file
            capture_test.analyze_pcap_file(args.pcap)
            
        elif args.live:
            # Live capture
            capture_test.capture_live_traffic(
                interface=args.interface,
                duration=args.duration,
                filter_expr=args.filter
            )
            
        else:
            # Default: simulation mode
            print("💡 No capture mode specified. Running simulation...")
            print("   Use --live for live capture or --pcap <file> for file analysis")
            capture_test._simulate_network_traffic(args.duration)
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Capture interrupted by user")
        
    except Exception as e:
        print(f"❌ Capture error: {e}")
    
    print(f"\n✅ Network capture test completed!")


if __name__ == "__main__":
    main() 