import os
import time


class ConsistencyTester:
    def __init__(self, redis) -> None:
        self.r = redis
        self.working_set = 1000
        self.keyspace = 10000
        self.writes = 0
        self.reads = 0
        self.failed_writes = 0
        self.failed_reads = 0
        self.lost_writes = 0
        self.not_ack_writes = 0
        self.delay = 0
        self.cached = {}  # We take our view of data stored in the DB.
        time_stamp_us = time.time_ns() % 10**9 // 1000  # Get ns
        self.prefix = "|".join([str(os.getpid()), str(time_stamp_us),
                       str(self.r.object_id), ""])
        self.errtime = {}
