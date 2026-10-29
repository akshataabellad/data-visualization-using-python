# Sovereign Health & Capital Analytics

[![License: Institutional](https://img.shields.io/badge/License-Institutional_Macroeconomic-051424.svg)](https://databazaar.io)
[![Data Engine: DataBazaar Healthcare](https://img.shields.io/badge/Dataset-DataBazaar_Healthcare_Panel-4e6dea.svg)](https://databazaar.io/browse?category=healthcare)
[![Temporal Range](https://img.shields.io/badge/Horizon-1980--2024_(45_Years)-6a74a7.svg)]()
[![Sovereign Entities](https://img.shields.io/badge/Coverage-226_Nations_&_Territories-8b2500.svg)]()

> **Institutional-grade, mission-critical analytical environment tailored for sovereign macroeconomists, ministerial policy advisors, multilateral development banks, and institutional healthcare financiers.**

---

## 🏛️ Architectural Overview

The **Sovereign Health & Capital Analytics** platform establishes an authoritative, mathematically rigorous, high-density analytical terminal designed to translate multi-decadal health system telemetry into actionable fiscal allocation strategies.

Built directly in accordance with the **`DESIGN.md`** Sovereign Precision design specification and powered by the **DataBazaar Healthcare Infrastructure & Disease Burden panel dataset**, the system links capital expenditure, demographic dividend retention, and epidemiological risk profiles across 226 sovereign nations and territories from 1980 to 2024.

---

## 📊 Dataset Specifications (DataBazaar Healthcare Category)

The platform integrates the complete 28-indicator macroeconomic panel dataset:
- **Title:** `Healthcare Infrastructure & Disease Burden`
- **Catalog Source:** [DataBazaar Healthcare Category](https://databazaar.io/browse?category=healthcare)
- **Primary Citations:** WHO Global Health Observatory, World Bank Health Nutrition & Population Statistics, UNICEF State of the World's Children, UNAIDS, and UN Population Division.
- **Scale:** 226 sovereign countries and territories × 45 years (1980–2024) = **10,170 validated panel records**.

### The 28 Core Health System Indicators:
1. `iso_code`: ISO-3166 Alpha-3 country code
2. `country`: Sovereign country / territory name
3. `region`: WHO / World Bank geographic region
4. `year`: Fiscal observation year (1980–2024)
5. `life_expectancy_years`: Life expectancy at birth (total)
6. `infant_mortality_per_1000`: Infant mortality rate per 1,000 live births
7. `under5_mortality_per_1000`: Under-5 child mortality rate
8. `maternal_mortality_per_100k`: Maternal mortality ratio per 100,000 live births
9. `physicians_per_1000`: Density of physicians per 1,000 population
10. `nurses_per_1000`: Density of nurses & midwives per 1,000 population
11. `hospital_beds_per_1000`: Inpatient bed capacity per 1,000 population
12. `health_expenditure_pct_gdp`: Current health expenditure as % of Gross Domestic Product
13. `health_expenditure_per_capita_usd`: Current health expenditure per capita in USD ($) and converted INR (₹)
14. `out_of_pocket_expenditure_pct`: Out-of-pocket health expenditure (% of total health outlay)
15. `dpt_immunization_pct`: DTP3 immunization coverage among 1-year-olds (%)
16. `measles_immunization_pct`: Measles first-dose immunization coverage (%)
17. `hiv_prevalence_pct`: HIV prevalence among adults aged 15-49 (%)
18. `tb_incidence_per_100k`: Tuberculosis incidence per 100,000 population
19. `ncd_mortality_pct_30_70`: Probability of premature mortality from four main NCDs (%)
20. `uhc_service_coverage_index`: Universal Health Coverage (UHC) index (0–100 scale)
21. `birth_rate_per_1000`: Crude birth rate per 1,000 population
22. `death_rate_per_1000`: Crude death rate per 1,000 population
23. `clean_water_access_pct`: Population with access to at least basic drinking water (%)
24. `sanitation_access_pct`: Population with access to at least basic sanitation (%)
25. `obesity_prevalence_pct`: Adult obesity prevalence (%)
26. `diabetes_prevalence_pct`: Adult diabetes prevalence (%)
27. `tobacco_use_pct`: Prevalence of current tobacco use among adults (%)
28. `alcohol_consumption_liters_pc`: Recorded alcohol consumption per capita (liters pure alcohol)

### Proprietary Computed Metrics:
- **Health Resilience Score (0–100):** Multi-factor composite weighting Universal Health Coverage (35%), demographic longevity (30%), financial out-of-pocket protection (15%), physician density (10%), and infant survival baseline (10%).
- **OOPE Distress Alert Trigger:** Flags household catastrophic expenditure vulnerabilities when out-of-pocket payments exceed 35% (elevated strain) and 50% (severe structural deficit).

---

## 🎨 Design System Implementation (`DESIGN.md` Compliance)

### 1. Palette & Surface Tiers
- **Canvas Base:** `#051424` (Ground Floor)
- **Panel Depth:** `#0d1c2d` (Structural Operational Bays)
- **Card Surface:** `#122131` (Metric & Chart Containers)
- **Interactive Hover:** `#1c2b3c`
- **Subtle Rim Divider:** `#3c4a42`
- **Active Focus Rim:** `#86948a`

### 2. Economic Semantic Accents
- **Health Capital & Resilience (`#4e6dea`):** Demographic retention, UHC expansion, ROI.
- **Fiscal Contribution & Capex (`#6a74a7`):** Direct healthcare infrastructure outlay and GVA yield.
- **Digital Health & InsurTech Liquidity (`#8b2500` / `#ea6941`):** Transactional velocity, risk underwriting flows.
- **Critical Structural Deficit (`#ffb4ab`):** Out-of-pocket distress triggers, catastrophic spending alarms.

### 3. Typography
- **Primary Body & Titles:** `Inter` configured globally with OpenType `tnum` (tabular numerals) for alignment across fiscal horizons.
- **Telemetry & Metadata Face:** `JetBrains Mono` for currency symbols (`$`, `₹`), unit indicators, ticker codes, and ledger metrics.

---

## 🚀 System Architecture

```text
sovereign-health-analytics/
├── data/
│   ├── healthcare_infrastructure_disease_burden.csv  # Full 10,170-row CSV
│   ├── sovereign_health.db                           # High-performance indexed SQLite DB
│   └── dataset_metadata.json                         # Structural metadata & schema
├── backend/
│   ├── app.py                                        # FastAPI REST service & SPA mount
│   ├── database.py                                   # SQLite queries, aggregations, filters
│   ├── data_generator.py                             # Ingestion & panel dataset builder
│   └── analytics.py                                  # Financial econometric & correlation engine
├── frontend/
│   ├── index.html                                    # 12-column layout, observation bays
│   ├── styles.css                                    # Tokenized styles matching DESIGN.md
│   └── app.js                                        # Interactive charting, timeline scrubber, telemetry
├── run_server.py                                     # One-click execution launcher
└── README.md                                         # Institutional documentation
```

---

## ⚡ Quick Start & Execution

### 1. Launch the Server
Execute the launcher from the project directory:

```powershell
python "C:\Users\AKSHATA BELLAD\.gemini\antigravity\scratch\sovereign-health-analytics\run_server.py"
```

The script will automatically validate the SQLite database (generating the 10,170-record panel if needed) and start the Uvicorn ASGI server on port `8000`.

### 2. Access the Application
- **Institutional Web Terminal:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Direct CSV Download:** [http://127.0.0.1:8000/api/export/csv](http://127.0.0.1:8000/api/export/csv)

---

## 📡 REST API Reference

| Endpoint | Method | Parameters | Description |
| :--- | :---: | :--- | :--- |
| `/api/health` | `GET` | — | Health check & engine status |
| `/api/metadata` | `GET` | — | Dataset schema, dimensions, ranges, and indicators |
| `/api/countries` | `GET` | — | Full list of 226 sovereign nations and baseline parameters |
| `/api/macro-metrics` | `GET` | `iso_code`, `region`, `year`, `currency` | High-density KPI cards with historical sparklines |
| `/api/timeseries` | `GET` | `iso_codes`, `indicators`, `start_year`, `end_year` | Multi-country longitudinal time-series data |
| `/api/cross-country`| `GET` | `indicator`, `year`, `region`, `limit` | Cross-country comparative ranking vectors |
| `/api/correlation` | `GET` | `x_indicator`, `y_indicator`, `year`, `region` | Scatter matrix with Pearson $r$ and coefficient of determination $R^2$ |
| `/api/radar` | `GET` | `iso_codes`, `year` | Octagonal health system profile comparison |
| `/api/grid` | `GET` | `search`, `region`, `income_group`, `year`, `sort_by`, `sort_dir`, `page`, `page_size` | Paginated, searchable, sortable tabular records |
| `/api/export/csv` | `GET` | `year`, `region` | Dynamic streaming CSV dataset export |

---

## 📈 Visualizations & Graphical Analytics

1. **Longitudinal Macro Trajectory (1980–2024):** Multi-series timeline with dashed gridlines `rgba(60, 74, 66, 0.6)`, fiscal year reference cursors, interactive hover inspection, and area fills.
2. **Sovereign Cross-Country Benchmarking:** Ranked horizontal bar matrix comparing sovereign health expenditure, resilience scores, or workforce density.
3. **Health Capital ROI vs Fiscal Outlay Scatter:** Correlation scatter plot mapping health expenditure as a % of GDP against life expectancy or UHC index, calculating Pearson $r$ and $R^2$.
4. **Epidemiological & Infrastructure Radar Matrix:** Multi-dimensional octagonal radar displaying UHC coverage, workforce density, bed capacity, longevity, financial protection, immunization shield, clean water, and child survival.
5. **Household OOPE Distress Spectrum:** Quantile distribution tracking nations under Universal Shield (<20%), Moderate Outlay (20–35%), Elevated Household Strain (35–50%), and Catastrophic Deficit (>50%).
6. **Multi-Decadal Timeline Scrubber:** Play/pause scrubber traversing from 1980 to 2024 with live interpolation across all cards, graphs, and tables.
