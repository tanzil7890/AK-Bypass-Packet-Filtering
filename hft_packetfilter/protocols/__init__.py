#!/usr/bin/env python3
"""
HFT-PacketFilter Protocols Module

Trading protocol parsers and handlers for High-Frequency Trading environments.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

# FIX Protocol support
from .fix_parser import FIXParser, FIXMessage, FIXSession, FIXValidator
# from .fix_utils import FIXMessageBuilder, FIXFieldExtractor, FIXSequenceManager

# Market data protocols - TODO: Implement these modules
# from .market_data_parser import MarketDataParser, MarketDataMessage, FeedHandler
# from .binary_protocols import BinaryProtocolParser, ExchangeSpecificParser

# WebSocket and REST protocols - TODO: Implement these modules
# from .websocket_handler import WebSocketHandler, WebSocketClient, StreamingDataHandler
# from .rest_handler import RESTHandler, RESTClient, APIConnector

# Protocol utilities - TODO: Implement these modules
# from .protocol_detector import ProtocolDetector, ProtocolIdentifier
# from .message_validator import MessageValidator, ProtocolValidator
# from .session_manager import SessionManager, ConnectionManager

__all__ = [
    # FIX Protocol
    "FIXParser",
    "FIXMessage",
    "FIXSession",
    "FIXValidator",
    
    # TODO: Add these when modules are implemented
    # "FIXMessageBuilder",
    # "FIXFieldExtractor",
    # "FIXSequenceManager",
    # "MarketDataParser",
    # "MarketDataMessage",
    # "FeedHandler",
    # "BinaryProtocolParser",
    # "ExchangeSpecificParser",
    # "WebSocketHandler",
    # "WebSocketClient",
    # "StreamingDataHandler",
    # "RESTHandler",
    # "RESTClient",
    # "APIConnector",
    # "ProtocolDetector",
    # "ProtocolIdentifier",
    # "MessageValidator",
    # "ProtocolValidator",
    # "SessionManager",
    # "ConnectionManager",
]
