# COEFAM Simulators

Central data simulators for the course. **You run these on one machine**; students
connect over the network with a client tool (e.g. MQTT Explorer) to view the live
data. These are *not* part of the shareable student Colab labs.

```
Simulators/
├── line_model.py                    # shared production-line model (protocol-agnostic)
├── production_line_mqtt_sim.py      # publishes the line to MQTT
├── production_line_opc_flat.py      # OPC UA server — FLAT list of tags
├── production_line_opc_profile.py   # OPC UA server — typed information model (profile)
├── opc_client_absorb.py             # OPC UA client — flat vs profile absorption demo
└── README.md
```

`line_model.py` is reused by every transport, so the MQTT and OPC UA simulators drive
the *same* line — students compare MQTT vs OPC UA (and flat tags vs a profile) on
identical data.

## What it produces

One filling line running a work order, emitting **clean, in-spec data**:

| Topic branch | Consumed by |
|---|---|
| `<root>/fill/*`, `<root>/motor/*`, `<root>/state` | SCADA / Historian (fast sensor + machine state) |
| `<root>/order/*` | MES (work-order execution, counts, progress) |
| `<root>/quality/*` | QMS (results, reject reasons) |
| `<root>/kpi/*` | ERP / Ops dashboards (OEE, throughput) |
| `<root>/telemetry` | one JSON payload an IIoT platform routes to all of them |

## Run it (MQTT)

**1. Install Python deps** (on the central machine):
```
pip install paho-mqtt
```

**2. Have a broker for people to connect to.** Two options:

- **Local broker (recommended for a class)** — install Mosquitto on the central machine:
  - Windows: download from https://mosquitto.org/download/ and run it (listens on `1883`).
    To accept LAN connections, add a `mosquitto.conf` with:
    ```
    listener 1883 0.0.0.0
    allow_anonymous true
    ```
    and start with `mosquitto -c mosquitto.conf -v`.
  - Linux/Mac: `sudo apt install mosquitto` / `brew install mosquitto`, then `mosquitto -v`.
  - Find the machine's LAN IP (`ipconfig` / `ip addr`) — students connect to that IP.

- **Public test broker (learning only, no setup)** — use `broker.hivemq.com`. Everyone
  shares the namespace, so use a unique `--root`.

**3. Start the simulator:**
```
# local broker on this machine:
python production_line_mqtt_sim.py --broker localhost --root coefam/line1

# or public broker:
python production_line_mqtt_sim.py --broker broker.hivemq.com --root coefam/line1
```

Options: `--port` (default 1883), `--rate` seconds/tick (default 1.0),
`--max-ticks` N to stop after N ticks (0 = run forever).

## How students connect (MQTT Explorer)

1. Install **MQTT Explorer** (free): http://mqtt-explorer.com
2. New connection →
   - **Host**: the central machine's LAN IP (local broker) *or* `broker.hivemq.com` (public)
   - **Port**: `1883`, no username/password
3. **Connect** → expand `<root>` (e.g. `coefam/line1`) → watch the live topic tree.

Discussion prompt: which branch would each real system (SCADA, MES, QMS, ERP)
subscribe to, and why does each need a different update cadence?

## Run it (OPC UA)

Two servers expose the **same line** two ways — to teach why an information model
beats a flat tag dump:

- **`production_line_opc_flat.py`** — a **flat list of tags** under Objects (how data
  often lands: loose, no structure, no types/units). A consumer must hard-code every name.
- **`production_line_opc_profile.py`** — a proper **information model**: a reusable
  `ProductionLineType` (a *profile*), data organized into Fill / Motor / Status / Order /
  Quality / KPI, every value with an explicit **data type** (Double / Int32 / String) and
  **engineering unit**. A consumer can *discover* and absorb it.

```
pip install asyncua

# flat (loose tags):
python production_line_opc_flat.py    --host 0.0.0.0 --port 4840

# profile (typed information model):
python production_line_opc_profile.py --host 0.0.0.0 --port 4840
```
Run one at a time on `4840`, or give them different `--port`s to run both together.
Options: `--rate` seconds/tick, `--max-ticks` N (0 = forever).

**Browse with UaExpert** (free OPC UA client:
https://www.unified-automation.com/products/development-tools/uaexpert.html) —
connect to `opc.tcp://<this-machine-ip>:4840/coefam/line1`, then expand **Objects**:
- flat server → a flat list of tags
- profile server → **Line1** → Fill / Motor / Order / Quality / KPI (typed, with units);
  and under **Types → ObjectTypes**, the reusable **ProductionLineType**.

**See the "absorb properly" contrast in code** with the included client:
```
python opc_client_absorb.py --mode flat    --url opc.tcp://localhost:4840/coefam/line1
python opc_client_absorb.py --mode profile --url opc.tcp://localhost:4840/coefam/line1
```
- *flat* → prints a flat dict; the consumer had to know every tag name and guess units.
- *profile* → discovers every instance of `ProductionLineType` and builds a nested record
  carrying the **data type and engineering unit** of each value — no hard-coded names, and
  it auto-adapts to any new instance of the type. That is how an MES / ERP / historian
  should absorb the data.

## Network notes

- MQTT uses port **1883**; OPC UA uses port **4840**. The relevant port must be
  reachable from student machines to the central machine (same LAN, or open the
  firewall / port-forward). On the same Wi-Fi/LAN this usually works out of the box.
- The public MQTT broker needs only outbound internet from each machine.
- For OPC UA, if a client struggles with the advertised endpoint, start the server
  with `--host <this-machine-ip>` instead of `0.0.0.0`.
