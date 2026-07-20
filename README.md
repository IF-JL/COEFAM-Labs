# COEFAM — Smart Manufacturing Labs

Runnable Jupyter labs for the IntelleX Fabrica Smart Manufacturing certificate program.
Everything runs free in **Google Colab** — no local install.

## Start here → the Lab Hub

Open **`index.ipynb`** in Colab. It renders an organized catalog of every lab with an
**Open in Colab** button per lab, grouped by certificate. Share the Hub's Colab link with students.

> First time: open `index.ipynb`, set `GH_USER` / `GH_REPO` in the first code cell, run both cells.

[![Open the Lab Hub in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/IF-JL/COEFAM-Labs/blob/main/index.ipynb)

## Structure

```
COEFAM-Labs/
├─ index.ipynb                 # ← the Lab Hub (table of contents)
├─ _template/lab_template.ipynb# copy this to start a new lab
└─ labs/
   ├─ cert01_intro_iiot/
   ├─ cert02_integrated_systems/
   ├─ cert03_auto_id/          # i3x_api_intro.ipynb lives here
   ├─ cert04_data_analytics/
   └─ cert05_smart_factory/
```

## Add a lab

1. Copy `_template/lab_template.ipynb` into the right `labs/<cert>/` folder and build it.
2. Add one row to the `CATALOG` list in `index.ipynb`.
3. Commit & push. The Hub picks it up automatically.

## How students run a lab

Click **Open in Colab** on the Hub → **File → Save a copy in Drive** → run the cells.
Their copy is theirs; the repo version stays clean.

## Publishing (one time)

1. Create a **public** GitHub repo named `COEFAM-Labs` under the `IF-JL` account.
2. Push this folder (`git push`), or drag-and-drop upload its contents.
3. `GH_USER`/`GH_REPO` are already set in `index.ipynb` — nothing else to change.
