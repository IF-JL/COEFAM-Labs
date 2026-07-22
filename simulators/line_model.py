#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
line_model.py
=============
The shared "production line" simulation used by the MQTT and (future) OPC UA
simulators. It produces clean, in-spec data for one filling line running a work
order: continuous sensor values every tick, a completed part every couple of
ticks (~96% pass), and rolling KPIs (OEE = Availability x Performance x Quality).

Keep this file protocol-agnostic — the MQTT / OPC publishers import it and map
its output onto their transport. No networking here.
"""

import random
import time


class ProductionLine:
    def __init__(self, order="WO-10432", product="Bottle-500ml", target=500,
                 ideal_cycle_s=2.0, pass_rate=0.96, seed=None):
        self.order = order
        self.product = product
        self.target = target
        self.ideal = ideal_cycle_s
        self.pass_rate = pass_rate
        self.rng = random.Random(seed)
        self.reasons = ["Underweight", "Overweight", "Cap Missing", "Label Skew"]
        self.reset()

    def reset(self):
        """Start a fresh work order (called on startup and when target is reached)."""
        self.produced = 0
        self.good = 0
        self.reject = 0
        self.t0 = time.time()

    def tick(self, k):
        """Advance one step; return a flat dict of everything a publisher needs."""
        r = self.rng
        # continuous, in-spec sensor values
        weight = round(r.gauss(500, 1.2), 1)          # g   (target 500)
        temp = round(r.gauss(62, 0.8), 1)             # deg C fill temperature
        vib = round(abs(r.gauss(1.8, 0.25)), 2)       # mm/s

        # complete a part roughly every other tick
        result, reason = "", ""
        if k % 2 == 0 and self.produced < self.target:
            self.produced += 1
            if r.random() <= self.pass_rate:
                self.good += 1
                result = "Pass"
            else:
                self.reject += 1
                result = "Fail"
                reason = r.choice(self.reasons)

        # KPIs
        elapsed = max(time.time() - self.t0, 1.0)
        availability = 0.98
        performance = min(1.0, (self.produced * self.ideal) / elapsed)
        quality = (self.good / self.produced) if self.produced else 1.0
        oee = availability * performance * quality

        # loop the order so a central sim runs continuously
        if self.produced >= self.target:
            self.reset()

        return {
            "order": self.order, "product": self.product, "target": self.target,
            "produced": self.produced, "good": self.good, "reject": self.reject,
            "progress_pct": round(100 * self.produced / self.target, 1) if self.target else 0.0,
            "weight_g": weight, "temperature_c": temp, "vibration_mm_s": vib,
            "state": "RUNNING", "result": result, "reject_reason": reason,
            "availability": round(availability, 3), "performance": round(performance, 3),
            "quality": round(quality, 3), "oee": round(oee, 3),
        }


if __name__ == "__main__":
    # quick smoke test: print a few ticks
    line = ProductionLine(seed=1)
    for k in range(1, 7):
        print(line.tick(k))
