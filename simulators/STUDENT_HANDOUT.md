# Student Handout — Viewing Live Production-Line Data
### MQTT Explorer & UaExpert

Your instructor is running a **simulated production line** on a central machine. In this
session you'll connect to it and watch its live data two ways: over **MQTT** (with MQTT
Explorer) and over **OPC UA** (with UaExpert).

**Before you start, write down the address your instructor gives you:**

```
Instructor machine IP: ______________________     (e.g. 192.168.1.50)
```

---

## Tool 1 — MQTT Explorer (for the MQTT demo)

**Download & install**
1. Go to **http://mqtt-explorer.com**
2. Download the version for your OS (Windows / macOS / Linux) and install it.
   - Windows: run the installer.
   - macOS: open the `.dmg` and drag MQTT Explorer to Applications.

**Connect**
1. Open MQTT Explorer → **+** (new connection).
2. Enter:
   - **Name:** anything (e.g. `class`)
   - **Host:** the instructor machine IP *(or `broker.hivemq.com` if told to use the public broker)*
   - **Port:** `1883`
   - **Username / Password:** leave blank
3. Click **CONNECT**.
4. In the topic tree on the left, expand **`coefam`** → **`line1`**. You'll see the data
   update live.

**What to look for:** the tree is organized by the system that would consume each branch —
`fill/*` and `motor/*` (SCADA), `order/*` (MES), `quality/*` (QMS), `kpi/*` (ERP).

---

## Tool 2 — UaExpert (for the OPC UA demo)

UaExpert is a free OPC UA client. It needs a **free account** to download.

**Download & install**
1. Go to **https://www.unified-automation.com/products/development-tools/uaexpert.html**
2. Click **Download** → you'll be asked to **register a free account** (or log in).
3. Download **UaExpert** for your OS and install it.
   - Windows: run the installer (accept the defaults).

**Connect**
1. Open UaExpert → **Server → Add…** (or the **+** icon).
2. Under *Custom Discovery*, double-click **"Double click to Add Server..."** and paste:
   ```
   opc.tcp://<instructor-IP>:4840/coefam/line1
   ```
3. Select the server that appears → **OK**.
4. Right-click it in the *Project* panel → **Connect**. (If asked about a certificate,
   choose to trust it / continue.)
5. In the **Address Space** panel, expand **Objects**.

**What to look for (your instructor will switch between two servers):**
- **Flat server:** a plain list of tags (`weight_g`, `kpi_oee`, …) — no grouping, no units.
- **Profile server:** an object **`Line1`** organized into **Fill / Motor / Order / Quality /
  KPI**, where each value shows a **data type** and an **engineering unit**. Under
  **Types → ObjectTypes** you'll also find the reusable **`ProductionLineType`**.
  Drag a value into the *Data Access View* to watch it update.

---

## Activity — Map the data

Fill this in from what you see in the two tools.

| Value | MQTT topic | OPC UA (profile) path | Consumed by | Data type | Unit |
|---|---|---|---|---|---|
| Fill weight | `coefam/line1/fill/weight_g` | `Line1 / Fill / WeightGrams` | SCADA / Historian | Double | g |
| Parts produced | | | | | |
| Last quality result | | | | | |
| Reject count | | | | | |
| OEE | | | | | |

**Think about it**
1. In MQTT, where does the *meaning* of a value live? What happens to every subscriber if a
   topic gets renamed?
2. On the **flat** OPC server, what do you (the integrator) have to know and maintain by hand?
3. On the **profile** OPC server, what does the server tell you that the flat one doesn't?
   Why does that let a system absorb the data without a custom mapping?

---

## Troubleshooting

- **Can't connect / nothing shows up** → double-check the instructor IP and the port
  (`1883` for MQTT, `4840` for OPC UA), and that you're on the same network/Wi-Fi.
- **UaExpert certificate prompt** → choose to trust/continue; it's a local demo server.
- Still stuck? Tell your instructor which tool and what error you see.
