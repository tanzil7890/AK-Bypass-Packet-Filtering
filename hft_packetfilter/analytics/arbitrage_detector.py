#!/usr/bin/env python3
"""
Arbitrage Detector

Cross-exchange arbitrage opportunity detection for HFT environments.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import statistics
import logging

from ..core.data_structures import ArbitrageOpportunity
from ..core.exceptions import ArbitrageDetectionError
from ..utils.logger import get_logger
from ..utils.metrics_collector import get_metrics_collector


@dataclass
class PriceQuote:
    """Price quote from an exchange"""
    timestamp: float
    exchange: str
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    
    def mid_price(self) -> float:
        """Calculate mid price"""
        return (self.bid_price + self.ask_price) / 2
    
    def spread(self) -> float:
        """Calculate bid-ask spread"""
        return self.ask_price - self.bid_price
    
    def spread_percentage(self) -> float:
        """Calculate spread as percentage of mid price"""
        mid = self.mid_price()
        return (self.spread() / mid) * 100 if mid > 0 else 0


@dataclass
class ArbitrageOpportunityData:
    """Extended arbitrage opportunity with additional data"""
    timestamp: float
    symbol: str
    buy_exchange: str
    sell_exchange: str
    buy_price: float
    sell_price: float
    spread: float
    spread_percentage: float
    volume: float
    estimated_profit: float = 0.0
    execution_time_us: float = 0.0
    confidence: float = 1.0
    expires_at: Optional[float] = None
    
    # Additional analysis
    buy_quote: Optional[PriceQuote] = None
    sell_quote: Optional[PriceQuote] = None
    transaction_costs: float = 0.0
    risk_score: float = 0.0
    
    def __post_init__(self):
        """Calculate derived fields"""
        self.spread = self.sell_price - self.buy_price
        self.spread_percentage = (self.spread / self.buy_price) * 100 if self.buy_price > 0 else 0
        
        # Calculate estimated profit after costs
        gross_profit = self.spread * self.volume
        self.estimated_profit = gross_profit - self.transaction_costs
    
    def is_profitable(self, min_spread_percentage: float = 0.1) -> bool:
        """Check if opportunity is profitable"""
        return (self.spread_percentage >= min_spread_percentage and 
                self.estimated_profit > 0)
    
    def is_expired(self) -> bool:
        """Check if opportunity has expired"""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class CrossExchangeAnalyzer:
    """Cross-exchange price analysis"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.logger = get_logger()
        
        # Price tracking
        self.quotes: Dict[str, PriceQuote] = {}  # exchange -> latest quote
        self.quote_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Statistics
        self.total_quotes_processed = 0
        self.opportunities_detected = 0
        
    def update_quote(self, quote: PriceQuote) -> None:
        """Update price quote for an exchange"""
        if quote.symbol != self.symbol:
            return
        
        self.quotes[quote.exchange] = quote
        self.quote_history[quote.exchange].append(quote)
        self.total_quotes_processed += 1
    
    def find_arbitrage_opportunities(self, 
                                   min_spread_percentage: float = 0.1,
                                   min_volume: float = 100) -> List[ArbitrageOpportunityData]:
        """
        Find arbitrage opportunities across exchanges
        
        Args:
            min_spread_percentage: Minimum spread percentage to consider
            min_volume: Minimum volume for opportunity
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        current_time = time.time()
        
        # Get all exchange pairs
        exchanges = list(self.quotes.keys())
        
        for i, buy_exchange in enumerate(exchanges):
            for sell_exchange in exchanges[i+1:]:
                if buy_exchange == sell_exchange:
                    continue
                
                buy_quote = self.quotes[buy_exchange]
                sell_quote = self.quotes[sell_exchange]
                
                # Check if quotes are recent (within 1 second)
                if (current_time - buy_quote.timestamp > 1.0 or 
                    current_time - sell_quote.timestamp > 1.0):
                    continue
                
                # Check buy low, sell high opportunity
                if sell_quote.bid_price > buy_quote.ask_price:
                    volume = min(buy_quote.ask_size, sell_quote.bid_size, min_volume)
                    if volume >= min_volume:
                        opportunity = ArbitrageOpportunityData(
                            timestamp=current_time,
                            symbol=self.symbol,
                            buy_exchange=buy_exchange,
                            sell_exchange=sell_exchange,
                            buy_price=buy_quote.ask_price,
                            sell_price=sell_quote.bid_price,
                            volume=volume,
                            buy_quote=buy_quote,
                            sell_quote=sell_quote,
                            expires_at=current_time + 5.0  # 5 second expiry
                        )
                        
                        if opportunity.is_profitable(min_spread_percentage):
                            opportunities.append(opportunity)
                
                # Check reverse opportunity
                if buy_quote.bid_price > sell_quote.ask_price:
                    volume = min(sell_quote.ask_size, buy_quote.bid_size, min_volume)
                    if volume >= min_volume:
                        opportunity = ArbitrageOpportunityData(
                            timestamp=current_time,
                            symbol=self.symbol,
                            buy_exchange=sell_exchange,
                            sell_exchange=buy_exchange,
                            buy_price=sell_quote.ask_price,
                            sell_price=buy_quote.bid_price,
                            volume=volume,
                            buy_quote=sell_quote,
                            sell_quote=buy_quote,
                            expires_at=current_time + 5.0
                        )
                        
                        if opportunity.is_profitable(min_spread_percentage):
                            opportunities.append(opportunity)
        
        self.opportunities_detected += len(opportunities)
        return opportunities
    
    def get_price_statistics(self, exchange: str, 
                           time_window: float = 3600) -> Dict[str, Any]:
        """Get price statistics for an exchange"""
        current_time = time.time()
        
        # Get recent quotes
        recent_quotes = [
            q for q in self.quote_history[exchange]
            if current_time - q.timestamp <= time_window
        ]
        
        if not recent_quotes:
            return {}
        
        bid_prices = [q.bid_price for q in recent_quotes]
        ask_prices = [q.ask_price for q in recent_quotes]
        spreads = [q.spread() for q in recent_quotes]
        
        return {
            "exchange": exchange,
            "symbol": self.symbol,
            "quote_count": len(recent_quotes),
            "bid_stats": {
                "min": min(bid_prices),
                "max": max(bid_prices),
                "avg": statistics.mean(bid_prices),
                "median": statistics.median(bid_prices)
            },
            "ask_stats": {
                "min": min(ask_prices),
                "max": max(ask_prices),
                "avg": statistics.mean(ask_prices),
                "median": statistics.median(ask_prices)
            },
            "spread_stats": {
                "min": min(spreads),
                "max": max(spreads),
                "avg": statistics.mean(spreads),
                "median": statistics.median(spreads)
            }
        }


class ArbitrageDetector:
    """
    Arbitrage opportunity detector
    
    Monitors multiple exchanges for arbitrage opportunities in real-time,
    providing alerts and analysis for HFT trading strategies.
    """
    
    def __init__(self,
                 min_spread_percentage: float = 0.1,
                 min_volume: float = 100,
                 min_profit_usd: float = 10.0,
                 monitoring_interval: float = 0.1):
        """
        Initialize arbitrage detector
        
        Args:
            min_spread_percentage: Minimum spread percentage to consider
            min_volume: Minimum volume for opportunities
            min_profit_usd: Minimum profit in USD
            monitoring_interval: Monitoring update interval in seconds
        """
        self.min_spread_percentage = min_spread_percentage
        self.min_volume = min_volume
        self.min_profit_usd = min_profit_usd
        self.monitoring_interval = monitoring_interval
        
        # Components
        self.logger = get_logger()
        self.metrics_collector = get_metrics_collector()
        
        # Symbol analyzers
        self.analyzers: Dict[str, CrossExchangeAnalyzer] = {}
        
        # Opportunity tracking
        self.active_opportunities: List[ArbitrageOpportunityData] = []
        self.opportunity_history: deque = deque(maxlen=10000)
        
        # Exchange configuration
        self.exchange_fees: Dict[str, float] = {}  # exchange -> fee percentage
        self.exchange_latencies: Dict[str, float] = {}  # exchange -> latency in us
        
        # Monitoring
        self.is_monitoring = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Callbacks
        self.opportunity_callbacks: List[Callable] = []
        self.alert_callbacks: List[Callable] = []
        
        # Statistics
        self.start_time = time.time()
        self.total_opportunities_found = 0
        self.total_profit_potential = 0.0
        
    def add_symbol(self, symbol: str) -> None:
        """Add symbol for arbitrage monitoring"""
        if symbol not in self.analyzers:
            self.analyzers[symbol] = CrossExchangeAnalyzer(symbol)
            self.logger.info(f"Added symbol for arbitrage monitoring: {symbol}")
    
    def remove_symbol(self, symbol: str) -> None:
        """Remove symbol from arbitrage monitoring"""
        if symbol in self.analyzers:
            del self.analyzers[symbol]
            self.logger.info(f"Removed symbol from arbitrage monitoring: {symbol}")
    
    def configure_exchange(self, exchange: str, fee_percentage: float, 
                          latency_us: float) -> None:
        """
        Configure exchange parameters
        
        Args:
            exchange: Exchange name
            fee_percentage: Trading fee percentage
            latency_us: Average latency in microseconds
        """
        self.exchange_fees[exchange] = fee_percentage
        self.exchange_latencies[exchange] = latency_us
        
        self.logger.info(f"Configured exchange {exchange}: "
                        f"fee={fee_percentage}%, latency={latency_us}μs")
    
    def update_price_quote(self, quote: PriceQuote) -> None:
        """
        Update price quote from an exchange
        
        Args:
            quote: Price quote object
        """
        # Ensure symbol analyzer exists
        if quote.symbol not in self.analyzers:
            self.add_symbol(quote.symbol)
        
        # Update the analyzer
        analyzer = self.analyzers[quote.symbol]
        analyzer.update_quote(quote)
        
        # Record metrics
        self.metrics_collector.record_gauge(
            f"arbitrage.price.{quote.exchange}.{quote.symbol}",
            quote.mid_price()
        )
        self.metrics_collector.record_gauge(
            f"arbitrage.spread.{quote.exchange}.{quote.symbol}",
            quote.spread_percentage()
        )
    
    def find_opportunities(self) -> List[ArbitrageOpportunityData]:
        """Find all current arbitrage opportunities"""
        all_opportunities = []
        
        for symbol, analyzer in self.analyzers.items():
            opportunities = analyzer.find_arbitrage_opportunities(
                self.min_spread_percentage,
                self.min_volume
            )
            
            # Enhance opportunities with additional analysis
            for opp in opportunities:
                self._enhance_opportunity(opp)
                
                # Filter by minimum profit
                if opp.estimated_profit >= self.min_profit_usd:
                    all_opportunities.append(opp)
        
        # Update active opportunities
        self.active_opportunities = [opp for opp in all_opportunities if not opp.is_expired()]
        
        # Add to history
        for opp in all_opportunities:
            self.opportunity_history.append(opp)
        
        # Update statistics
        self.total_opportunities_found += len(all_opportunities)
        self.total_profit_potential += sum(opp.estimated_profit for opp in all_opportunities)
        
        # Record metrics
        self.metrics_collector.record_gauge(
            "arbitrage.active_opportunities",
            len(self.active_opportunities)
        )
        self.metrics_collector.record_counter(
            "arbitrage.opportunities_found",
            len(all_opportunities)
        )
        
        # Trigger callbacks
        for opp in all_opportunities:
            for callback in self.opportunity_callbacks:
                try:
                    callback(opp)
                except Exception as e:
                    self.logger.error(f"Opportunity callback error: {e}")
            
            # Send alerts for high-value opportunities
            if opp.estimated_profit >= self.min_profit_usd * 5:  # 5x minimum
                self._send_opportunity_alert(opp)
        
        return all_opportunities
    
    def _enhance_opportunity(self, opportunity: ArbitrageOpportunityData) -> None:
        """Enhance opportunity with additional analysis"""
        # Calculate transaction costs
        buy_fee = self.exchange_fees.get(opportunity.buy_exchange, 0.001)  # 0.1% default
        sell_fee = self.exchange_fees.get(opportunity.sell_exchange, 0.001)
        
        buy_cost = opportunity.buy_price * opportunity.volume * (buy_fee / 100)
        sell_cost = opportunity.sell_price * opportunity.volume * (sell_fee / 100)
        opportunity.transaction_costs = buy_cost + sell_cost
        
        # Recalculate profit after costs
        gross_profit = opportunity.spread * opportunity.volume
        opportunity.estimated_profit = gross_profit - opportunity.transaction_costs
        
        # Calculate execution time
        buy_latency = self.exchange_latencies.get(opportunity.buy_exchange, 1000)  # 1ms default
        sell_latency = self.exchange_latencies.get(opportunity.sell_exchange, 1000)
        opportunity.execution_time_us = max(buy_latency, sell_latency)
        
        # Calculate confidence score
        confidence = 1.0
        
        # Reduce confidence for stale quotes
        current_time = time.time()
        if opportunity.buy_quote:
            age = current_time - opportunity.buy_quote.timestamp
            if age > 0.5:  # Older than 500ms
                confidence *= 0.8
        
        if opportunity.sell_quote:
            age = current_time - opportunity.sell_quote.timestamp
            if age > 0.5:
                confidence *= 0.8
        
        # Reduce confidence for small spreads
        if opportunity.spread_percentage < 0.2:  # Less than 0.2%
            confidence *= 0.7
        
        # Reduce confidence for high execution time
        if opportunity.execution_time_us > 5000:  # More than 5ms
            confidence *= 0.6
        
        opportunity.confidence = confidence
        
        # Calculate risk score
        risk_score = 0.0
        
        # Higher risk for larger volumes
        if opportunity.volume > 10000:
            risk_score += 0.3
        
        # Higher risk for volatile symbols (simplified)
        if opportunity.spread_percentage > 1.0:  # Very wide spread
            risk_score += 0.4
        
        # Higher risk for slow execution
        if opportunity.execution_time_us > 2000:  # More than 2ms
            risk_score += 0.3
        
        opportunity.risk_score = min(1.0, risk_score)
    
    def _send_opportunity_alert(self, opportunity: ArbitrageOpportunityData) -> None:
        """Send alert for high-value opportunity"""
        alert_data = {
            "type": "arbitrage_opportunity",
            "severity": "LOW",
            "symbol": opportunity.symbol,
            "buy_exchange": opportunity.buy_exchange,
            "sell_exchange": opportunity.sell_exchange,
            "spread_percentage": opportunity.spread_percentage,
            "estimated_profit": opportunity.estimated_profit,
            "confidence": opportunity.confidence,
            "risk_score": opportunity.risk_score,
            "opportunity": opportunity
        }
        
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                self.logger.error(f"Alert callback error: {e}")
    
    def start_monitoring(self) -> None:
        """Start arbitrage monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self._stop_event.clear()
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info("Started arbitrage monitoring")
    
    def stop_monitoring(self) -> None:
        """Stop arbitrage monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        self._stop_event.set()
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        self.logger.info("Stopped arbitrage monitoring")
    
    def _monitoring_loop(self) -> None:
        """Arbitrage monitoring loop"""
        while not self._stop_event.is_set():
            try:
                self.find_opportunities()
                self._cleanup_expired_opportunities()
                self._stop_event.wait(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in arbitrage monitoring loop: {e}")
                time.sleep(1)
    
    def _cleanup_expired_opportunities(self) -> None:
        """Remove expired opportunities"""
        self.active_opportunities = [
            opp for opp in self.active_opportunities 
            if not opp.is_expired()
        ]
    
    def get_arbitrage_report(self, symbol: Optional[str] = None,
                           time_window: float = 3600) -> Dict[str, Any]:
        """
        Get arbitrage analysis report
        
        Args:
            symbol: Optional symbol filter
            time_window: Time window in seconds
            
        Returns:
            Arbitrage report dictionary
        """
        current_time = time.time()
        
        # Filter recent opportunities
        recent_opportunities = [
            opp for opp in self.opportunity_history
            if current_time - opp.timestamp <= time_window
        ]
        
        if symbol:
            recent_opportunities = [
                opp for opp in recent_opportunities
                if opp.symbol == symbol
            ]
        
        # Calculate statistics
        total_opportunities = len(recent_opportunities)
        total_profit = sum(opp.estimated_profit for opp in recent_opportunities)
        
        # Group by symbol
        symbol_stats = defaultdict(lambda: {
            "count": 0,
            "total_profit": 0.0,
            "avg_spread": 0.0,
            "max_spread": 0.0
        })
        
        for opp in recent_opportunities:
            stats = symbol_stats[opp.symbol]
            stats["count"] += 1
            stats["total_profit"] += opp.estimated_profit
            stats["avg_spread"] += opp.spread_percentage
            stats["max_spread"] = max(stats["max_spread"], opp.spread_percentage)
        
        # Calculate averages
        for symbol_name, stats in symbol_stats.items():
            if stats["count"] > 0:
                stats["avg_spread"] /= stats["count"]
        
        report = {
            "timestamp": current_time,
            "time_window_hours": time_window / 3600,
            "total_opportunities": total_opportunities,
            "active_opportunities": len(self.active_opportunities),
            "total_profit_potential": total_profit,
            "avg_profit_per_opportunity": total_profit / total_opportunities if total_opportunities > 0 else 0,
            "symbol_statistics": dict(symbol_stats),
            "recent_opportunities": [
                {
                    "timestamp": opp.timestamp,
                    "symbol": opp.symbol,
                    "buy_exchange": opp.buy_exchange,
                    "sell_exchange": opp.sell_exchange,
                    "spread_percentage": opp.spread_percentage,
                    "estimated_profit": opp.estimated_profit,
                    "confidence": opp.confidence,
                    "risk_score": opp.risk_score
                }
                for opp in recent_opportunities[-20:]  # Last 20 opportunities
            ]
        }
        
        return report
    
    def add_opportunity_callback(self, callback: Callable) -> None:
        """Add opportunity callback"""
        self.opportunity_callbacks.append(callback)
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add alert callback"""
        self.alert_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return {
            "uptime_seconds": time.time() - self.start_time,
            "symbols_monitored": len(self.analyzers),
            "total_opportunities_found": self.total_opportunities_found,
            "total_profit_potential": self.total_profit_potential,
            "active_opportunities": len(self.active_opportunities),
            "is_monitoring": self.is_monitoring,
            "min_spread_percentage": self.min_spread_percentage,
            "min_volume": self.min_volume,
            "min_profit_usd": self.min_profit_usd
        } 