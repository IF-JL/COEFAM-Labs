# Instructor Guide — Data Integration Simulators

One page to run the session. The teaching content is in **`LESSON_data_integration.md`**.

## Before class (central machine)

- [ ] `pip install paho-mqtt asyncua`
- [ ] Note this machine's **LAN IP** (`ipconfig` / `ip addr`) — students connect to it.
- [ ] (MQTT, local broker option) install & start **Mosquitto** listening on `0.0.0.0:1883`
      — or plan to use the public broker `broker.hivemq.com`.
- [ ] Open ports **1883** (MQTT) and **4840** (OPC UA) on the firewall / same LAN.
- [ ] Smoke-test each sim once with `--max-ticks 10`.

## Before class (student machines)

- [ ] **MQTT Explorer** — http://mqtt-explorer.com
- [ ] **UaExpert** — https://www.unified-automation.com/products/development-tools/uaexpert.html
- [ ] (optional, for the code demo) `pip install asyncua`

## Which sim to run when

| Segment | Run on the central machine | Students use |
|---|---|---|
| 1 · Live data over MQTT | `python production_line_mqtt_sim.py --broker localhost --root coefam/line1` | MQTT Explorer → `<ip>:1883`, subscribe `coefam/line1/#` |
| 2 · OPC UA, flat tags | `python production_line_opc_flat.py --host 0.0.0.0 --port 4840` | UaExpert → `opc.tcp://<ip>:4840/coefam/line1` |
| 3 · OPC UA, information model | `python production_line_opc_profile.py --host 0.0.0.0 --port 4840` | UaExpert → same URL |
| 3b · absorb in code | (servers above) | `python opc_client_absorb.py --mode flat|profile --url opc.tcp://<ip>:4840/coefam/line1` |

Run **one OPC server at a time** on 4840 (stop segment 2 before segment 3), or give them
different `--port`s. Add `--rate 0.5` to make the data move faster on screen.

## Timing (≈90 min; trim the activity for 60)

10 framing · 20 MQTT demo+discuss · 15 flat OPC · 20 profile OPC + code · 15 activity · 10 debrief

## Discussion beats (the three "aha"s)

1. **MQTT topic tree** → *"Which real system subscribes to which branch, and why does each need a different update rate?"* (SCADA=fast sensors, MES=counts, QMS=quality, ERP=KPIs.)
2. **Flat OPC tags** → *"You're the integrator. What do you have to know to use `kpi_oee`? What breaks if the vendor renames it?"* (Everything is hand-mapped; renames break you.)
3. **Profile OPC model** → *"Same data — what changed? Now the consumer can read the type, unit and structure from the server itself."* (Discoverable, typed, reusable — the CESMII SM Profile idea.)

## Troubleshooting

- **Student can't connect** → wrong IP, firewall, or not on the same LAN. Verify with the instructor machine first (localhost).
- **UaExpert connects but endpoint fails** → restart the server with `--host <machine-ip>` instead of `0.0.0.0`.
- **MQTT Explorer empty** → wrong broker host/port, or sim not running; on the public broker make sure everyone uses the same `--root`.
- **Both OPC servers at once** → port clash on 4840; use different `--port`s.
