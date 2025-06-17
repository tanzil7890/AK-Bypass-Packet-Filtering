# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: profile=False
# cython: linetrace=False

"""
Ultra-Fast Packet Parser

Cython-optimized packet parsing for HFT applications.
Achieves microsecond-level parsing performance.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import cython
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.string cimport memcpy, memset
from libc.stdlib cimport malloc, free
import numpy as np
cimport numpy as cnp

# Fast packet header structures
cdef packed struct ethernet_header:
    uint8_t dest_mac[6]
    uint8_t src_mac[6]
    uint16_t ethertype

cdef packed struct ipv4_header:
    uint8_t version_ihl
    uint8_t tos
    uint16_t total_length
    uint16_t identification
    uint16_t flags_fragment
    uint8_t ttl
    uint8_t protocol
    uint16_t checksum
    uint32_t src_ip
    uint32_t dest_ip

cdef packed struct tcp_header:
    uint16_t src_port
    uint16_t dest_port
    uint32_t seq_num
    uint32_t ack_num
    uint8_t data_offset_flags
    uint8_t flags
    uint16_t window_size
    uint16_t checksum
    uint16_t urgent_pointer

cdef packed struct udp_header:
    uint16_t src_port
    uint16_t dest_port
    uint16_t length
    uint16_t checksum

# Exchange-specific constants
cdef uint16_t NYSE_PORTS[4]
cdef uint16_t NASDAQ_PORTS[4] 
cdef uint16_t CBOE_PORTS[4]

NYSE_PORTS[:] = [4001, 9001, 8001, 7001]
NASDAQ_PORTS[:] = [4002, 9002, 8002, 7002]
CBOE_PORTS[:] = [4003, 9003, 8003, 7003]

cdef class FastPacketParser:
    """Ultra-fast packet parser optimized for HFT trading protocols."""
    
    cdef:
        uint64_t packets_parsed
        uint64_t bytes_processed
        uint64_t parse_time_ns
        bint initialized
        
    def __cinit__(self):
        self.packets_parsed = 0
        self.bytes_processed = 0
        self.parse_time_ns = 0
        self.initialized = True
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline uint16_t _ntohs(self, uint16_t value) nogil:
        """Fast network to host byte order conversion."""
        return ((value & 0xFF) << 8) | ((value >> 8) & 0xFF)
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline uint32_t _ntohl(self, uint32_t value) nogil:
        """Fast network to host byte order conversion."""
        return ((value & 0xFF) << 24) | (((value >> 8) & 0xFF) << 16) | \
               (((value >> 16) & 0xFF) << 8) | ((value >> 24) & 0xFF)
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline bint _is_exchange_port(self, uint16_t port) nogil:
        """Fast exchange port identification."""
        cdef int i
        
        # Check NYSE ports
        for i in range(4):
            if port == NYSE_PORTS[i]:
                return True
                
        # Check NASDAQ ports  
        for i in range(4):
            if port == NASDAQ_PORTS[i]:
                return True
                
        # Check CBOE ports
        for i in range(4):
            if port == CBOE_PORTS[i]:
                return True
                
        return False
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline int _get_exchange_id(self, uint16_t port) nogil:
        """Fast exchange identification. Returns: 1=NYSE, 2=NASDAQ, 3=CBOE, 0=Unknown."""
        cdef int i
        
        # Check NYSE ports (ID = 1)
        for i in range(4):
            if port == NYSE_PORTS[i]:
                return 1
                
        # Check NASDAQ ports (ID = 2)
        for i in range(4):
            if port == NASDAQ_PORTS[i]:
                return 2
                
        # Check CBOE ports (ID = 3)
        for i in range(4):
            if port == CBOE_PORTS[i]:
                return 3
                
        return 0
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline bint _is_fix_protocol(self, const uint8_t* payload, int payload_len) nogil:
        """Fast FIX protocol detection."""
        if payload_len < 8:
            return False
            
        # Check for FIX protocol header: "8=FIX"
        return (payload[0] == 56 and  # '8'
                payload[1] == 61 and  # '='
                payload[2] == 70 and  # 'F'
                payload[3] == 73 and  # 'I'
                payload[4] == 88)      # 'X'
    
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def parse_packet_fast(self, const uint8_t[::1] packet_data not None):
        """
        Ultra-fast packet parsing optimized for HFT protocols.
        
        Returns:
            dict: Parsed packet information with trading-relevant fields
        """
        cdef:
            int packet_len = len(packet_data)
            const uint8_t* data = &packet_data[0]
            ethernet_header* eth_hdr
            ipv4_header* ip_hdr
            tcp_header* tcp_hdr
            udp_header* udp_hdr
            const uint8_t* payload
            int payload_len
            uint16_t src_port, dest_port
            int exchange_id
            bint is_trading_packet = False
            bint is_fix = False
            int ip_header_len
            int tcp_header_len
            int payload_start
            
        if packet_len < 14:  # Minimum Ethernet frame
            return None
            
        # Parse Ethernet header
        eth_hdr = <ethernet_header*>data
        
        if self._ntohs(eth_hdr.ethertype) != 0x0800:  # Not IPv4
            return None
            
        if packet_len < 34:  # Minimum IPv4 + Ethernet
            return None
            
        # Parse IPv4 header
        ip_hdr = <ipv4_header*>(data + 14)
        
        if (ip_hdr.version_ihl >> 4) != 4:  # Not IPv4
            return None
            
        ip_header_len = (ip_hdr.version_ihl & 0x0F) * 4
        
        if ip_header_len < 20 or packet_len < 14 + ip_header_len:
            return None
            
        # Fast trading protocol detection
        if ip_hdr.protocol == 6:  # TCP
            if packet_len < 14 + ip_header_len + 20:  # Minimum TCP header
                return None
                
            tcp_hdr = <tcp_header*>(data + 14 + ip_header_len)
            src_port = self._ntohs(tcp_hdr.src_port)
            dest_port = self._ntohs(tcp_hdr.dest_port)
            
            # Check if trading-related port
            is_trading_packet = self._is_exchange_port(src_port) or self._is_exchange_port(dest_port)
            
            if is_trading_packet:
                exchange_id = self._get_exchange_id(dest_port)
                if exchange_id == 0:
                    exchange_id = self._get_exchange_id(src_port)
                    
                # Check payload for FIX protocol
                tcp_header_len = ((tcp_hdr.data_offset_flags >> 4) & 0x0F) * 4
                payload_len = packet_len - 14 - ip_header_len - tcp_header_len
                
                if payload_len > 0:
                    payload = data + 14 + ip_header_len + tcp_header_len
                    is_fix = self._is_fix_protocol(payload, payload_len)
                    
        elif ip_hdr.protocol == 17:  # UDP
            if packet_len < 14 + ip_header_len + 8:  # Minimum UDP header
                return None
                
            udp_hdr = <udp_header*>(data + 14 + ip_header_len)
            src_port = self._ntohs(udp_hdr.src_port)
            dest_port = self._ntohs(udp_hdr.dest_port)
            
            # Check if trading-related port
            is_trading_packet = self._is_exchange_port(src_port) or self._is_exchange_port(dest_port)
            
            if is_trading_packet:
                exchange_id = self._get_exchange_id(dest_port)
                if exchange_id == 0:
                    exchange_id = self._get_exchange_id(src_port)
                    
                # Check payload 
                payload_len = packet_len - 14 - ip_header_len - 8
                if payload_len > 0:
                    payload = data + 14 + ip_header_len + 8
                    is_fix = self._is_fix_protocol(payload, payload_len)
        
        # Update statistics
        self.packets_parsed += 1
        self.bytes_processed += packet_len
        
        # Return only trading-relevant packets for efficiency
        if not is_trading_packet:
            return None
            
        # Fast return of essential trading information
        return {
            'src_port': src_port,
            'dest_port': dest_port,
            'protocol': 'TCP' if ip_hdr.protocol == 6 else 'UDP',
            'exchange_id': exchange_id,
            'exchange_name': ['Unknown', 'NYSE', 'NASDAQ', 'CBOE'][exchange_id],
            'is_fix': is_fix,
            'packet_size': packet_len,
            'src_ip': self._ntohl(ip_hdr.src_ip),
            'dest_ip': self._ntohl(ip_hdr.dest_ip),
        }
        
    def get_statistics(self):
        """Get parsing statistics."""
        return {
            'packets_parsed': self.packets_parsed,
            'bytes_processed': self.bytes_processed,
            'parse_time_ns': self.parse_time_ns,
        }
        
    def reset_statistics(self):
        """Reset parsing statistics."""
        self.packets_parsed = 0
        self.bytes_processed = 0
        self.parse_time_ns = 0 