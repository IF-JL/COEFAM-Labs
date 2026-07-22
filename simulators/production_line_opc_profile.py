#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_line_opc_profile.py
==============================
OPC UA server that exposes the SAME production line as a PROPER INFORMATION MODEL.

Instead of a flat bag of tags, it:
  * defines a reusable ObjectType  ->  "ProductionLineType" (a *profile* / template)
  * organizes the data into meaningful sub-objects: Fill, Motor, Status, Order,
    Quality, KPI
  * gives every variable an explicit OPC UA DATA TYPE (Double / Int32 / String)
  * attaches ENGINEERING UNITS (EUInformation) to the analog values
  * instantiates the type as an instance "Line1"

Why this matters for "absorbing the data properly":
A consumer can *discover* the model. It reads the type definition once, learns the
structure, the data type and the unit of every value, and maps it into its own
system generically -- instead of hard-coding a list of tag names and guessing what
each one means (as it must with production_line_opc_flat.py).

Run centrally; browse with UaExpert (see the ProductionLineType under Types, and the
structured Line1 instance under Objects). A ready-made consumer is opc_client_absorb.py.

    pip install asyncua
    python production_line_opc_profile.py --host 0.0.0.0 --port 4840
    # UaExpert -> opc.tcp://<this-machine-ip>:4840/coefam/line1
"""

import argparse
import asyncio
import sys

from asyncua import Server, ua

from line_model import ProductionLine


async def run(host, port, rate, max_ticks):
    server = Server()
    await server.init()
    endpoint = "opc.tcp://%s:%d/coefam/line1" % (host, port)
    server.set_endpoint(endpoint)
    server.set_server_name("COEFAM Production Line (information model)")
    idx = await server.register_namespace("http://coefam.intellexfabrica.com/line1/model")

    # ---------- 1. Define the ProductionLineType (the profile / template) ----------
    line_type = await server.nodes.base_object_type.add_object_type(idx, "ProductionLineType")

    async def sub(parent, name):
        o = await parent.add_object(idx, name)
        await o.set_modelling_rule(True)          # Mandatory -> copied to instances
        return o

    async def var(parent, name, initial, vtype, unit=None, desc=None):
        v = await parent.add_variable(idx, name, initial, varianttype=vtype)
        await v.set_modelling_rule(True)
        if desc:
            await v.write_attribute(ua.AttributeIds.Description,
                                    ua.DataValue(ua.Variant(ua.LocalizedText(desc), ua.VariantType.LocalizedText)))
        if unit:
            eu = ua.EUInformation()
            eu.NamespaceUri = "http://www.opcfoundation.org/UA/units/un/cefact"
            eu.DisplayName = ua.LocalizedText(unit)
            eu.Description = ua.LocalizedText(unit)
            prop = await v.add_property(idx, "EngineeringUnits", ua.Variant(eu, ua.VariantType.ExtensionObject))
            await prop.set_modelling_rule(True)   # copy the unit onto instances too
        return v

    fill = await sub(line_type, "Fill")
    await var(fill, "WeightGrams", 0.0, ua.VariantType.Double, unit="g", desc="Fill weight")
    await var(fill, "Temperature", 0.0, ua.VariantType.Double, unit="degC", desc="Fill temperature")

    motor = await sub(line_type, "Motor")
    await var(motor, "Vibration", 0.0, ua.VariantType.Double, unit="mm/s", desc="Motor vibration")

    status = await sub(line_type, "Status")
    await var(status, "State", "INIT", ua.VariantType.String, desc="Line running state")

    order = await sub(line_type, "Order")
    await var(order, "Id", "", ua.VariantType.String, desc="Work order id")
    await var(order, "Product", "", ua.VariantType.String, desc="Product being made")
    await var(order, "Target", 0, ua.VariantType.Int32, unit="parts", desc="Order target quantity")
    await var(order, "Produced", 0, ua.VariantType.Int32, unit="parts", desc="Parts produced so far")
    await var(order, "ProgressPct", 0.0, ua.VariantType.Double, unit="%", desc="Order progress")

    quality = await sub(line_type, "Quality")
    await var(quality, "LastResult", "", ua.VariantType.String, desc="Last part Pass/Fail")
    await var(quality, "RejectCount", 0, ua.VariantType.Int32, unit="parts", desc="Rejected parts")

    kpi = await sub(line_type, "KPI")
    await var(kpi, "Availability", 0.0, ua.VariantType.Double, unit="ratio", desc="Availability")
    await var(kpi, "Performance", 0.0, ua.VariantType.Double, unit="ratio", desc="Performance")
    await var(kpi, "Quality", 0.0, ua.VariantType.Double, unit="ratio", desc="Quality")
    await var(kpi, "OEE", 0.0, ua.VariantType.Double, unit="ratio", desc="Overall Equipment Effectiveness")

    # ---------- 2. Instantiate the type as "Line1" ----------
    line_obj = await server.nodes.objects.add_object(idx, "Line1", objecttype=line_type.nodeid)

    async def h(*path):
        return await line_obj.get_child(["%d:%s" % (idx, p) for p in path])

    node = {
        "weight": await h("Fill", "WeightGrams"),
        "temp": await h("Fill", "Temperature"),
        "vib": await h("Motor", "Vibration"),
        "state": await h("Status", "State"),
        "oid": await h("Order", "Id"),
        "product": await h("Order", "Product"),
        "target": await h("Order", "Target"),
        "produced": await h("Order", "Produced"),
        "progress": await h("Order", "ProgressPct"),
        "result": await h("Quality", "LastResult"),
        "reject": await h("Quality", "RejectCount"),
        "avail": await h("KPI", "Availability"),
        "perf": await h("KPI", "Performance"),
        "qual": await h("KPI", "Quality"),
        "oee": await h("KPI", "OEE"),
    }

    line = ProductionLine()
    print("Information-model OPC UA server at %s" % endpoint)
    print("  UaExpert -> Types/ObjectTypes: 'ProductionLineType' (the profile)")
    print("           -> Objects: 'Line1' -> Fill / Motor / Status / Order / Quality / KPI (typed, with units)")

    async with server:
        k = 0
        while True:
            k += 1
            m = line.tick(k)
            await node["weight"].write_value(float(m["weight_g"]))
            await node["temp"].write_value(float(m["temperature_c"]))
            await node["vib"].write_value(float(m["vibration_mm_s"]))
            await node["state"].write_value(m["state"])
            await node["oid"].write_value(m["order"])
            await node["product"].write_value(m["product"])
            await node["target"].write_value(ua.Variant(int(m["target"]), ua.VariantType.Int32))
            await node["produced"].write_value(ua.Variant(int(m["produced"]), ua.VariantType.Int32))
            await node["progress"].write_value(float(m["progress_pct"]))
            if m["result"]:
                await node["result"].write_value(m["result"])
            await node["reject"].write_value(ua.Variant(int(m["reject"]), ua.VariantType.Int32))
            await node["avail"].write_value(float(m["availability"]))
            await node["perf"].write_value(float(m["performance"]))
            await node["qual"].write_value(float(m["quality"]))
            await node["oee"].write_value(float(m["oee"]))
            if k % 5 == 0:
                print("t=%5ds  produced=%3d/%d  OEE=%.2f" % (k, m["produced"], m["target"], m["oee"]))
            if max_ticks and k >= max_ticks:
                break
            await asyncio.sleep(rate)


def main():
    ap = argparse.ArgumentParser(description="OPC UA server: production line as a typed information model.")
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
