# Lesson — From Machine Data to Connected Systems
### MQTT, OPC UA, and why information models beat flat tags

**Where it fits:** best as an **Integrated Systems** lesson (Cert 02) — it makes the
"connect → contextualize → consume" and SM-Profile ideas tangible — with a hands-on
**Smart Factory Systems** (Cert 05) flavor. Placement is flexible; the concepts stand alone.

**Duration:** ~90 min (60-min version: shorten the activity).
**Format:** instructor runs simulators on one central machine; students connect over the LAN with viewer tools and (optionally) a Python client.
**Companion files:** `INSTRUCTOR_GUIDE.md` (setup/run), `production_line_mqtt_sim.py`, `production_line_opc_flat.py`, `production_line_opc_profile.py`, `opc_client_absorb.py`.

---

## Learning objectives

By the end, a student can:

1. **Trace** a production line's data to the four systems that consume it — SCADA/Historian, MES, QMS, ERP — and explain why each needs a different slice and cadence.
2. **View** the same live plant data over **MQTT** (in MQTT Explorer) and **OPC UA** (in UaExpert).
3. **Contrast** MQTT (lightweight pub/sub; meaning lives in topic names) with OPC UA (a browsable, structured address space).
4. **Explain** why a **flat list of tags** is expensive and fragile to integrate, and how an **information model / profile** — with explicit **data types** and **engineering units** — lets a system *discover and absorb* the data properly and reusably.

## The central scenario

One filling line runs a work order (`WO-10432`, Bottle-500ml, target 500). It continuously
produces **clean, in-spec data**: fill weight (~500 g), fill temperature (~62 °C), motor
vibration, part pass/fail (~96% good), counts, and rolling **OEE**. Every demo in this lesson
is the *same line* — only the transport and the modeling change. That's the whole point:
**the data is constant; how we structure and consume it is the lesson.**

---

## Agenda

| Time | Segment |
|---|---|
| 0:00 | 1 · Framing — the integration problem |
| 0:10 | 2 · Demo: the line over **MQTT** + who-absorbs-what |
| 0:30 | 3 · Demo: OPC UA as a **flat tag list** (the pain) |
| 0:45 | 4 · Demo: OPC UA as an **information model / profile** (the payoff) + absorb-in-code |
| 1:05 | 5 · Hands-on activity |
| 1:20 | 6 · Debrief & tie-back |

---

## 1 · Framing (10 min)

**Talking points**
- A modern line emits data every second. On its own that data is just numbers.
- Four different systems each want a *different slice* of it:
  - **SCADA / Historian** — fast sensor values and machine state, for real-time monitoring and trends.
  - **MES** — the work order: what's running, how many made, genealogy, progress.
  - **QMS** — quality results and reject reasons, for holds and SPC.
  - **ERP** — the business roll-up: order status, throughput, OEE.
- The integration question is not "can we get the data out" — it's **"how do we get it out so each system can absorb it without a custom, brittle, one-off mapping?"**
- Two levers we'll explore: the **transport** (MQTT vs OPC UA) and the **model** (flat tags vs an information model / profile).

**Board sketch:** the line in the middle; four boxes (SCADA, MES, QMS, ERP) around it; arrows in.

---

## 2 · Demo: the line over MQTT (20 min)

**Run:** `python production_line_mqtt_sim.py --broker localhost --root coefam/line1`
**Students:** MQTT Explorer → connect to `<central-ip>:1883` → expand `coefam/line1`.

**Walk the topic tree live** and name the consumer of each branch:

| Branch | Absorbed by |
|---|---|
| `fill/*`, `motor/*`, `state` | SCADA / Historian |
| `order/*` | MES |
| `quality/*` | QMS |
| `kpi/*` | ERP / dashboards |
| `telemetry` (one JSON payload) | an IIoT platform that routes fields to all of them |

**Talking points**
- MQTT is **publish/subscribe**: the line publishes to *topics*; any system subscribes to just the topics it cares about. Lightweight, great over flaky/low-bandwidth networks.
- **Where's the meaning?** Entirely in the **topic names**. `coefam/line1/kpi/oee` means "OEE" only because we *named* it that. MQTT itself carries no type, no unit, no structure — it's a string payload on a string topic.
- Notice values update at different rates — the fast sensor topics vs the slow KPI topics. Each consumer needs a different cadence.

**Discussion (5 min):** *"If a second line is added, or the vendor renames a topic, what happens to every subscriber?"* → every consumer must be told the new names by hand.

---

## 3 · Demo: OPC UA as a flat tag list (15 min)

**Stop the flat/other OPC server if running.**
**Run:** `python production_line_opc_flat.py --host 0.0.0.0 --port 4840`
**Students:** UaExpert → connect `opc.tcp://<central-ip>:4840/coefam/line1` → expand **Objects**.

**What they see:** a **flat list of tags** — `weight_g`, `temperature_c`, `order_produced`,
`kpi_oee`, … loose under Objects. No grouping, no units, no type beyond the raw value.

