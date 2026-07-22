#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
opc_client_absorb.py
====================
Shows the DIFFERENCE between absorbing OPC UA data from a flat tag list vs from a
proper information model. Point it at either simulator:

    pip install asyncua

    # against the flat-tag server -- consumer must hard-code names, guess meaning:
    python opc_client_absorb.py --mode flat    --url opc.tcp://localhost:4840/coefam/line1

    # against the profile server -- consumer DISCOVERS structure, types and units:
    python opc_client_absorb.py --mode profile --url opc.tcp://localhost:4840/coefam/line1

The flat path proves the pain: a hard-coded list of tag names, no types, no units,
no structure. The profile path proves the payoff: the consumer walks the model,
learns every value's data type and engineering unit, and builds a clean structured
record automatically -- exactly how an MES/ERP/historian should absorb the data.
"""

import argparse
import asyncio
import json
import sys

from asyncua import Client, ua


# What a naive consumer of the FLAT server is forced to maintain by hand.
# It has to know every name, and it still has no idea of type or unit.
FLAT_TAGS = [
    "weight_g", "temperature_c", "vibration_mm_s", "state",
    "order_id", "order_product", "order_target", "order_produced", "order_progress_pct",
    "quality_last_result", "quality_reject_count",
    "kpi_availability", "kpi_performance", "kpi_quality", "kpi_oee",
]


async def absorb_flat(client):
    """Read a flat server: match hard-coded names under Objects. No types/units."""
    children = await client.nodes.objects.get_children()
    by_name = {}
    for n in children:
        by_name[(await n.read_browse_name()).Name] = n
    record = {}
    missing = []
    for name in FLAT_TAGS:            # <-- we must KNOW this list
        node = by_name.get(name)
        if node is None:
            missing.append(name)
            continue
        record[name] = await node.read_value()
    print("FLAT absorption — a hand-maintained list of %d tags, no structure, no units:" % len(FLAT_TAGS))
    print(json.dumps(record, indent=2, default=str))
    if missing:
        print("  !! tags we expected but did not find (rename on the server breaks us):", missing)
    print("\n  Consumer had to: know every tag name, and separately hard-code what each means.")


async def absorb_profile(client):
    """Discover instances of ProductionLineType and absorb them generically:
    structure + data type + engineering unit are read from the model itself."""
    # 1) find every line instance by its TYPE (not by a hard-coded name)
    lines = []
    for obj in await client.nodes.objects.get_children():
        try:
            td = await obj.read_type_definition()
            tname = (await client.get_node(td).read_browse_name()).Name
        except Exception:
            tname = ""
        if tname == "ProductionLineType":
            lines.append(obj)

    if not lines:
        print("No ProductionLineType instances found — is this the profile server?")
        return

    for line in lines:
        name = (await line.read_browse_name()).Name
        record = {}
        for group in await line.get_children():
            gname = (await group.read_browse_name()).Name
            if gname == "Server":
                continue
            section = {}
            for v in await group.get_children():
                vn = (await v.read_browse_name()).Name
                value = await v.read_value()
                dtype = (await v.read_data_type_as_variant_type()).name
                unit = None
                for prop in await v.get_children():
                    if (await prop.read_browse_name()).Name == "EngineeringUnits":
                        unit = (await prop.read_value()).DisplayName.Text
                section[vn] = {"value": value, "type": dtype, "unit": unit}
            record[gname] = section
        print("PROFILE absorption — discovered instance '%s' of ProductionLineType:" % name)
        print(json.dumps(record, indent=2, default=str))
        print("\n  Consumer discovered: the structure, the data type AND the unit of every value —")
        print("  no hard-coded tag list, and it would auto-adapt to any new instance of the type.")


async def run(url, mode):
    async with Client(url=url) as client:
        if mode == "flat":
            await absorb_flat(client)
        else:
            await absorb_profile(client)


def main():
    ap = argparse.ArgumentParser(description="Absorb the production line over OPC UA (flat vs profile).")
    ap.add_argument("--url", default="opc.tcp://localhost:4840/coefam/line1")
    ap.add_argument("--mode", choices=["flat", "profile"], default="profile")
    a = ap.parse_args()
    asyncio.run(run(a.url, a.mode))
    return 0


if __name__ == "__main__":
    sys.exit(main())
