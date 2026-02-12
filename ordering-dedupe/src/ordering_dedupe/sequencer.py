from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict, List, Generic, TypeVar, Tuple

T = TypeVar("T")


@dataclass
class Sequencer:
    """
    Thread-safe sequence number generator.
    """
    next_seq: int = 1
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def issue(self) -> int:
        """
        Issue the next sequence number.
        """
        with self._lock:
            seq = self.next_seq
            self.next_seq += 1
            return seq

    @staticmethod
    def reorder(items: List[Tuple[int, object]]) -> List[object]:
        """
        Stateless utility to sort a batch of items by their sequence number.
        Does not handle missing items or state.
        """
        return [v for _, v in sorted(items, key=lambda x: x[0])]


@dataclass
class Reorderer(Generic[T]):
    """
    Stateful reorderer that ensures items are delivered in strict sequence.
    Buffers out-of-order items and handles duplicates/late arrivals.
    """
    next_expected: int = 1
    _buffer: Dict[int, T] = field(default_factory=dict, init=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False)

    def push(self, sequence: int, item: T) -> List[T]:
        """
        Push an item with a sequence number.
        
        Returns:
            A list of items that are now in consecutive order starting from the expected sequence.
            Returns empty list if the item is buffered (gap detected) or late/duplicate.
        """
        with self._lock:
            if sequence < self.next_expected:
                # Late or duplicate
                return []
            
            if sequence == self.next_expected:
                # Expected item
                result = [item]
                self.next_expected += 1
                
                # Check buffer for subsequent items
                while self.next_expected in self._buffer:
                    result.append(self._buffer.pop(self.next_expected))
                    self.next_expected += 1
                return result
            
            # Future item, buffer it
            self._buffer[sequence] = item
            return []
    
    def reset(self, next_expected: int = 1):
        """Reset the reorderer state."""
        with self._lock:
            self.next_expected = next_expected
            self._buffer.clear()
