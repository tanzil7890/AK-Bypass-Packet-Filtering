#!/usr/bin/env python3
"""
FIX Protocol Parser

Financial Information eXchange (FIX) protocol parser for HFT environments.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import time
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import OrderedDict
import logging

from ..core.exceptions import ProtocolError
from ..utils.logger import get_logger


@dataclass
class FIXMessage:
    """FIX protocol message"""
    msg_type: str
    fields: OrderedDict = field(default_factory=OrderedDict)
    raw_message: str = ""
    timestamp: float = field(default_factory=time.time)
    sequence_number: Optional[int] = None
    
    def get_field(self, tag: int, default: Any = None) -> Any:
        """Get field value by tag"""
        return self.fields.get(str(tag), default)
    
    def set_field(self, tag: int, value: Any) -> None:
        """Set field value by tag"""
        self.fields[str(tag)] = str(value)
    
    def has_field(self, tag: int) -> bool:
        """Check if field exists"""
        return str(tag) in self.fields
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "msg_type": self.msg_type,
            "fields": dict(self.fields),
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "raw_message": self.raw_message
        }


class FIXValidator:
    """FIX message validator"""
    
    # Required fields for different message types
    REQUIRED_FIELDS = {
        "A": [8, 9, 35, 49, 56, 34, 52],  # Logon
        "D": [8, 9, 35, 49, 56, 34, 52, 11, 21, 55, 54, 38, 40],  # New Order Single
        "8": [8, 9, 35, 49, 56, 34, 52, 37, 17, 150, 39],  # Execution Report
        "0": [8, 9, 35, 49, 56, 34, 52],  # Heartbeat
        "1": [8, 9, 35, 49, 56, 34, 52, 112],  # Test Request
        "5": [8, 9, 35, 49, 56, 34, 52],  # Logout
    }
    
    def __init__(self):
        self.logger = get_logger()
    
    def validate_message(self, message: FIXMessage) -> Dict[str, Any]:
        """
        Validate FIX message
        
        Args:
            message: FIX message to validate
            
        Returns:
            Validation result dictionary
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            # Check required fields
            required_fields = self.REQUIRED_FIELDS.get(message.msg_type, [])
            for field_tag in required_fields:
                if not message.has_field(field_tag):
                    result["errors"].append(f"Missing required field: {field_tag}")
                    result["is_valid"] = False
            
            # Validate BeginString (tag 8)
            begin_string = message.get_field(8)
            if begin_string and not begin_string.startswith("FIX"):
                result["errors"].append(f"Invalid BeginString: {begin_string}")
                result["is_valid"] = False
            
            # Validate BodyLength (tag 9)
            body_length = message.get_field(9)
            if body_length:
                try:
                    length = int(body_length)
                    if length <= 0:
                        result["errors"].append("BodyLength must be positive")
                        result["is_valid"] = False
                except ValueError:
                    result["errors"].append("BodyLength must be numeric")
                    result["is_valid"] = False
            
            # Validate MsgType (tag 35)
            msg_type = message.get_field(35)
            if msg_type != message.msg_type:
                result["errors"].append("MsgType field doesn't match message type")
                result["is_valid"] = False
            
            # Validate sequence number (tag 34)
            seq_num = message.get_field(34)
            if seq_num:
                try:
                    seq = int(seq_num)
                    if seq <= 0:
                        result["errors"].append("MsgSeqNum must be positive")
                        result["is_valid"] = False
                    message.sequence_number = seq
                except ValueError:
                    result["errors"].append("MsgSeqNum must be numeric")
                    result["is_valid"] = False
            
            # Validate timestamp format (tag 52)
            sending_time = message.get_field(52)
            if sending_time:
                if not self._validate_timestamp(sending_time):
                    result["warnings"].append("Invalid SendingTime format")
            
            # Message-specific validation
            if message.msg_type == "D":  # New Order Single
                self._validate_new_order(message, result)
            elif message.msg_type == "8":  # Execution Report
                self._validate_execution_report(message, result)
            
        except Exception as e:
            result["errors"].append(f"Validation exception: {str(e)}")
            result["is_valid"] = False
            self.logger.error(f"FIX validation error: {e}")
        
        return result
    
    def _validate_timestamp(self, timestamp: str) -> bool:
        """Validate FIX timestamp format"""
        # FIX timestamp format: YYYYMMDD-HH:MM:SS or YYYYMMDD-HH:MM:SS.sss
        pattern = r'^\d{8}-\d{2}:\d{2}:\d{2}(\.\d{3})?$'
        return bool(re.match(pattern, timestamp))
    
    def _validate_new_order(self, message: FIXMessage, result: Dict[str, Any]) -> None:
        """Validate New Order Single message"""
        # Validate Side (tag 54)
        side = message.get_field(54)
        if side and side not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            result["errors"].append(f"Invalid Side value: {side}")
            result["is_valid"] = False
        
        # Validate OrderQty (tag 38)
        order_qty = message.get_field(38)
        if order_qty:
            try:
                qty = float(order_qty)
                if qty <= 0:
                    result["errors"].append("OrderQty must be positive")
                    result["is_valid"] = False
            except ValueError:
                result["errors"].append("OrderQty must be numeric")
                result["is_valid"] = False
        
        # Validate OrdType (tag 40)
        ord_type = message.get_field(40)
        if ord_type and ord_type not in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            result["errors"].append(f"Invalid OrdType value: {ord_type}")
            result["is_valid"] = False
    
    def _validate_execution_report(self, message: FIXMessage, result: Dict[str, Any]) -> None:
        """Validate Execution Report message"""
        # Validate ExecType (tag 150)
        exec_type = message.get_field(150)
        if exec_type and exec_type not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E", "F", "G", "H", "I"]:
            result["warnings"].append(f"Unknown ExecType value: {exec_type}")
        
        # Validate OrdStatus (tag 39)
        ord_status = message.get_field(39)
        if ord_status and ord_status not in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A", "B", "C", "D", "E"]:
            result["warnings"].append(f"Unknown OrdStatus value: {ord_status}")


