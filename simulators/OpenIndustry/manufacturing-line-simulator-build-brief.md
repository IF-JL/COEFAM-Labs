# Manufacturing Line Simulator — Build Brief for Claude Code

## Purpose

Build a teaching tool for a training package: a visual manufacturing line simulation that
students can watch run in real time, that emits live data streams as it operates, and that
feeds those streams into an MES-style dashboard/system — so students see the full path from
physical line → data → manufacturing intelligence layer, mirroring how real industrial
platforms (e.g. ThinkIQ) are architected.

This is a training/education tool, not a production deployment. Prioritize clarity,
runnability, and "students can see it working in under 5 minutes" over completeness or
industrial hardening.

## Goals (in priority order)

1. A student can open the project and watch a manufacturing line visually run — parts moving
   down a conveyor, through stations, with visible state changes (machine busy/idle/down,
   part counts, etc).
2. The line emits a live data stream (tags/telemetry) as it runs — e.g. cycle counts,
   machine status, throughput, simulated sensor values (temperature, vibration, etc).
3. That data stream is visible somewhere outside the simulator itself — a dashboard — so
   students see "the line moved, and here is the data that resulted."
4. That data optionally lands in a lightweight MES-style layer (work order / production
   tracking) so students see data becoming operational information, not just numbers on
   a chart.
5. The whole thing runs locally, for free, with a reasonable setup process a non-engineer
   instructor could eventually follow (docker-compose ideally).

## Recommended architecture

```
[Godot simulation]  --tags/telemetry-->  [MQTT broker (Mosquitto)]
                                              |
                                              v
                                     [InfluxDB (time series)]
                                              |
                                              v
                                     [Grafana (dashboard)]
                                              |
                                              v
                              [Lightweight MES layer (optional, phase 3)]
```

### Why this stack
- **Godot** — free, open-source, good 2D/3D visualization, scriptable in GDScript or C#.
  Reference project: `Open-Industry-Project/Open-Industry-Project` on GitHub — a free,
  open-source warehouse/manufacturing simulator built on Godot that already models
  conveyors, sensors, and PLC/OPC UA tag communication. Use it as a structural reference
  or literal starting point rather than building line physics from scratch.
- **MQTT (Mosquitto)** — simplest possible way to get the simulator emitting a real data
  stream. Much faster to stand up than OPC UA for a teaching tool; still an authentic
  industrial protocol students will recognize.
- **InfluxDB** — free tier, purpose-built for time-series telemetry, pairs natively with
  Grafana.
- **Grafana** — free, gives students an immediate "here's the dashboard" payoff with
  minimal config.
- **MES layer** — start minimal (a simple web app or even a Grafana panel showing
  work-order-style state: part counts against a target, current "job" running) rather than
  standing up a full MES product. Can point to OpenMES later if a fuller MES experience is
  wanted in a later phase.

## Suggested build phases (so Claude Code can build incrementally and you can review at
each stage)

### Phase 1 — Visual line only
- Godot project with a simple line: 1 source (part spawner) → 2-3 stations → 1 sink.
- Parts visibly move along conveyors at a configurable speed.
- Each station has a visible state: idle / processing / down (color-coded).
- Simple manual controls: start/stop/reset, and a way to trigger a fault at a station.
- Deliverable: runnable Godot project, no external dependencies yet.

### Phase 2 — Data stream
- Add MQTT client to the Godot sim (or a lightweight bridge process alongside it).
- Publish telemetry per station: status, cycle count, cycle time, simulated sensor value.
- docker-compose for Mosquitto + InfluxDB + Grafana.
- A Telegraf config or small script subscribing to MQTT and writing to InfluxDB.
- Pre-built Grafana dashboard: line throughput, station status, OEE-style simple metric.
- Deliverable: `docker-compose up` brings up the full data pipeline; running the sim
  populates the dashboard live.

### Phase 3 — MES layer (optional / stretch)
- Minimal web app (or Grafana-based) showing: current work order, target vs actual count,
  simple downtime log pulled from station "down" events.
- This is where the "integrates into MES" teaching point lands — data becoming an
  operational view, not just a chart.

## Repo structure (suggested)

```
mfg-line-simulator/
├── README.md                 # setup + how to run, aimed at an instructor
├── docker-compose.yml        # mosquitto + influxdb + grafana (+ mes later)
├── sim/                      # Godot project
│   ├── project.godot
│   └── scenes/scripts...
├── bridge/                   # MQTT -> InfluxDB glue if not using Telegraf
├── dashboards/                # Grafana dashboard JSON exports
├── mes/                       # phase 3 minimal MES app
└── docs/
    └── architecture.md
```

## Notes / constraints for Claude Code

- Keep everything free/open-source — no paid SaaS dependencies.
- Favor docker-compose for anything that isn't the Godot app itself, so setup is one command.
- Keep MQTT topic/tag naming clean and documented in README — this will double as a teaching
  reference for students (e.g. `line1/station2/status`, `line1/station2/cycle_count`).
- Build Phase 1 fully runnable and reviewable before starting Phase 2; same for 2 → 3.
- This will be used in a training package, so inline comments in the Godot scripts and a
  short "how this works" doc per phase are valuable — treat some documentation as a
  deliverable, not just the code.

## Open decisions to confirm with the instructor (me) before/during build

- Line complexity for Phase 1: how many stations, single line or a simple branch?
- 2D top-down visualization vs. 3D — 2D is faster to build and likely clearer for training
  purposes.
- Whether Phase 3 MES layer is in scope for the first pass or a later iteration.
