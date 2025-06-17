#!/usr/bin/env python3
"""
HFT Packet Filtering Demonstration

This script demonstrates how the AK-Bypass packet filtering system
can be used for High-Frequency Trading applications.

Usage:
    python3 hft_demo.py
    sudo python3 hft_demo.py --live  # For live capture

Author: Tanzil github://@tanzil7890
License: Educational/Research Use Only
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from core.packet_filter import PacketFilter, FilterRule, FilterAction
    from core.packet_parser import PacketParser
    from tools.hft_analyzer import HFTNetworkAnalyzer, ExchangeConnection, TradingMetrics
    from scapy.all import Ether, IP, TCP, UDP, Raw
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


def create_hft_demo_packets():
    """Create realistic HFT demo packets"""
    packets = []
    
    # FIX Trading Messages
    fix_order = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                 IP(src="192.168.1.100", dst="198.51.100.10") /  # NYSE
                 TCP(sport=12345, dport=4001, flags="PA") /
                 Raw(load=b"8=FIX.4.2|9=178|35=D|49=SENDER|56=TARGET|34=1|52=20250128-12:30:00|11=ORDER123|21=1|55=AAPL|54=1|60=20250128-12:30:00|38=100|40=2|44=150.50|10=123|"))
    packets.append(("FIX Order Submission", fix_order))
    
    # Market Data Feed
    market_data = (Ether(src="11:22:33:44:55:66", dst="aa:bb:cc:dd:ee:ff") /
                   IP(src="198.51.100.10", dst="192.168.1.100") /  # From NYSE
                   UDP(sport=9001, dport=12346) /
                   Raw(load=b"AAPL,150.52,150.51,1000,500,12:30:01.123456"))
    packets.append(("Market Data Update", market_data))
    
    # High-frequency order
    hf_order = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                IP(src="192.168.1.100", dst="203.0.113.20") /  # NASDAQ
                TCP(sport=12347, dport=4002, flags="PA") /
                Raw(load=b"8=FIX.4.2|9=156|35=D|49=HFT_FIRM|56=NASDAQ|34=12345|52=20250128-12:30:00.001|11=HFT_ORDER_001|21=1|55=MSFT|54=2|60=20250128-12:30:00.001|38=50|40=1|10=098|"))
    packets.append(("High-Frequency Order", hf_order))
    
    # Order cancellation (latency-sensitive)
    cancel_order = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                    IP(src="192.168.1.100", dst="198.51.100.10") /
                    TCP(sport=12348, dport=4001, flags="PA") /
                    Raw(load=b"8=FIX.4.2|9=134|35=F|49=SENDER|56=TARGET|34=2|52=20250128-12:30:00.002|11=ORDER123|41=CANCEL123|55=AAPL|54=1|10=087|"))
    packets.append(("Order Cancellation", cancel_order))
    
    # Arbitrage opportunity detection
    arbitrage_data = (Ether(src="11:22:33:44:55:66", dst="aa:bb:cc:dd:ee:ff") /
                      IP(src="203.0.113.20", dst="192.168.1.100") /  # From NASDAQ
                      UDP(sport=9002, dport=12349) /
                      Raw(load=b"AAPL,150.48,150.47,800,600,12:30:01.125000"))  # Price discrepancy
    packets.append(("Arbitrage Opportunity", arbitrage_data))
    
    # Risk management alert
    risk_alert = (Ether(src="aa:bb:cc:dd:ee:ff", dst="11:22:33:44:55:66") /
                  IP(src="192.168.1.100", dst="10.0.0.1") /  # Risk server
                  TCP(sport=12350, dport=8080, flags="PA") /
                  Raw(load=b"RISK_ALERT: Position limit exceeded for AAPL"))
    packets.append(("Risk Management Alert", risk_alert))
    
    # Suspicious activity (potential attack)
    suspicious_packet = (Ether(src="cc:dd:ee:ff:aa:bb", dst="11:22:33:44:55:66") /
                         IP(src="10.0.0.50", dst="192.168.1.100") /
                         TCP(sport=54321, dport=4001, flags="") /  # NULL scan
                         Raw(load=b""))
    packets.append(("Suspicious Activity", suspicious_packet))
    
    return packets


def demo_hft_latency_analysis():
    """Demonstrate latency analysis for HFT"""
    print("=" * 60)
    print("HFT LATENCY ANALYSIS DEMONSTRATION")
    print("=" * 60)
    
    # Initialize HFT analyzer
    hft_analyzer = HFTNetworkAnalyzer()
    
    # Configure exchange connections
    exchanges = [
        ExchangeConnection(
            name="NYSE",
            ip_address="198.51.100.10",
            ports=[4001, 9001],
            protocol="FIX/TCP",
            latency_target_us=500
        ),
        ExchangeConnection(
            name="NASDAQ", 
            ip_address="203.0.113.20",
            ports=[4002, 9002],
            protocol="FIX/TCP",
            latency_target_us=600
        ),
        ExchangeConnection(
            name="CBOE",
            ip_address="192.0.2.30",
            ports=[4003, 9003], 
            protocol="FIX/TCP",
            latency_target_us=800
        )
    ]
    
    for exchange in exchanges:
        hft_analyzer.add_exchange_connection(exchange)
    
    print(f"Configured {len(exchanges)} exchange connections:")
    for exchange in exchanges:
        print(f"  - {exchange.name}: {exchange.ip_address} (target: {exchange.latency_target_us}μs)")
    
    # Process demo packets
    print("\nProcessing HFT demo packets...")
    demo_packets = create_hft_demo_packets()
    
    for name, packet in demo_packets:
        print(f"\n--- Processing: {name} ---")
        # Simulate packet processing through HFT analyzer
        hft_analyzer._analyze_hft_packet(packet, FilterAction.LOG, None)
    
    # Generate HFT report
    print("\n" + "=" * 40)
    print("HFT ANALYSIS REPORT")
    print("=" * 40)
    
    report = hft_analyzer.generate_hft_report()
    
    print(f"Exchanges Monitored: {report['summary']['exchanges_monitored']}")
    print(f"Packets Analyzed: {report['summary']['total_packets_analyzed']}")
    print(f"Risk Events: {report['summary']['risk_events']}")
    
    return hft_analyzer


def demo_hft_risk_management():
    """Demonstrate risk management capabilities"""
    print("\n" + "=" * 60)
    print("HFT RISK MANAGEMENT DEMONSTRATION")
    print("=" * 60)
    
    # Initialize packet filter with risk rules
    risk_filter = PacketFilter()
    
    # Risk management rules
    risk_rules = [
        FilterRule(
            name="Block_Unauthorized_Trading",
            protocol="tcp",
            dst_port=4001,
            src_ip="!192.168.1.0/24",  # Block external sources
            action=FilterAction.BLOCK,
            priority=1,
            description="Block unauthorized trading attempts"
        ),
        FilterRule(
            name="Monitor_High_Volume_Orders",
            protocol="tcp", 
            dst_port=4001,
            action=FilterAction.LOG,
            priority=10,
            description="Monitor all trading orders"
        ),
        FilterRule(
            name="Alert_Admin_Access",
            protocol="tcp",
            dst_port=22,
            action=FilterAction.LOG,
            priority=5,
            description="Alert on SSH access attempts"
        ),
        FilterRule(
            name="Block_Port_Scanning",
            action=FilterAction.BLOCK,
            priority=1,
            description="Block port scanning attempts"
        )
    ]
    
    # Add risk rules
    for rule in risk_rules:
        risk_filter.add_rule(rule)
    
    print(f"Configured {len(risk_rules)} risk management rules:")
    for rule in risk_filter.get_rules():
        print(f"  - {rule.name}: {rule.action.value} (priority: {rule.priority})")
    
    # Test risk scenarios
    print("\nTesting risk scenarios...")
    
    risk_packets = [
        ("Legitimate Order", create_hft_demo_packets()[0][1]),
        ("Unauthorized Access", create_hft_demo_packets()[-1][1]),  # Suspicious packet
        ("High Volume Order", create_hft_demo_packets()[2][1])      # HF order
    ]
    
    for name, packet in risk_packets:
        print(f"\n--- Testing: {name} ---")
        risk_filter._process_packet(packet)
    
    # Show risk statistics
    stats = risk_filter.get_statistics()
    print(f"\nRisk Management Results:")
    print(f"  Allowed: {stats['capture_stats']['allowed_packets']}")
    print(f"  Blocked: {stats['capture_stats']['blocked_packets']}")
    print(f"  Logged: {stats['capture_stats']['logged_packets']}")
    
    return risk_filter


def demo_market_data_quality():
    """Demonstrate market data quality monitoring"""
    print("\n" + "=" * 60)
    print("MARKET DATA QUALITY MONITORING")
    print("=" * 60)
    
    # Initialize parser for market data analysis
    parser = PacketParser()
    
    # Simulate market data feed with quality issues
    market_data_packets = []
    
    # Normal market data
    for i in range(10):
        timestamp = time.time() + (i * 0.001)  # 1ms intervals
        packet = (Ether() / IP(src="198.51.100.10", dst="192.168.1.100") /
                  UDP(sport=9001, dport=12346) /
                  Raw(load=f"AAPL,150.{50+i},150.{49+i},1000,500,{timestamp}".encode()))
        market_data_packets.append(("Normal Market Data", packet))
    
    # Gap in data (quality issue)
    time.sleep(0.2)  # 200ms gap
    packet = (Ether() / IP(src="198.51.100.10", dst="192.168.1.100") /
              UDP(sport=9001, dport=12346) /
              Raw(load=b"AAPL,150.60,150.59,1000,500,GAP_DETECTED"))
    market_data_packets.append(("Data Gap", packet))
    
    # Large packet (potential batching)
    large_data = b"BATCH_DATA:" + b"AAPL,150.61,150.60,1000,500;" * 50  # Large batch
    packet = (Ether() / IP(src="198.51.100.10", dst="192.168.1.100") /
              UDP(sport=9001, dport=12346) /
              Raw(load=large_data))
    market_data_packets.append(("Large Batch", packet))
    
    print("Analyzing market data quality...")
    
    quality_metrics = {
        'total_packets': 0,
        'large_packets': 0,
        'gaps_detected': 0,
        'average_size': 0,
        'total_size': 0
    }
    
    last_timestamp = 0
    
    for name, packet in market_data_packets:
        parsed = parser.parse_packet(packet)
        quality_metrics['total_packets'] += 1
        quality_metrics['total_size'] += parsed.size
        
        # Check for large packets
        if parsed.size > 1000:
            quality_metrics['large_packets'] += 1
            print(f"  Large packet detected: {parsed.size} bytes")
        
        # Check for gaps
        if last_timestamp > 0:
            gap = parsed.timestamp - last_timestamp
            if gap > 0.1:  # 100ms threshold
                quality_metrics['gaps_detected'] += 1
                print(f"  Data gap detected: {gap:.3f}s")
        
        last_timestamp = parsed.timestamp
    
    quality_metrics['average_size'] = quality_metrics['total_size'] / quality_metrics['total_packets']
    
    print(f"\nMarket Data Quality Report:")
    print(f"  Total Packets: {quality_metrics['total_packets']}")
    print(f"  Average Size: {quality_metrics['average_size']:.1f} bytes")
    print(f"  Large Packets: {quality_metrics['large_packets']}")
    print(f"  Gaps Detected: {quality_metrics['gaps_detected']}")
    
    quality_score = max(0, 100 - (quality_metrics['gaps_detected'] * 10) - (quality_metrics['large_packets'] * 5))
    print(f"  Quality Score: {quality_score}/100")
    
    return quality_metrics


def demo_arbitrage_detection():
    """Demonstrate arbitrage opportunity detection"""
    print("\n" + "=" * 60)
    print("ARBITRAGE OPPORTUNITY DETECTION")
    print("=" * 60)
    
    # Simulate price feeds from different exchanges
    price_feeds = {
        'NYSE': {'AAPL': 150.50, 'MSFT': 300.25},
        'NASDAQ': {'AAPL': 150.48, 'MSFT': 300.27},  # Price discrepancy
        'CBOE': {'AAPL': 150.51, 'MSFT': 300.24}
    }
    
    print("Current market prices:")
    for exchange, prices in price_feeds.items():
        print(f"  {exchange}: AAPL=${prices['AAPL']:.2f}, MSFT=${prices['MSFT']:.2f}")
    
    # Detect arbitrage opportunities
    symbols = ['AAPL', 'MSFT']
    arbitrage_opportunities = []
    
    for symbol in symbols:
        prices = [price_feeds[exchange][symbol] for exchange in price_feeds.keys()]
        min_price = min(prices)
        max_price = max(prices)
        spread = max_price - min_price
        
        if spread > 0.02:  # 2 cent threshold
            min_exchange = [ex for ex, prices in price_feeds.items() if prices[symbol] == min_price][0]
            max_exchange = [ex for ex, prices in price_feeds.items() if prices[symbol] == max_price][0]
            
            opportunity = {
                'symbol': symbol,
                'buy_exchange': min_exchange,
                'sell_exchange': max_exchange,
                'buy_price': min_price,
                'sell_price': max_price,
                'spread': spread,
                'profit_per_share': spread - 0.01  # Minus transaction costs
            }
            arbitrage_opportunities.append(opportunity)
    
    print(f"\nArbitrage Opportunities Detected: {len(arbitrage_opportunities)}")
    for opp in arbitrage_opportunities:
        print(f"  {opp['symbol']}: Buy {opp['buy_exchange']} ${opp['buy_price']:.2f} -> "
              f"Sell {opp['sell_exchange']} ${opp['sell_price']:.2f} "
              f"(Profit: ${opp['profit_per_share']:.2f}/share)")
    
    return arbitrage_opportunities


def demo_live_hft_monitoring():
    """Demonstrate live HFT monitoring (requires sudo)"""
    print("\n" + "=" * 60)
    print("LIVE HFT NETWORK MONITORING")
    print("=" * 60)
    print("Note: This requires sudo privileges for packet capture")
    
    try:
        # Initialize HFT analyzer for live monitoring
        hft_analyzer = HFTNetworkAnalyzer()
        
        # Add real exchange connections (example IPs)
        exchanges = [
            ExchangeConnection("NYSE", "198.51.100.10", [4001, 9001], "FIX/TCP", 500),
            ExchangeConnection("NASDAQ", "203.0.113.20", [4002, 9002], "FIX/TCP", 600)
        ]
        
        for exchange in exchanges:
            hft_analyzer.add_exchange_connection(exchange)
        
        print(f"Starting live monitoring of {len(exchanges)} exchanges...")
        print("Monitoring for 30 seconds...")
        
        # Start live monitoring
        hft_analyzer.start_monitoring(duration_seconds=30)
        
        # Generate report
        report = hft_analyzer.generate_hft_report()
        print(f"\nLive Monitoring Results:")
        print(f"  Packets Captured: {report['summary']['total_packets_analyzed']}")
        print(f"  Risk Events: {report['summary']['risk_events']}")
        
    except PermissionError:
        print("ERROR: Permission denied. Live monitoring requires sudo privileges.")
        print("Try running: sudo python3 hft_demo.py --live")
    except Exception as e:
        print(f"Error during live monitoring: {e}")


def main():
    """Main HFT demonstration function"""
    parser = argparse.ArgumentParser(description="HFT Packet Filtering Demo")
    parser.add_argument("--live", action="store_true",
                       help="Enable live packet capture (requires sudo)")
    parser.add_argument("--export", type=str,
                       help="Export HFT analysis results")
    
    args = parser.parse_args()
    
    print("AK-Bypass Packet Filtering System")
    print("High-Frequency Trading Applications")
    print("Educational/Research Use Only")
    print("=" * 60)
    
    # Run HFT demonstrations
    hft_analyzer = demo_hft_latency_analysis()
    risk_filter = demo_hft_risk_management()
    quality_metrics = demo_market_data_quality()
    arbitrage_opps = demo_arbitrage_detection()
    
    # Export results if requested
    if args.export:
        print(f"\nExporting HFT analysis to {args.export}...")
        try:
            hft_analyzer.export_hft_data(args.export)
            
            # Export additional metrics
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'market_data_quality': quality_metrics,
                'arbitrage_opportunities': arbitrage_opps,
                'risk_statistics': risk_filter.get_statistics()
            }
            
            with open(f"{args.export}_comprehensive.json", 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"Comprehensive analysis exported to {args.export}_comprehensive.json")
            
        except Exception as e:
            print(f"Error exporting results: {e}")
    
    # Live monitoring if requested
    if args.live:
        demo_live_hft_monitoring()
    else:
        print("\n" + "=" * 60)
        print("HFT DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("Key HFT Applications Demonstrated:")
        print("  ✓ Latency measurement and optimization")
        print("  ✓ Risk management and security monitoring")
        print("  ✓ Market data quality analysis")
        print("  ✓ Arbitrage opportunity detection")
        print("\nTo test live HFT monitoring:")
        print("  sudo python3 hft_demo.py --live")
        print("\nTo export comprehensive analysis:")
        print("  python3 hft_demo.py --export hft_analysis")


if __name__ == "__main__":
    main() 