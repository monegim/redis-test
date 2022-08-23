import os
from random import random
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

    def genkey(self):
        # Write more often to a small subset of keys
        ks = self.keyspace if random.random() > 0.5 else self.working_set
        return self.prefix + "key_" + str(random.randint(0, ks))

    def check_consistency(self, key, value):
        expected = self.cached[key]
        if not expected:  # We lack info about previous state.
            return
        if expected > value:
            self.lost_writes += expected-value
        elif expected < value:
            self.not_ack_writes += value-expected