class FIXSession:
    """FIX session management"""
    
    def __init__(self, sender_comp_id: str, target_comp_id: str, 
                 begin_string: str = "FIX.4.4"):
        self.sender_comp_id = sender_comp_id
        self.target_comp_id = target_comp_id
        self.begin_string = begin_string
        
        # Session state
        self.is_logged_on = False
        self.outgoing_seq_num = 1
        self.incoming_seq_num = 1
        self.last_heartbeat = time.time()
        self.heartbeat_interval = 30  # seconds
        
        # Message tracking
        self.sent_messages = {}
        self.received_messages = {}
        
        self.logger = get_logger()
    
    def get_next_seq_num(self) -> int:
        """Get next outgoing sequence number"""
        seq_num = self.outgoing_seq_num
        self.outgoing_seq_num += 1
        return seq_num
    
    def validate_incoming_seq_num(self, seq_num: int) -> bool:
        """Validate incoming sequence number"""
        if seq_num == self.incoming_seq_num:
            self.incoming_seq_num += 1
            return True
        elif seq_num < self.incoming_seq_num:
            # Duplicate message
            self.logger.warning(f"Duplicate message received: {seq_num}")
            return False
        else:
            # Gap detected
            self.logger.error(f"Sequence gap detected. Expected: {self.incoming_seq_num}, Received: {seq_num}")
            return False
    
    def needs_heartbeat(self) -> bool:
        """Check if heartbeat is needed"""
        return time.time() - self.last_heartbeat > self.heartbeat_interval
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat time"""
        self.last_heartbeat = time.time()


class FIXParser:
    """
    FIX protocol parser
    
    Parses FIX messages for HFT environments with high performance
    and comprehensive validation.
    """
    
    # FIX field separator
    SOH = '\x01'
    
    # Common FIX message types
    MESSAGE_TYPES = {
        "0": "Heartbeat",
        "1": "Test Request",
        "2": "Resend Request",
        "3": "Reject",
        "4": "Sequence Reset",
        "5": "Logout",
        "6": "IOI",
        "7": "Advertisement",
        "8": "Execution Report",
        "9": "Order Cancel Reject",
        "A": "Logon",
        "B": "News",
        "C": "Email",
        "D": "New Order Single",
        "E": "New Order List",
        "F": "Order Cancel Request",
        "G": "Order Cancel/Replace Request",
        "H": "Order Status Request",
        "V": "Market Data Request",
        "W": "Market Data Snapshot/Full Refresh",
        "X": "Market Data Incremental Refresh",
        "Y": "Market Data Request Reject"
    }
    
    def __init__(self, validate_messages: bool = True):
        """
        Initialize FIX parser
        
        Args:
            validate_messages: Whether to validate parsed messages
        """
        self.validate_messages = validate_messages
        self.validator = FIXValidator() if validate_messages else None
        self.logger = get_logger()
        
        # Statistics
        self.messages_parsed = 0
        self.parse_errors = 0
        self.validation_errors = 0
    
    def parse_message(self, raw_message: str) -> Optional[FIXMessage]:
        """
        Parse FIX message from raw string
        
        Args:
            raw_message: Raw FIX message string
            
        Returns:
            Parsed FIX message or None if parsing failed
        """
        try:
            # Clean the message (remove any trailing characters)
            message = raw_message.strip()
            
            # Split by SOH character
            if self.SOH in message:
                fields_list = message.split(self.SOH)
            else:
                # Try with pipe separator (some systems use this for display)
                fields_list = message.split('|')
            
            # Parse fields
            fields = OrderedDict()
            msg_type = None
            
            for field_str in fields_list:
                if not field_str:
                    continue
                
                if '=' not in field_str:
                    continue
                
                tag, value = field_str.split('=', 1)
                fields[tag] = value
                
                # Extract message type (tag 35)
                if tag == "35":
                    msg_type = value
            
            if not msg_type:
                raise ProtocolError("Missing MsgType field (35)")
            
            # Create FIX message
            fix_message = FIXMessage(
                msg_type=msg_type,
                fields=fields,
                raw_message=raw_message,
                timestamp=time.time()
            )
            
            # Validate if enabled
            if self.validate_messages and self.validator:
                validation_result = self.validator.validate_message(fix_message)
                if not validation_result["is_valid"]:
                    self.validation_errors += 1
                    self.logger.warning(f"FIX validation failed: {validation_result['errors']}")
            
            self.messages_parsed += 1
            return fix_message
            
        except Exception as e:
            self.parse_errors += 1
            self.logger.error(f"FIX parsing error: {e}")
            raise ProtocolError(f"Failed to parse FIX message: {e}")
    
    def parse_multiple_messages(self, data: str) -> List[FIXMessage]:
        """
        Parse multiple FIX messages from data stream
        
        Args:
            data: Raw data containing multiple FIX messages
            
        Returns:
            List of parsed FIX messages
        """
        messages = []
        
        # Split by message boundaries (8=FIX pattern)
        message_pattern = r'(8=FIX[^8]*?)(?=8=FIX|$)'
        message_matches = re.findall(message_pattern, data, re.DOTALL)
        
        for message_data in message_matches:
            try:
                message = self.parse_message(message_data)
                if message:
                    messages.append(message)
            except Exception as e:
                self.logger.error(f"Error parsing message in stream: {e}")
                continue
        
        return messages
    
    def get_message_type_name(self, msg_type: str) -> str:
        """Get human-readable message type name"""
        return self.MESSAGE_TYPES.get(msg_type, f"Unknown ({msg_type})")
    
    def format_message(self, message: FIXMessage, 
                      include_descriptions: bool = False) -> str:
        """
        Format FIX message for display
        
        Args:
            message: FIX message to format
            include_descriptions: Whether to include field descriptions
            
        Returns:
            Formatted message string
        """
        lines = []
        lines.append(f"Message Type: {message.msg_type} ({self.get_message_type_name(message.msg_type)})")
        lines.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message.timestamp))}")
        
        if message.sequence_number:
            lines.append(f"Sequence Number: {message.sequence_number}")
        
        lines.append("Fields:")
        
        for tag, value in message.fields.items():
            if include_descriptions:
                description = self._get_field_description(int(tag))
                lines.append(f"  {tag} ({description}): {value}")
            else:
                lines.append(f"  {tag}: {value}")
        
        return "\n".join(lines)
    
    def _get_field_description(self, tag: int) -> str:
        """Get field description by tag"""
        # Common FIX field descriptions
        descriptions = {
            8: "BeginString",
            9: "BodyLength",
            35: "MsgType",
            49: "SenderCompID",
            56: "TargetCompID",
            34: "MsgSeqNum",
            52: "SendingTime",
            11: "ClOrdID",
            21: "HandlInst",
            55: "Symbol",
            54: "Side",
            38: "OrderQty",
            40: "OrdType",
            44: "Price",
            37: "OrderID",
            17: "ExecID",
            150: "ExecType",
            39: "OrdStatus",
            14: "CumQty",
            151: "LeavesQty",
            6: "AvgPx",
            112: "TestReqID",
            108: "HeartBtInt"
        }
        
        return descriptions.get(tag, f"Tag{tag}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parser statistics"""
        return {
            "messages_parsed": self.messages_parsed,
            "parse_errors": self.parse_errors,
            "validation_errors": self.validation_errors,
            "error_rate": self.parse_errors / max(1, self.messages_parsed),
            "validation_enabled": self.validate_messages
        } 