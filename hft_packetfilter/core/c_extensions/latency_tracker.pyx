# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: profile=False
# cython: linetrace=False

"""
Ultra-Low Latency Tracker

High-precision latency measurement and tracking for HFT applications.
Provides nanosecond-level accuracy for latency analysis.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import cython
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.stdlib cimport malloc, free
from libc.string cimport memset
import time
import numpy as np
cimport numpy as cnp

# Constants for latency calculations
cdef double NANOSEC_PER_SEC = 1000000000.0
cdef double MICROSEC_PER_SEC = 1000000.0
cdef int MAX_LATENCY_SAMPLES = 100000

# Latency measurement structure
cdef packed struct latency_sample:
    uint64_t timestamp_ns
    uint32_t latency_ns
    uint16_t exchange_id
    uint8_t protocol_type
    uint8_t padding

cdef class UltraLowLatencyTracker:
    """Ultra-low latency measurement and tracking system."""
    
    cdef:
        latency_sample* samples
        int sample_count
        int max_samples
        uint64_t total_samples
        uint64_t start_time_ns
        double min_latency_us
        double max_latency_us
        double sum_latency_us
        double sum_squared_latency_us
        uint64_t violation_count
        double target_latency_us
        bint initialized
        
    def __cinit__(self, int max_samples=MAX_LATENCY_SAMPLES, double target_latency_us=500.0):
        self.max_samples = max_samples
        self.target_latency_us = target_latency_us
        self.samples = <latency_sample*>malloc(max_samples * sizeof(latency_sample))
        
        if self.samples == NULL:
            raise MemoryError("Cannot allocate memory for latency samples")
            
        memset(self.samples, 0, max_samples * sizeof(latency_sample))
        self.sample_count = 0
        self.total_samples = 0
        self.min_latency_us = 999999.0
        self.max_latency_us = 0.0
        self.sum_latency_us = 0.0
        self.sum_squared_latency_us = 0.0
        self.violation_count = 0
        self.start_time_ns = <uint64_t>(time.time_ns())
        self.initialized = True
        
    def __dealloc__(self):
        if self.samples != NULL:
            free(self.samples)
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline uint64_t _get_time_ns(self):
        """Get high-precision time in nanoseconds."""
        return <uint64_t>(time.time_ns())
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef inline void _add_sample_fast(self, uint32_t latency_ns, uint16_t exchange_id, uint8_t protocol_type):
        """Fast internal sample addition without bounds checking."""
        cdef:
            int index = self.sample_count % self.max_samples
            double latency_us = latency_ns / 1000.0
            
        # Store sample
        self.samples[index].timestamp_ns = self._get_time_ns()
        self.samples[index].latency_ns = latency_ns
        self.samples[index].exchange_id = exchange_id
        self.samples[index].protocol_type = protocol_type
        
        # Update statistics
        if latency_us < self.min_latency_us:
            self.min_latency_us = latency_us
        if latency_us > self.max_latency_us:
            self.max_latency_us = latency_us
            
        self.sum_latency_us += latency_us
        self.sum_squared_latency_us += latency_us * latency_us
        
        # Check for violations
        if latency_us > self.target_latency_us:
            self.violation_count += 1
            
        self.sample_count += 1
        self.total_samples += 1
        
    def record_latency(self, double latency_us, int exchange_id=0, str protocol='TCP'):
        """
        Record a latency measurement.
        
        Args:
            latency_us: Latency in microseconds
            exchange_id: Exchange identifier (0=Unknown, 1=NYSE, 2=NASDAQ, 3=CBOE)
            protocol: Protocol type ('TCP', 'UDP', 'FIX')
        """
        cdef:
            uint32_t latency_ns = <uint32_t>(latency_us * 1000.0)
            uint16_t exch_id = <uint16_t>exchange_id
            uint8_t proto_type = 0
            
        # Convert protocol to numeric type
        if protocol == 'TCP':
            proto_type = 1
        elif protocol == 'UDP':
            proto_type = 2
        elif protocol == 'FIX':
            proto_type = 3
            
        self._add_sample_fast(latency_ns, exch_id, proto_type)
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def record_packet_latency(self, uint64_t send_time_ns, uint64_t recv_time_ns, 
                             int exchange_id=0, str protocol='TCP'):
        """
        Record latency from packet timestamps.
        
        Args:
            send_time_ns: Send timestamp in nanoseconds
            recv_time_ns: Receive timestamp in nanoseconds
            exchange_id: Exchange identifier
            protocol: Protocol type
        """
        if recv_time_ns <= send_time_ns:
            return  # Invalid timestamps
            
        cdef:
            uint64_t latency_ns_raw = recv_time_ns - send_time_ns
            uint32_t latency_ns = <uint32_t>min(latency_ns_raw, 4294967295)  # Cap at uint32 max
            double latency_us = latency_ns / 1000.0
            
        self.record_latency(latency_us, exchange_id, protocol)
        
    def get_current_latency_us(self):
        """Get the most recent latency measurement in microseconds."""
        if self.sample_count == 0:
            return 0.0
            
        cdef int last_index = (self.sample_count - 1) % self.max_samples
        return self.samples[last_index].latency_ns / 1000.0
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def get_percentile(self, double percentile):
        """
        Calculate latency percentile.
        
        Args:
            percentile: Percentile to calculate (0.0 - 100.0)
            
        Returns:
            float: Latency in microseconds at the given percentile
        """
        if self.sample_count == 0:
            return 0.0
            
        # Extract latencies into numpy array for fast sorting
        cdef:
            int actual_count = min(self.sample_count, self.max_samples)
            cnp.ndarray[cnp.float64_t, ndim=1] latencies = np.empty(actual_count, dtype=np.float64)
            int i
            
        for i in range(actual_count):
            latencies[i] = self.samples[i].latency_ns / 1000.0
            
        # Sort and calculate percentile
        latencies = np.sort(latencies)
        cdef int index = <int>((percentile / 100.0) * (actual_count - 1))
        
        return latencies[index]
        
    def get_statistics(self):
        """Get comprehensive latency statistics."""
        if self.sample_count == 0:
            return {
                'count': 0,
                'min_us': 0.0,
                'max_us': 0.0,
                'mean_us': 0.0,
                'std_us': 0.0,
                'p50_us': 0.0,
                'p95_us': 0.0,
                'p99_us': 0.0,
                'p99_9_us': 0.0,
                'violation_rate': 0.0,
                'target_us': self.target_latency_us,
            }
            
        cdef:
            double mean_us = self.sum_latency_us / self.total_samples
            double variance = (self.sum_squared_latency_us / self.total_samples) - (mean_us * mean_us)
            double std_us = variance ** 0.5 if variance > 0 else 0.0
            double violation_rate = (self.violation_count / float(self.total_samples)) * 100.0
            
        return {
            'count': self.total_samples,
            'min_us': self.min_latency_us,
            'max_us': self.max_latency_us,
            'mean_us': mean_us,
            'std_us': std_us,
            'p50_us': self.get_percentile(50.0),
            'p95_us': self.get_percentile(95.0),
            'p99_us': self.get_percentile(99.0),
            'p99_9_us': self.get_percentile(99.9),
            'violation_rate': violation_rate,
            'target_us': self.target_latency_us,
        }
        
    def get_exchange_statistics(self, int exchange_id):
        """Get statistics for a specific exchange."""
        if self.sample_count == 0:
            return None
            
        cdef:
            int actual_count = min(self.sample_count, self.max_samples)
            list exchange_latencies = []
            int i
            double latency_us
            
        # Extract latencies for specific exchange
        for i in range(actual_count):
            if self.samples[i].exchange_id == exchange_id:
                latency_us = self.samples[i].latency_ns / 1000.0
                exchange_latencies.append(latency_us)
                
        if not exchange_latencies:
            return None
            
        # Calculate statistics
        cdef:
            int count = len(exchange_latencies)
            double min_lat = min(exchange_latencies)
            double max_lat = max(exchange_latencies)
            double mean_lat = sum(exchange_latencies) / count
            double variance = sum([(x - mean_lat) ** 2 for x in exchange_latencies]) / count
            double std_lat = variance ** 0.5 if variance > 0 else 0.0
            
        exchange_latencies.sort()
        
        return {
            'exchange_id': exchange_id,
            'count': count,
            'min_us': min_lat,
            'max_us': max_lat,
            'mean_us': mean_lat,
            'std_us': std_lat,
            'p50_us': exchange_latencies[int(0.5 * (count - 1))],
            'p95_us': exchange_latencies[int(0.95 * (count - 1))],
            'p99_us': exchange_latencies[int(0.99 * (count - 1))],
        }
        
    def reset_statistics(self):
        """Reset all latency statistics."""
        self.sample_count = 0
        self.total_samples = 0
        self.min_latency_us = 999999.0
        self.max_latency_us = 0.0
        self.sum_latency_us = 0.0
        self.sum_squared_latency_us = 0.0
        self.violation_count = 0
        self.start_time_ns = <uint64_t>(time.time_ns())
        
        if self.samples != NULL:
            memset(self.samples, 0, self.max_samples * sizeof(latency_sample))
            
    def set_target_latency(self, double target_us):
        """Set the target latency threshold."""
        self.target_latency_us = target_us
        
    def get_sample_count(self):
        """Get current number of samples."""
        return self.total_samples
        
    def is_violation(self, double latency_us):
        """Check if latency exceeds target."""
        return latency_us > self.target_latency_us 