**Optional, in code:** `python opc_client_absorb.py --mode flat --url opc.tcp://<ip>:4840/coefam/line1`
→ prints a flat dict; point out the script carries a **hand-maintained list of 15 tag names**.

**Talking points**
- We changed the *transport* (now OPC UA, a proper industrial protocol) but kept the *model* flat.
- The integrator's job is still miserable: you must **know every tag name**, **hard-code what each means**, and **guess the unit** (is `weight_g` grams? is `temperature_c` °C or °F?).
- A rename, a new line, or a new value breaks every consumer. This is the reality in a lot of plants — a "tag soup."

**Discussion (3 min):** *"You're integrating this into MES. What do you have to document and maintain, forever, by hand?"*

---

## 4 · Demo: OPC UA as an information model / profile (20 min)

**Stop the flat server.**
**Run:** `python production_line_opc_profile.py --host 0.0.0.0 --port 4840`
**Students:** UaExpert → same URL → expand **Objects → Line1**, and **Types → ObjectTypes → ProductionLineType**.

**What they see now — same data, transformed:**
- `Line1` is organized into **Fill / Motor / Status / Order / Quality / KPI**.
- Every value has an explicit **data type** — `WeightGrams` is a `Double`, `Target` is an `Int32`, `State` is a `String`.
- Analog values carry an **engineering unit** — `WeightGrams [g]`, `Temperature [degC]`, `OEE [ratio]`.
- Under **Types**, there's a reusable **`ProductionLineType`** — the *profile/template*. `Line1` is an *instance* of it.

**In code — the payoff:**
```
python opc_client_absorb.py --mode profile --url opc.tcp://<ip>:4840/coefam/line1
```
It **discovers** every instance of `ProductionLineType`, walks the structure, and builds a
nested record carrying the **type and unit of every value — with no hard-coded tag list**.

**Talking points**
- Same line, same numbers — but now the **meaning travels with the data**: structure, type, unit, and a type definition are all *readable from the server*.
- A consumer can **discover** the model instead of being told the names. Add `Line2` (another instance of the type) and the same client absorbs it with **zero changes**.
- This is exactly the idea behind **CESMII SM Profiles / OPC UA companion specifications**: agree on a reusable type once, and every compliant system can consume any instance of it. ("Connect → **Contextualize** → Consume.")
- MES/ERP/QMS integration stops being a bespoke tag-mapping project and becomes "subscribe to instances of a known type."

---

## 5 · Hands-on activity (15 min)

Students work from their connected viewers (individually or in pairs).

**Part A — Map the data (both transports).** Complete the table:

| Value | MQTT topic | OPC profile path | Consumed by | Data type | Unit |
|---|---|---|---|---|---|
| Fill weight | `…/fill/weight_g` | `Line1/Fill/WeightGrams` | SCADA/Historian | Double | g |
| Parts produced | ? | ? | ? | ? | ? |
| Last quality result | ? | ? | ? | ? | ? |
| OEE | ? | ? | ? | ? | ? |

**Part B — Break it.** *On the flat server*, imagine `kpi_oee` is renamed to `oee_pct`.
List every place a consumer would break. *On the profile server*, what would a consumer
have to change to keep working? (Answer: little to nothing — it reads structure/type, not names.)

**Part C — Extend it (stretch).** In `line_model.py`, which one value would you add, and in
the **profile** server, which sub-object and data type would you give it so consumers absorb
it automatically?

---

## 6 · Debrief & tie-back (10 min)

**Pull the thread together:**
- **Transport ≠ model.** OPC UA didn't fix integration by itself — the *flat* OPC server was just as painful as MQTT-by-topic-name. The fix was the **information model**.
- **Flat tags:** meaning lives in names and tribal knowledge; every consumer hand-maps; renames and new lines break things.
- **Profile / information model:** meaning lives *in the data* — structure, data type, unit, reusable type. Consumers **discover and absorb** generically; it scales to many lines and vendors.
- **Course tie-in:** this is the concrete version of Cert 02's SM Profiles, OPC-UA, and the Automation Pyramid, and of the "how MES/ERP/QMS absorb data" story. MQTT and OPC UA are both valid transports; the **model** is what makes the data usable.

**One-sentence takeaway:** *Getting the data out is easy; getting it out with its meaning attached — types, units, structure, a reusable profile — is what lets real systems absorb it.*

---

## Quick assessment (exit questions)

1. Name the four consuming systems and one value each would subscribe to.
2. In MQTT, where does the *meaning* of a value live? What breaks when a topic is renamed?
3. Give two things the **profile** OPC server tells a consumer that the **flat** server does not.
4. Why is "an instance of a reusable type" better for integration than "a list of tags"?
5. True/false: switching from MQTT to OPC UA automatically solves data integration. (False — you also need a model.)

## Answer key

1. SCADA/Historian←fill/motor/state; MES←order; QMS←quality; ERP←kpi. 2. In the topic name; every subscriber that hard-coded the name breaks. 3. Any two of: structure/grouping, data type, engineering unit, a discoverable reusable type definition. 4. A type can be discovered and reused across many instances/lines/vendors without re-mapping; a tag list must be hand-maintained per consumer. 5. False.
