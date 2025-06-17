#!/usr/bin/env python3
"""
HFT-PacketFilter Analytics Module

Advanced analytics and intelligence for High-Frequency Trading environments.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

# Market data analytics
from .market_data_quality import MarketDataAnalyzer, QualityMetrics, FeedValidator
from .arbitrage_detector import ArbitrageDetector, ArbitrageOpportunityData, CrossExchangeAnalyzer, PriceQuote
# from .execution_analyzer import ExecutionAnalyzer, ExecutionMetrics, SlippageAnalyzer

# Performance analytics - TODO: Implement these modules
# from .latency_analyzer import LatencyAnalyzer, LatencyProfiler, JitterAnalyzer
# from .throughput_analyzer import ThroughputAnalyzer, BandwidthMonitor, PacketFlowAnalyzer

# Risk analytics - TODO: Implement these modules
# from .risk_analyzer import RiskAnalyzer, ThreatDetector, AnomalyDetector
# from .compliance_monitor import ComplianceMonitor, RegulatoryAnalyzer, AuditTrailManager

# Trading analytics - TODO: Implement these modules
# from .order_flow_analyzer import OrderFlowAnalyzer, MarketImpactAnalyzer, LiquidityAnalyzer
# from .portfolio_analyzer import PortfolioAnalyzer, ExposureMonitor, PnLAnalyzer

__all__ = [
    # Market data analytics
    "MarketDataAnalyzer",
    "QualityMetrics",
    "FeedValidator",
    "ArbitrageDetector",
    "ArbitrageOpportunityData", 
    "CrossExchangeAnalyzer",
    "PriceQuote",
    
    # TODO: Add these when modules are implemented
    # "ExecutionAnalyzer",
    # "ExecutionMetrics",
    # "SlippageAnalyzer",
    # "LatencyAnalyzer",
    # "LatencyProfiler",
    # "JitterAnalyzer",
    # "ThroughputAnalyzer",
    # "BandwidthMonitor",
    # "PacketFlowAnalyzer",
    # "RiskAnalyzer",
    # "ThreatDetector",
    # "AnomalyDetector",
    # "ComplianceMonitor",
    # "RegulatoryAnalyzer",
    # "AuditTrailManager",
    # "OrderFlowAnalyzer",
    # "MarketImpactAnalyzer",
    # "LiquidityAnalyzer",
    # "PortfolioAnalyzer",
    # "ExposureMonitor",
    # "PnLAnalyzer",
]
