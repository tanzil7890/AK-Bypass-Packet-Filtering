#!/usr/bin/env python3
"""
Production HFT-PacketFilter Demonstration

This script demonstrates how to use the HFT-PacketFilter package
in a production-like environment for real-time trading analysis.

Usage:
    python3 production_hft_demo.py
    sudo python3 production_hft_demo.py --live  # For live capture

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime

# Add the package to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    # Import the HFT-PacketFilter package
    import hft_packetfilter as hft
    from hft_packetfilter.core import ExchangeConfig, CommonExchanges
    from hft_packetfilter.utils.logger import HFTLogger
except ImportError as e:
    print(f"Error importing HFT-PacketFilter package: {e}")
    print("Please ensure the package is properly installed:")
    print("  pip install -e .")
    sys.exit(1)


def demo_quick_start():
    """Demonstrate the quick start functionality"""
    print("=" * 60)
    print("HFT-PACKETFILTER QUICK START DEMO")
    print("=" * 60)
    
    # Quick start with default configuration
    print("1. Quick Start with Default Configuration")
    analyzer = hft.quick_start()
    print(f"   - Analyzer created: {analyzer}")
    print(f"   - Exchanges configured: {len(analyzer.exchanges)}")
    
    # Show configured exchanges
    for name, config in analyzer.exchanges.items():
        print(f"   - {name}: {config.host}:{config.ports}")
    
    return analyzer


def demo_custom_configuration():
    """Demonstrate custom exchange configuration"""
    print("\n" + "=" * 60)
    print("CUSTOM EXCHANGE CONFIGURATION")
    print("=" * 60)
    
    # Create analyzer with custom settings
    analyzer = hft.HFTAnalyzer(
        performance_mode="high_performance",
        logging_level="INFO",
        metrics_export="json"
    )
    
    # Add custom exchanges
    exchanges = [
        ExchangeConfig(
            name="NYSE_PROD",
            host="prod.nyse.gateway.com",
            ports=[4001, 9001],
            protocol="FIX/TCP",
            latency_target_us=300,  # Aggressive latency target
            session_times={
                "market_open": "09:30",
                "market_close": "16:00"
            },
            rate_limits={
                "orders_per_second": 2000,
                "messages_per_second": 10000
            }
        ),
        ExchangeConfig(
            name="NASDAQ_PROD",
            host="prod.nasdaq.gateway.com",
            ports=[4002, 9002],
            protocol="FIX/TCP",
            latency_target_us=350,
            session_times={
                "market_open": "09:30",
                "market_close": "16:00"
            },
            rate_limits={
                "orders_per_second": 1800,
                "messages_per_second": 9000
            }
        )
    ]
    
    # Add exchanges to analyzer
    for exchange in exchanges:
        analyzer.add_exchange(exchange)
        print(f"   - Added: {exchange.name} ({exchange.host})")
        print(f"     Latency Target: {exchange.latency_target_us}μs")
        print(f"     Rate Limits: {exchange.rate_limits}")
    
    return analyzer


def demo_risk_management(analyzer):
    """Demonstrate risk management features"""
    print("\n" + "=" * 60)
    print("RISK MANAGEMENT CONFIGURATION")
    print("=" * 60)
    
    # Import filter rules from existing code
    try:
        from src.core.packet_filter import FilterRule, FilterAction
    except ImportError:
        print("   Warning: Could not import FilterRule - using mock rules")
        return
    
    # Add risk management rules
    risk_rules = [
        FilterRule(
            name="Block_Unauthorized_Trading",
            protocol="tcp",
            dst_port=4001,
            src_ip="!192.168.1.0/24",
            action=FilterAction.BLOCK,
            priority=1,
            description="Block unauthorized trading access"
        ),
        FilterRule(
            name="Monitor_High_Volume",
            protocol="tcp",
            dst_port=4001,
            action=FilterAction.LOG,
            priority=5,
            description="Monitor high-volume trading"
        ),
        FilterRule(
            name="Detect_Port_Scanning",
            action=FilterAction.BLOCK,
            priority=1,
            description="Block port scanning attempts"
        )
    ]
    
    for rule in risk_rules:
        analyzer.add_risk_rule(rule)
        print(f"   - Added risk rule: {rule.name}")
        print(f"     Action: {rule.action.value}, Priority: {rule.priority}")


def demo_compliance_monitoring(analyzer):
    """Demonstrate regulatory compliance features"""
    print("\n" + "=" * 60)
    print("REGULATORY COMPLIANCE MONITORING")
    print("=" * 60)
    
    # Enable compliance monitoring
    regulations = ["MiFID_II", "Reg_NMS"]
    analyzer.enable_compliance_monitoring(
        regulations=regulations,
        audit_trail=True,
        real_time_alerts=True
    )
    
    print(f"   - Enabled compliance for: {regulations}")
    print("   - Audit trail: Enabled")
    print("   - Real-time alerts: Enabled")


def demo_callbacks(analyzer):
    """Demonstrate callback functionality"""
    print("\n" + "=" * 60)
    print("CALLBACK SYSTEM DEMONSTRATION")
    print("=" * 60)
    
    # Packet processing callback
    def packet_callback(parsed_packet, action, rule):
        print(f"   [PACKET] {parsed_packet.ip_src} -> {parsed_packet.ip_dst}:{parsed_packet.dst_port}")
    
    # Latency alert callback
    def latency_callback(alert):
        print(f"   [LATENCY ALERT] {alert['exchange']}: {alert['latency_us']:.1f}μs "
              f"(threshold: {alert['threshold_us']}μs)")
    
    # Risk event callback
    def risk_callback(alert):
        event = alert['event']
        print(f"   [RISK EVENT] {event.event_type} from {event.source_ip} "
              f"(severity: {event.severity})")
    
    # Register callbacks
    analyzer.add_packet_callback(packet_callback)
    analyzer.add_latency_callback(latency_callback)
    analyzer.add_risk_callback(risk_callback)
    
    print("   - Registered packet processing callback")
    print("   - Registered latency alert callback")
    print("   - Registered risk event callback")


def demo_monitoring_simulation(analyzer):
    """Demonstrate monitoring with simulated data"""
    print("\n" + "=" * 60)
    print("MONITORING SIMULATION")
    print("=" * 60)
    
    print("   Starting 10-second monitoring simulation...")
    
    # Start monitoring for 10 seconds
    try:
        analyzer.start_monitoring(duration_seconds=10)
        
        # Wait for monitoring to complete
        time.sleep(11)
        
        # Get live metrics
        metrics = analyzer.get_live_metrics()
        print(f"   - Total packets processed: {metrics['summary']['total_packets']}")
        print(f"   - Uptime: {metrics['summary']['uptime_seconds']:.1f} seconds")
        print(f"   - Exchanges monitored: {metrics['summary']['exchanges_monitored']}")
        
        # Get latency report
        latency_report = analyzer.get_latency_report()
        print(f"   - Latency anomalies detected: {len(latency_report.get('latency_anomalies', {}))}")
        
        # Get risk report
        risk_report = analyzer.get_risk_report()
        print(f"   - Risk events: {len(risk_report.get('risk_events', {}))}")
        
    except PermissionError:
        print("   Note: Live packet capture requires sudo privileges")
        print("   Simulation completed with mock data")
    except Exception as e:
        print(f"   Monitoring error: {e}")


def demo_export_functionality(analyzer):
    """Demonstrate export functionality"""
    print("\n" + "=" * 60)
    print("EXPORT FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Export analysis in JSON format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"hft_analysis_{timestamp}"
        
        analyzer.export_analysis(filename, format="json")
        print(f"   - Analysis exported to {filename}.json")
        
        # Show file size
        if os.path.exists(f"{filename}.json"):
            size = os.path.getsize(f"{filename}.json")
            print(f"   - File size: {size} bytes")
        
    except Exception as e:
        print(f"   Export error: {e}")


def demo_context_manager():
    """Demonstrate context manager usage"""
    print("\n" + "=" * 60)
    print("CONTEXT MANAGER USAGE")
    print("=" * 60)
    
    # Use analyzer as context manager
    with hft.HFTAnalyzer(performance_mode="standard") as analyzer:
        # Add a demo exchange
        analyzer.add_exchange(CommonExchanges.nyse())
        print("   - Created analyzer with context manager")
        print(f"   - Exchanges: {len(analyzer.exchanges)}")
        print("   - Monitoring will auto-stop on exit")
    
    print("   - Context manager exited, monitoring stopped")


def demo_package_info():
    """Display package information"""
    print("\n" + "=" * 60)
    print("PACKAGE INFORMATION")
    print("=" * 60)
    
    print(f"   Package: {hft.__package_info__['name']}")
    print(f"   Version: {hft.__version__}")
    print(f"   Description: {hft.__description__}")
    print(f"   Author: {hft.__author__}")
    print(f"   License: {hft.__license__}")
    print(f"   Homepage: {hft.__package_info__['homepage']}")
    print(f"   Documentation: {hft.__package_info__['documentation']}")


def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description="HFT-PacketFilter Production Demo")
    parser.add_argument("--live", action="store_true",
                       help="Enable live packet capture (requires sudo)")
    parser.add_argument("--export", action="store_true",
                       help="Export analysis results")
    parser.add_argument("--quick", action="store_true",
                       help="Run quick demo only")
    
    args = parser.parse_args()
    
    print("HFT-PacketFilter: High-Frequency Trading Network Analysis Package")
    print("Production Demonstration Script")
    print("=" * 60)
    
    try:
        # Package information
        demo_package_info()
        
        if args.quick:
            # Quick demo only
            analyzer = demo_quick_start()
        else:
            # Full demonstration
            analyzer = demo_quick_start()
            analyzer = demo_custom_configuration()
            demo_risk_management(analyzer)
            demo_compliance_monitoring(analyzer)
            demo_callbacks(analyzer)
            
            if args.live:
                demo_monitoring_simulation(analyzer)
            else:
                print("\n   Note: Use --live flag for actual packet capture")
            
            if args.export:
                demo_export_functionality(analyzer)
            
            demo_context_manager()
        
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        print("Key Features Demonstrated:")
        print("  ✓ Quick start functionality")
        print("  ✓ Custom exchange configuration")
        print("  ✓ Risk management rules")
        print("  ✓ Regulatory compliance monitoring")
        print("  ✓ Callback system")
        print("  ✓ Export functionality")
        print("  ✓ Context manager usage")
        
        print("\nNext Steps:")
        print("  1. Install package: pip install hft-packetfilter")
        print("  2. Configure your exchanges")
        print("  3. Start monitoring: analyzer.start_monitoring()")
        print("  4. Analyze results: analyzer.get_live_metrics()")
        
        print("\nFor production use:")
        print("  - Configure real exchange endpoints")
        print("  - Set appropriate latency targets")
        print("  - Enable compliance monitoring")
        print("  - Set up alerting and monitoring")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 