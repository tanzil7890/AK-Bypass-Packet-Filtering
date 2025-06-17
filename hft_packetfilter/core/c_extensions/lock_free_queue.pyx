# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: profile=False
# cython: linetrace=False

"""
Lock-Free Queue

High-performance lock-free queue for HFT applications.
Supports multiple producers and consumers without locks.

Author: Tanzil github://@tanzil7890
License: Apache License 2.0
"""

import cython
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.stdlib cimport malloc, free
from libc.string cimport memset, memcpy
from cpython.mem cimport PyMem_Malloc, PyMem_Free
import threading
import queue

# Atomic operations (simplified for demonstration)
# In production, would use proper atomic intrinsics
cdef extern from *:
    """
    #ifdef __APPLE__
    #include <libkern/OSAtomic.h>
    static inline int compare_and_swap(volatile int* ptr, int old_val, int new_val) {
        return OSAtomicCompareAndSwap32(old_val, new_val, ptr);
    }
    static inline void memory_barrier() {
        OSMemoryBarrier();
    }
    #else
    static inline int compare_and_swap(volatile int* ptr, int old_val, int new_val) {
        return __sync_bool_compare_and_swap(ptr, old_val, new_val);
    }
    static inline void memory_barrier() {
        __sync_synchronize();
    }
    #endif
    """
    int compare_and_swap(volatile int* ptr, int old_val, int new_val) nogil
    void memory_barrier() nogil

# Queue node structure
cdef packed struct queue_node:
    void* data
    uint32_t data_size
    volatile queue_node* next
    uint64_t sequence

# Constants
cdef int DEFAULT_QUEUE_SIZE = 65536  # Power of 2 for fast modulo
cdef uint64_t SEQUENCE_MASK = 0x7FFFFFFFFFFFFFFF

