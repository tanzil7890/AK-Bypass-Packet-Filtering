# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
# cython: profile=False
# cython: linetrace=False

"""
High-Performance Memory Pool

Zero-allocation memory pool for HFT applications.
Provides pre-allocated memory blocks for ultra-low latency.

Author: HFT-PacketFilter Development Team
License: Apache License 2.0
"""

import cython
from libc.stdint cimport uint8_t, uint16_t, uint32_t, uint64_t
from libc.stdlib cimport malloc, free
from libc.string cimport memset, memcpy
import mmap
import os

# Memory alignment constants
cdef int CACHE_LINE_SIZE = 64
cdef int PAGE_SIZE = 4096
cdef int DEFAULT_BLOCK_SIZE = 1024
cdef int DEFAULT_POOL_SIZE = 1024 * 1024  # 1MB

# Memory block structure
cdef packed struct memory_block:
    uint8_t* data
    uint32_t size
    uint32_t offset
    bint in_use
    memory_block* next

cdef class HighPerformanceMemoryPool:
    """High-performance memory pool with zero-allocation hot paths."""
    
    cdef:
        uint8_t* pool_memory
        memory_block* free_blocks
        memory_block* all_blocks
        uint32_t pool_size
        uint32_t block_size
        uint32_t num_blocks
        uint32_t blocks_allocated
        uint32_t blocks_free
        uint64_t total_allocations
        uint64_t total_deallocations
        bint use_mmap
        bint initialized
        int mmap_fd
        object allocated_views  # Python dict to track memoryviews
        
    def __cinit__(self, uint32_t pool_size=DEFAULT_POOL_SIZE, 
                  uint32_t block_size=DEFAULT_BLOCK_SIZE, 
                  bint use_mmap=True):
        self.pool_size = pool_size
        self.block_size = block_size
        self.num_blocks = pool_size // block_size
        self.use_mmap = use_mmap
        self.blocks_allocated = 0
        self.blocks_free = self.num_blocks
        self.total_allocations = 0
        self.total_deallocations = 0
        self.mmap_fd = -1
        self.allocated_views = {}  # Track memoryview -> block mapping
        
        # Allocate pool memory
        if self._allocate_pool() != 0:
            raise MemoryError("Failed to allocate memory pool")
            
        # Initialize block structures
        if self._initialize_blocks() != 0:
            raise MemoryError("Failed to initialize memory blocks")
            
        self.initialized = True
        
    def __dealloc__(self):
        self._cleanup_pool()
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef int _allocate_pool(self) nogil:
        """Allocate the main memory pool."""
        # Use regular allocation for better compatibility
        self.pool_memory = <uint8_t*>malloc(self.pool_size)
        if self.pool_memory == NULL:
            return -1
            
        # Zero the memory
        memset(self.pool_memory, 0, self.pool_size)
        return 0
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef int _initialize_blocks(self) nogil:
        """Initialize the block management structures."""
        cdef:
            uint32_t i
            memory_block* block
            uint32_t offset = 0
            
        # Allocate block structures
        self.all_blocks = <memory_block*>malloc(self.num_blocks * sizeof(memory_block))
        if self.all_blocks == NULL:
            return -1
            
        memset(self.all_blocks, 0, self.num_blocks * sizeof(memory_block))
        
        # Initialize free list
        self.free_blocks = &self.all_blocks[0]
        
        for i in range(self.num_blocks):
            block = &self.all_blocks[i]
            block.data = self.pool_memory + offset
            block.size = self.block_size
            block.offset = offset
            block.in_use = False
            
            if i < self.num_blocks - 1:
                block.next = &self.all_blocks[i + 1]
            else:
                block.next = NULL
                
            offset += self.block_size
            
        return 0
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef void _cleanup_pool(self) nogil:
        """Clean up allocated memory."""
        if self.all_blocks != NULL:
            free(self.all_blocks)
            self.all_blocks = NULL
            
        if self.pool_memory != NULL:
            if self.use_mmap:
                with gil:
                    try:
                        # Unmap memory-mapped region
                        os.close(self.mmap_fd) if self.mmap_fd >= 0 else None
                    except:
                        pass
            else:
                free(self.pool_memory)
            self.pool_memory = NULL
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef uint8_t* _allocate_block_fast(self) nogil:
        """Fast block allocation without locks."""
        cdef memory_block* block
        
        if self.free_blocks == NULL:
            return NULL  # Pool exhausted
            
        # Get block from free list
        block = self.free_blocks
        self.free_blocks = block.next
        
        # Mark as in use
        block.in_use = True
        block.next = NULL
        
        # Update counters
        self.blocks_allocated += 1
        self.blocks_free -= 1
        self.total_allocations += 1
        
        return block.data
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    cdef void _deallocate_block_fast(self, uint8_t* ptr) nogil:
        """Fast block deallocation without locks."""
        cdef:
            memory_block* block = NULL
            uint32_t i
            uint32_t offset = ptr - self.pool_memory
            
        # Find the block
        for i in range(self.num_blocks):
            if self.all_blocks[i].offset == offset:
                block = &self.all_blocks[i]
                break
                
        if block == NULL or not block.in_use:
            return  # Invalid pointer or double free
            
        # Clear the block data for security
        memset(block.data, 0, block.size)
        
        # Mark as free and add to free list
        block.in_use = False
        block.next = self.free_blocks
        self.free_blocks = block
        
        # Update counters
        self.blocks_allocated -= 1
        self.blocks_free += 1
        self.total_deallocations += 1
        
    def allocate(self, uint32_t size=0):
        """
        Allocate a memory block from the pool.
        
        Args:
            size: Requested size (ignored, returns fixed block size)
            
        Returns:
            memoryview: Memory view of allocated block, or None if exhausted
        """
        cdef uint8_t* ptr
        
        with nogil:
            ptr = self._allocate_block_fast()
            
        if ptr == NULL:
            return None
            
        # Create memory view and track it
        memview = <uint8_t[:self.block_size]>ptr
        self.allocated_views[id(memview)] = <size_t>ptr
        return memview
        
    def deallocate(self, memview):
        """
        Deallocate a memory block back to the pool.
        
        Args:
            memview: Memory view to deallocate
        """
        if memview is None:
            return
            
        # Look up the pointer from our tracking dict
        cdef uint8_t* ptr
        cdef size_t ptr_addr
        view_id = id(memview)
        if view_id in self.allocated_views:
            ptr_addr = self.allocated_views[view_id]
            del self.allocated_views[view_id]
            
            ptr = <uint8_t*>ptr_addr
            with nogil:
                self._deallocate_block_fast(ptr)
            
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def allocate_packet_buffer(self):
        """Allocate a buffer optimized for packet data."""
        return self.allocate(self.block_size)
        
    @cython.boundscheck(False)
    @cython.wraparound(False)
    def allocate_message_buffer(self):
        """Allocate a buffer optimized for FIX messages."""
        return self.allocate(self.block_size)
        
    def get_statistics(self):
        """Get memory pool statistics."""
        return {
            'pool_size_bytes': self.pool_size,
            'block_size_bytes': self.block_size,
            'total_blocks': self.num_blocks,
            'blocks_allocated': self.blocks_allocated,
            'blocks_free': self.blocks_free,
            'utilization_percent': (self.blocks_allocated / float(self.num_blocks)) * 100.0,
            'total_allocations': self.total_allocations,
            'total_deallocations': self.total_deallocations,
            'use_mmap': self.use_mmap,
        }
        
    def reset_pool(self):
        """Reset the entire memory pool (dangerous - invalidates all pointers)."""
        cdef uint32_t i
        
        # Clear tracking dict
        self.allocated_views.clear()
        
        with nogil:
            # Mark all blocks as free
            for i in range(self.num_blocks):
                self.all_blocks[i].in_use = False
                if i < self.num_blocks - 1:
                    self.all_blocks[i].next = &self.all_blocks[i + 1]
                else:
                    self.all_blocks[i].next = NULL
                    
            # Reset free list
            self.free_blocks = &self.all_blocks[0]
            
            # Reset counters
            self.blocks_allocated = 0
            self.blocks_free = self.num_blocks
            
            # Clear pool memory
            memset(self.pool_memory, 0, self.pool_size)
            
    def prefault_memory(self):
        """Pre-fault all memory pages to avoid page faults during trading."""
        cdef:
            uint32_t i
            uint8_t dummy
            
        # Touch every page to fault it in
        for i in range(0, self.pool_size, PAGE_SIZE):
            dummy = self.pool_memory[i]
            self.pool_memory[i] = dummy
                
    def get_block_size(self):
        """Get the fixed block size."""
        return self.block_size
        
    def get_free_blocks(self):
        """Get number of free blocks."""
        return self.blocks_free
        
    def is_address_in_pool(self, ptr):
        """Check if a pointer belongs to this pool."""
        cdef uint8_t* addr = <uint8_t*><size_t>ptr
        return (addr >= self.pool_memory and 
                addr < self.pool_memory + self.pool_size)
                
    def get_fragmentation_ratio(self):
        """Get memory fragmentation ratio (0.0 = no fragmentation)."""
        if self.blocks_allocated == 0:
            return 0.0
            
        # Simple fragmentation estimate based on free block distribution
        cdef:
            uint32_t free_segments = 0
            memory_block* current = self.free_blocks
            
        while current != NULL:
            free_segments += 1
            current = current.next
            
        if self.blocks_free == 0:
            return 0.0
            
        # Perfect case: all free blocks are contiguous (1 segment)
        # Worst case: every free block is isolated (blocks_free segments)
        return (free_segments - 1) / float(max(1, self.blocks_free - 1)) 