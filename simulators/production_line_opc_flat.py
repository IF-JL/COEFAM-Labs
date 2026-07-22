#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_line_opc_flat.py
===========================
OPC UA server that exposes the production line as a FLAT LIST OF TAGS.

This is how machine data very often lands from a gateway or PLC: a bag of loose,
generically-named variables directly under Objects, with no structure and no
semantics. A consuming system has to know every tag name by hand and hard-code
what each one means. It "works", but it does not scale and it is not reusable.

Contrast this with production_line_opc_profile.py, which exposes the SAME data as
a proper information model (a typed ObjectType / profile) that a client can
discover and absorb generically.

Run centrally; students browse it with an OPC UA client (e.g. UaExpert).

    pip install asyncua
    python production_line_opc_flat.py --host 0.0.0.0 --port 4840

Then in UaExpert connect to  opc.tcp://<this-machine-ip>:4840/coefam/line1
and expand Objects -> you will see a flat list of tags.
"""

import argparse
import asyncio
import sys

from asyncua import Server

from line_model import ProductionLine


async def run(host, port, rate, max_ticks):
    server = Server()
    await server.init()
    endpoint = "opc.tcp://%s:%d/coefam/line1" % (host, port)
    server.set_endpoint(endpoint)
    server.set_server_name("COEFAM Production Line (flat tags)")
    idx = await server.register_namespace("http://coefam.intellexfabrica.com/line1/flat")

    objects = server.nodes.objects

    # FLAT: every value is a loose variable directly under Objects.
    tags = {}
    async def add(name, initial):
        tags[name] = await objects.add_variable(idx, name, initial)

    await add("weight_g", 0.0)
    await add("temperature_c", 0.0)
    await add("vibration_mm_s", 0.0)
    await add("state", "INIT")
    await add("order_id", "")
    await add("order_product", "")
    await add("order_target", 0)
    await add("order_produced", 0)
    await add("order_progress_pct", 0.0)
    await add("quality_last_result", "")
    await add("quality_reject_count", 0)
    await add("kpi_availability", 0.0)
    await add("kpi_performance", 0.0)
    await add("kpi_quality", 0.0)
    await add("kpi_oee", 0.0)

    line = ProductionLine()
    print("Flat-tag OPC UA server at %s" % endpoint)
    print("  UaExpert -> Objects -> a flat list of %d tags (no structure, no types beyond the raw value)." % len(tags))

    async with server:
        k = 0
        while True:
            k += 1
            m = line.tick(k)
            await tags["weight_g"].write_value(float(m["weight_g"]))
            await tags["temperature_c"].write_value(float(m["temperature_c"]))
            await tags["vibration_mm_s"].write_value(float(m["vibration_mm_s"]))
            await tags["state"].write_value(m["state"])
            await tags["order_id"].write_value(m["order"])
            await tags["order_product"].write_value(m["product"])
            await tags["order_target"].write_value(int(m["target"]))
            await tags["order_produced"].write_value(int(m["produced"]))
            await tags["order_progress_pct"].write_value(float(m["progress_pct"]))
            if m["result"]:
                await tags["quality_last_result"].write_value(m["result"])
            await tags["quality_reject_count"].write_value(int(m["reject"]))
            await tags["kpi_availability"].write_value(float(m["availability"]))
            await tags["kpi_performance"].write_value(float(m["performance"]))
            await tags["kpi_quality"].write_value(float(m["quality"]))
            await tags["kpi_oee"].write_value(float(m["oee"]))
            if k % 5 == 0:
                print("t=%5ds  produced=%3d/%d  OEE=%.2f" % (k, m["produced"], m["target"], m["oee"]))
            if max_ticks and k >= max_ticks:
                break
            await asyncio.sleep(rate)


def main():
    ap = argparse.ArgumentParser(description="OPC UA server: production line as a flat tag list.")
    ap.add_argument("--host", default="0.0.0.0", help="bind host (default 0.0.0.0 = all interfaces)")
    ap.add_argument("--port", type=int, default=4840)
    ap.add_argument("--rate", type=float, default=1.0, help="seconds between ticks")
    ap.add_argument("--max-ticks", type=int, default=0, help="stop after N ticks (0 = forever)")
    a = ap.parse_args()
    try:
        asyncio.run(run(a.host, a.port, a.rate, a.max_ticks))
    except KeyboardInterrupt:
        print("\nstopped.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
