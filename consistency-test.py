import logging
import os
from random import random
import time
import redis

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

    def puterr(self, msg):
        if not self.errtime[msg] or time.time() != self.errtime[msg]:
            print(msg)
        
        self.errtime[msg] = self.time.time()
    
    def test(self):
        last_report = time.time()
        while True:
            # Read
            key = self.genkey()
            try:
                val = self.r.get(key)
                self.check_consistency(key,str(val))
                self.reads += 1
            except Exception as e:
                logging.error(f"Reading: {e}")
                self.failed_reads += 1

            # Write
            try:
                self.cached[key] = int(self.r.incr(key))
                self.writes += 1
            except Exception as e:
                logging.error(f"Reading: {e}")
                self.failed_writes += 1

            # Report
            time.sleep(self.delay)
            if time.time() != last_report:
                report = f"{self.reads} R ({self.failed_reads} err) | " + \
                         f"{self.writes} W ({self.failed_writes} err) | "
                report += f"{self.lost_writes} lost | " if self.lost_writes > 0 else ""
                report += f"{self.not_ack_writes} noack | " if self.not_ack_writes > 0 else ""
                last_report = time.time()
                print(report)
            