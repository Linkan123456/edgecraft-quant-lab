# EdgeCraft Quant Lab
## Master Architecture v1.0

---

# Vision

EdgeCraft Quant Lab ska utvecklas till en komplett plattform för kvantitativ strategiutveckling.

Systemet ska vara:

- Modulärt
- Skalbart
- Objektorienterat
- Plugin-baserat
- Återanvändbart
- AI-redo

Ingen modul ska känna till någon annan modul mer än genom definierade API:er.

---

# Grundprincip

UI

↓

Core

↓

Engine

↓

Strategies

↓

Data

All logik ska ligga i Engine.

Pages ska endast innehålla användargränssnitt.

---

# Projektstruktur

app.py

pages/

engine/

strategies/

data/

charts/

docs/

exports/

tests/

---

# Core

Core ansvarar för:

- Backtest
- Resultat
- Strategy Runner
- Registry
- Parameter Engine

Core ska aldrig innehålla någon strategi.

---

# Strategy Layer

Alla strategier implementerar samma interface.

Exempel:

Double Seven

IBS

Connors RSI

Walker

Patrick C

OOPS

Larry Williams

Fler strategier ska kunna läggas till utan att ändra övriga moduler.

---

# Research Layer

Research använder endast Core.

Research känner aldrig till en strategi.

Research ska kunna göra:

Parameter Sweep

Heatmaps

Robust Score

Parameter Ranking

Sensitivity Analysis

---

# Validation Layer

Walk Forward

Monte Carlo

Cross Validation

Out-of-Sample

Noise Test

Regime Test

---

# Scanner Layer

Market Scanner

Timeframe Scanner

Strategy Scanner

Portfolio Scanner

---

# AI Layer

AI Lab

AI Optimizer

AI Strategy Discovery

AI Pattern Mining

AI Risk Analysis

---

# Portfolio Layer

Portfolio Optimizer

Correlation

Capital Allocation

Risk Allocation

Position Sizing

---

# Reporting Layer

Charts

PDF

CSV

Excel

HTML Reports

---

# Plugin System

Alla moduler ska kunna läggas till utan att modifiera befintlig kod.

---

# Designprinciper

En modul

Ett ansvar

En väg in

En väg ut

Ingen duplicerad logik

All kommunikation sker genom Core.

---

# Målbild

EdgeCraft Quant Lab ska kunna användas för:

Backtest

Research

Walk Forward

Monte Carlo

Scanner

Portfolio

AI

Risk

Rapporter

utan att arkitekturen behöver ändras.