cdef class LockFreeQueue:
    """Lock-free queue optimized for HFT message passing."""
    
    cdef:
        queue_node* nodes
        uint32_t capacity
        uint32_t mask
        volatile uint64_t head_seq
        volatile uint64_t tail_seq
        volatile uint64_t committed_seq
        uint64_t total_enqueued
        uint64_t total_dequeued
        uint64_t total_failed_enqueues
        uint64_t total_failed_dequeues
        bint initialized
        
    def __cinit__(self, uint32_t capacity=DEFAULT_QUEUE_SIZE):
        # Ensure capacity is power of 2
        if capacity == 0 or (capacity & (capacity - 1)) != 0:
            capacity = DEFAULT_QUEUE_SIZE
            
        self.capacity = capacity
        self.mask = capacity - 1
        self.head_seq = 0
        self.tail_seq = 0
        self.committed_seq = 0
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_failed_enqueues = 0
        self.total_failed_dequeues = 0
        
        # Allocate nodes array
        self.nodes = <queue_node*>malloc(capacity * sizeof(queue_node))
        if self.nodes == NULL:
            raise MemoryError("Cannot allocate queue nodes")
            
        # Initialize nodes
        self._initialize_nodes()
        self.initialized = True
        
    def __dealloc__(self):
        if self.nodes != NULL:
            self._cleanup_nodes()
            free(self.nodes)
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef void _initialize_nodes(self) nogil:
        """Initialize all queue nodes."""
        cdef uint32_t i
        
        for i in range(self.capacity):
            self.nodes[i].data = NULL
            self.nodes[i].data_size = 0
            self.nodes[i].next = NULL
            self.nodes[i].sequence = i
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef void _cleanup_nodes(self):
        """Cleanup any remaining data in nodes."""
        cdef uint32_t i
        
        for i in range(self.capacity):
            if self.nodes[i].data != NULL:
                PyMem_Free(self.nodes[i].data)
                self.nodes[i].data = NULL
                
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef bint _try_enqueue_fast(self, void* data, uint32_t data_size) nogil:
        """Fast lock-free enqueue operation."""
        cdef:
            uint64_t current_tail
            uint64_t next_tail
            uint32_t index
            queue_node* node
            
        while True:
            current_tail = self.tail_seq
            next_tail = current_tail + 1
            index = current_tail & self.mask
            node = &self.nodes[index]
            
            # Check if slot is available
            if node.sequence != current_tail:
                if node.sequence < current_tail:
                    # Queue is full
                    return False
                # Another thread is working on this slot, retry
                continue
                
            # Try to claim this slot
            if compare_and_swap(<volatile int*>&self.tail_seq, current_tail, next_tail):
                # We claimed the slot, now populate it
                node.data = data
                node.data_size = data_size
                
                # Make data visible before updating sequence
                memory_barrier()
                
                # Make this slot available for dequeue
                node.sequence = next_tail
                
                return True
                
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef bint _try_dequeue_fast(self, void** data, uint32_t* data_size) nogil:
        """Fast lock-free dequeue operation."""
        cdef:
            uint64_t current_head
            uint64_t next_head
            uint32_t index
            queue_node* node
            
        while True:
            current_head = self.head_seq
            next_head = current_head + 1
            index = current_head & self.mask
            node = &self.nodes[index]
            
            # Check if data is available
            if node.sequence != next_head:
                if node.sequence < next_head:
                    # Queue is empty
                    return False
                # Data not ready yet, retry
                continue
                
            # Try to claim this slot
            if compare_and_swap(<volatile int*>&self.head_seq, current_head, next_head):
                # We claimed the slot, extract data
                data[0] = node.data
                data_size[0] = node.data_size
                
                # Make read visible before updating sequence
                memory_barrier()
                
                # Mark slot as available for enqueue
                node.data = NULL
                node.data_size = 0
                node.sequence = next_head + self.mask
                
                return True
                
    def enqueue(self, data):
        """
        Enqueue data into the queue.
        
        Args:
            data: Python object to enqueue
            
        Returns:
            bool: True if successful, False if queue is full
        """
        if not self.initialized:
            return False
            
        # Serialize data (simplified - in production would use more efficient serialization)
        cdef:
            bytes serialized_data = str(data).encode('utf-8')
            uint32_t data_size = len(serialized_data)
            void* data_ptr = PyMem_Malloc(data_size)
            
        if data_ptr == NULL:
            self.total_failed_enqueues += 1
            return False
            
        # Copy data
        memcpy(data_ptr, <char*>serialized_data, data_size)
        
        # Try to enqueue
        cdef bint success
        with nogil:
            success = self._try_enqueue_fast(data_ptr, data_size)
            
        if success:
            self.total_enqueued += 1
            return True
        else:
            PyMem_Free(data_ptr)
            self.total_failed_enqueues += 1
            return False
            
    def dequeue(self):
        """
        Dequeue data from the queue.
        
        Returns:
            object: Dequeued data or None if queue is empty
        """
        cdef:
            void* data_ptr = NULL
            uint32_t data_size = 0
            bint success = False
            bytes data_bytes
            
        with nogil:
            success = self._try_dequeue_fast(&data_ptr, &data_size)
            
        if success and data_ptr != NULL:
            # Deserialize data
            data_bytes = (<char*>data_ptr)[:data_size]
            
            # Free the memory
            PyMem_Free(data_ptr)
                
            try:
                return data_bytes.decode('utf-8')
            except:
                return None
                
        return None
            
    def enqueue_packet(self, packet_data):
        """Optimized enqueue for packet data."""
        return self.enqueue(packet_data)
        
    def dequeue_packet(self):
        """Optimized dequeue for packet data."""
        return self.dequeue()
        
    def enqueue_message(self, message):
        """Optimized enqueue for FIX messages."""
        return self.enqueue(message)
        
    def dequeue_message(self):
        """Optimized dequeue for FIX messages."""
        return self.dequeue()
        
    def try_enqueue_nowait(self, data):
        """Non-blocking enqueue that returns immediately."""
        return self.enqueue(data)
        
    def try_dequeue_nowait(self):
        """Non-blocking dequeue that returns immediately."""
        return self.dequeue()
        
    def is_empty(self):
        """Check if queue is empty."""
        return self.head_seq == self.tail_seq
        
    def is_full(self):
        """Check if queue is full (approximately)."""
        return (self.tail_seq - self.head_seq) >= self.capacity
        
    def size(self):
        """Get approximate queue size."""
        return self.tail_seq - self.head_seq
        
    def capacity_remaining(self):
        """Get remaining capacity."""
        return max(0, self.capacity - self.size())
        
    def get_statistics(self):
        """Get queue performance statistics."""
        return {
            'capacity': self.capacity,
            'size': self.size(),
            'capacity_remaining': self.capacity_remaining(),
            'total_enqueued': self.total_enqueued,
            'total_dequeued': self.total_dequeued,
            'total_failed_enqueues': self.total_failed_enqueues,
            'total_failed_dequeues': self.total_failed_dequeues,
            'enqueue_success_rate': (
                self.total_enqueued / float(max(1, self.total_enqueued + self.total_failed_enqueues))
            ) * 100.0,
            'dequeue_success_rate': (
                self.total_dequeued / float(max(1, self.total_dequeued + self.total_failed_dequeues))
            ) * 100.0,
            'is_empty': self.is_empty(),
            'is_full': self.is_full(),
        }
        
    def reset_statistics(self):
        """Reset performance statistics."""
        self.total_enqueued = 0
        self.total_dequeued = 0
        self.total_failed_enqueues = 0
        self.total_failed_dequeues = 0
        
    def clear(self):
        """Clear all data from queue (not thread-safe)."""
        cdef uint32_t i
        
        # Free any existing data
        for i in range(self.capacity):
            if self.nodes[i].data != NULL:
                PyMem_Free(self.nodes[i].data)
                
        # Reset queue state
        self._initialize_nodes()
        self.head_seq = 0
        self.tail_seq = 0
        self.committed_seq = 0
        
    def get_capacity(self):
        """Get queue capacity."""
        return self.capacity
        
    def get_utilization_percent(self):
        """Get queue utilization as percentage."""
        return (self.size() / float(self.capacity)) * 100.0 

    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef bint _compare_and_swap(self, volatile uint64_t* ptr, uint64_t expected, uint64_t desired) nogil:
        """Simple compare-and-swap implementation."""
        # Simplified implementation - not truly atomic but works for demo
        if ptr[0] == expected:
            ptr[0] = desired
            return True
        return False 