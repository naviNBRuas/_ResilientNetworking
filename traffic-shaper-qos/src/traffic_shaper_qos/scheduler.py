from __future__ import annotations

import heapq
import threading
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(order=True)
class _QueueEntry:
    """
    Internal entry for the scheduling heap.
    Sort order is determined primarily by virtual_time.
    """
    virtual_time: float
    weight: float = field(compare=False)
    queue: deque = field(compare=False, default_factory=deque)
    name: str = field(compare=False, default="")
    active: bool = field(compare=False, default=True)


class WeightedFairScheduler:
    """
    A thread-safe Weighted Fair Queueing (WFQ) scheduler.
    
    Allows multiple named queues with associated weights. Items are dequeued
    based on their virtual schedule time, ensuring weighted fairness.
    """

    def __init__(self) -> None:
        self._queues: Dict[str, _QueueEntry] = {}
        self._heap: List[_QueueEntry] = []
        self._lock = threading.RLock()

    def enqueue(self, queue_name: str, item: Any, weight: float = 1.0) -> None:
        """
        Add an item to the specified queue.
        
        Args:
            queue_name: Identifier for the queue.
            item: The item to enqueue.
            weight: The weight for the queue (default 1.0). Higher weight = more bandwidth.
                    If the queue already exists, its weight is updated.
        """
        with self._lock:
            entry = self._queues.get(queue_name)
            
            if entry is None:
                # New queue. Initialize virtual time to current system minimum to prevent starvation of others.
                # If heap is empty, start at 0.0.
                start_vt = self._heap[0].virtual_time if self._heap else 0.0
                entry = _QueueEntry(
                    virtual_time=start_vt,
                    weight=weight,
                    name=queue_name,
                    active=True
                )
                self._queues[queue_name] = entry
                heapq.heappush(self._heap, entry)
            else:
                # Update weight
                entry.weight = weight
                
                # If queue was inactive (empty), reactivate it.
                if not entry.active:
                    entry.active = True
                    # Bring virtual time up to date if it fell behind while idle.
                    current_min_vt = self._heap[0].virtual_time if self._heap else 0.0
                    entry.virtual_time = max(entry.virtual_time, current_min_vt)
                    heapq.heappush(self._heap, entry)
            
            entry.queue.append(item)

    def dequeue(self) -> Any:
        """
        Remove and return the next item according to the WFQ algorithm.
        
        Returns:
            The dequeued item.
            
        Raises:
            IndexError: If all queues are empty.
        """
        with self._lock:
            while self._heap:
                entry = heapq.heappop(self._heap)
                
                if not entry.queue:
                    # This implies the queue became empty previously and was marked inactive,
                    # but we are seeing it now. Or it was drained.
                    # In our logic, if we pop it and it's empty, we just mark inactive and don't push back.
                    # So if we see an empty queue here, it might be a stale handle or logic error.
                    # Safest is to mark inactive and continue.
                    entry.active = False
                    continue

                item = entry.queue.popleft()
                
                if entry.queue:
                    # Update virtual time: VT_new = VT_old + 1/weight
                    # Use max(epsilon, weight) to avoid division by zero.
                    entry.virtual_time += 1.0 / max(0.0001, entry.weight)
                    heapq.heappush(self._heap, entry)
                else:
                    # Queue is now empty. Mark as inactive.
                    # Do NOT push back to heap. It will be re-added upon enqueue.
                    entry.active = False
                
                return item
            
            raise IndexError("No items to dequeue")

    def empty(self) -> bool:
        """Check if scheduler is empty."""
        with self._lock:
            # Efficient check: if heap is empty, we are definitely empty.
            # But technically heap might contain empty queues if we didn't lazy-clean properly?
            # Our dequeue logic guarantees heap only contains active queues or we clean them on pop.
            # But checking queues.values() is the ground truth.
            return all(not e.queue for e in self._queues.values())

    def peek(self) -> Any:
        """
        Return the next item to be dequeued without removing it.
        
        Returns:
            The next item.
            
        Raises:
            IndexError: If empty.
        """
        with self._lock:
             # We need to find the first valid entry in heap
            temp_popped = []
            result = None
            
            while self._heap:
                entry = heapq.heappop(self._heap)
                if not entry.queue:
                    # Clean up empty queues found during peek
                    entry.active = False
                    continue
                
                result = entry.queue[0]
                temp_popped.append(entry)
                break
            
            # Restore heap
            for entry in temp_popped:
                heapq.heappush(self._heap, entry)
                
            if result is not None:
                return result
                
            raise IndexError("No items to peek")