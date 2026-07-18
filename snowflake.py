# snowflake.py
import time
import os

# Custom Epoch (e.g., Jan 1, 2026)
EPOCH = 1767225600000 

# Bit allocations
WORKER_ID_BITS = 10
SEQUENCE_BITS = 12

MAX_WORKER_ID = -1 ^ (-1 << WORKER_ID_BITS)
MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BITS)

WORKER_ID_SHIFT = SEQUENCE_BITS
TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + WORKER_ID_BITS

class SnowflakeGenerator:
    def __init__(self):
        # Read unique worker ID from environment variable assigned in docker-compose
        self.worker_id = int(os.getenv("WORKER_ID", 0))
        if self.worker_id > MAX_WORKER_ID or self.worker_id < 0:
            raise ValueError(f"Worker ID must be between 0 and {MAX_WORKER_ID}")
            
        self.sequence = 0
        self.last_timestamp = -1

    def _get_current_ms(self) -> int:
        return int(time.time() * 1000)

    def generate_id(self) -> int:
        timestamp = self._get_current_ms()

        if timestamp < self.last_timestamp:
            raise RuntimeError("Clock moved backwards! Rejecting ID generation.")

        if timestamp == self.last_timestamp:
            # Same millisecond, increment sequence counter
            self.sequence = (self.sequence + 1) & MAX_SEQUENCE
            if self.sequence == 0:
                # Sequence overflowed, wait for next millisecond
                while timestamp <= self.last_timestamp:
                    timestamp = self._get_current_ms()
        else:
            # New millisecond, reset sequence counter
            self.sequence = 0

        self.last_timestamp = timestamp

        # Bitwise shift variables into a single 64-bit integer
        generated_id = (
            ((timestamp - EPOCH) << TIMESTAMP_LEFT_SHIFT) |
            (self.worker_id << WORKER_ID_SHIFT) |
            self.sequence
        )
        return generated_id

# Instantiate a single instance per container process
id_worker = SnowflakeGenerator()