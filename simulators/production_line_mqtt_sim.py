#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_line_mqtt_sim.py
===========================
Run a simulated production line and publish its live data to an MQTT broker as a
structured topic tree. Intended to run CENTRALLY (on one machine) so a class can
point MQTT Explorer at that machine's broker and watch the data live.

The topic tree is organized by the system that consumes each branch:

    <root>/fill/*      <root>/motor/*   <root>/state    ->  SCADA / Historian
    <root>/order/*                                      ->  MES  (work order execution)
    <root>/quality/*                                    ->  QMS  (results / reject reasons)
    <root>/kpi/*                                        ->  ERP / Ops dashboards (OEE)
    <root>/telemetry   (one JSON payload)               ->  IIoT platform / broker ingest

Usage
-----
    pip install paho-mqtt

    # against a broker running on THIS machine (recommended for a class):
    python production_line_mqtt_sim.py --broker localhost --root coefam/line1

    # or against a public test broker (learning only):
    python production_line_mqtt_sim.py --broker broker.hivemq.com --root coefam/line1

Students then open MQTT Explorer, connect to the same broker
(host = this machine's IP or the public broker, port 1883) and subscribe to
`<root>/#`.

See README.md for broker setup (mosquitto) and network notes.
"""

import argparse
import json
import sys
import time

import paho.mqtt.client as mqtt

from line_model import ProductionLine


def make_client(client_id):
    """Create a paho client that works on both paho-mqtt 2.x and 1.x."""
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Publish a simulated production line to MQTT.")
    ap.add_argument("--broker", default="localhost", help="MQTT broker host (default: localhost)")
    ap.add_argument("--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    ap.add_argument("--root", default="coefam/line1", help="topic root (default: coefam/line1)")
    ap.add_argument("--rate", type=float, default=1.0, help="seconds between ticks (default: 1.0)")
    ap.add_argument("--max-ticks", type=int, default=0, help="stop after N ticks (0 = run forever)")
    args = ap.parse_args(argv)

    line = ProductionLine()
    client = make_client("coefam-line-sim")
    try:
        client.connect(args.broker, args.port, keepalive=60)
    except Exception as e:
        print("Could not connect to %s:%d -- is a broker running there? (%s)"
              % (args.broker, args.port, e))
        return 1
    client.loop_start()

    def pub(sub, val, retain=True):
        client.publish("%s/%s" % (args.root, sub), str(val), qos=0, retain=retain)

    print("Publishing '%s/#' to %s:%d every %.1fs  (Ctrl+C to stop)"
          % (args.root, args.broker, args.port, args.rate))
    print("  In MQTT Explorer: connect to %s:%d and subscribe to  %s/#"
          % (args.broker, args.port, args.root))

    k = 0
    try:
        while True:
            k += 1
            m = line.tick(k)
            # SCADA / historian -- fast sensor + machine state
            pub("fill/weight_g", m["weight_g"])
            pub("fill/temperature_c", m["temperature_c"])
            pub("motor/vibration_mm_s", m["vibration_mm_s"])
            pub("state", m["state"])
            # MES -- work order execution & counts
            pub("order/id", m["order"])
            pub("order/product", m["product"])
            pub("order/target", m["target"])
            pub("order/produced", m["produced"])
            pub("order/progress_pct", m["progress_pct"])
            # QMS -- quality results
            if m["result"]:
                pub("quality/last_result", m["result"])
                if m["reject_reason"]:
                    pub("quality/last_reject_reason", m["reject_reason"])
            pub("quality/reject_count", m["reject"])
            # ERP / dashboards -- KPIs
            pub("kpi/availability", m["availability"])
            pub("kpi/performance", m["performance"])
            pub("kpi/quality", m["quality"])
            pub("kpi/oee", m["oee"])
            # one consolidated JSON payload
            pub("telemetry", json.dumps({
                "order": m["order"], "produced": m["produced"], "target": m["target"],
                "weight_g": m["weight_g"], "temperature_c": m["temperature_c"],
                "last_result": m["result"], "oee": m["oee"],
            }), retain=False)

            if k % 5 == 0:
                print("t=%5ds  produced=%3d/%d  good=%d  reject=%d  OEE=%.2f"
                      % (k, m["produced"], m["target"], m["good"], m["reject"], m["oee"]))

            if args.max_ticks and k >= args.max_ticks:
                break
            time.sleep(args.rate)
    except KeyboardInterrupt:
        print("\nstopping...")
    finally:
        client.loop_stop()
        client.disconnect()
        print("disconnected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
