"""
Database access layer for Sovereign Health & Capital Analytics
Provides high-performance queries on the 10,170-row panel dataset.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "sovereign_health.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_all_countries() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT iso_code, country, region, income_group, population_2024,
           latest_life_exp, latest_health_exp_gdp, latest_oope, latest_uhc
    FROM countries
    ORDER BY country ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_metadata() -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(DISTINCT iso_code) as countries, COUNT(*) as records, MIN(year) as min_y, MAX(year) as max_y FROM indicators")
    row = dict(cur.fetchone())
    
    cur.execute("SELECT DISTINCT region FROM countries ORDER BY region ASC")
    regions = [r[0] for r in cur.fetchall()]
    
    cur.execute("SELECT DISTINCT income_group FROM countries ORDER BY income_group ASC")
    incomes = [r[0] for r in cur.fetchall()]
    
    conn.close()
    return {
        "title": "Healthcare Infrastructure & Disease Burden",
        "total_countries": row["countries"],
        "total_records": row["records"],
        "min_year": row["min_y"],
        "max_year": row["max_y"],
        "regions": regions,
        "income_groups": incomes,
        "dataset_source": "Synthesized from WHO Global Health Observatory, World Bank, UNICEF, UNAIDS, UN Population Division (DataBazaar Healthcare Category)"
    }

def get_macro_kpis(iso_code: Optional[str] = None, region: Optional[str] = None, year: int = 2024, currency: str = "USD") -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        AVG(health_resilience_score) as avg_resilience,
        AVG(health_expenditure_pct_gdp) as avg_exp_gdp,
        AVG(health_expenditure_per_capita_usd) as avg_exp_pc,
        AVG(out_of_pocket_expenditure_pct) as avg_oope,
        AVG(life_expectancy_years) as avg_life_exp,
        AVG(uhc_service_coverage_index) as avg_uhc,
        AVG(physicians_per_1000) as avg_phys,
        AVG(hospital_beds_per_1000) as avg_beds,
        AVG(infant_mortality_per_1000) as avg_infant_mort,
        SUM(oope_distress_alert) as total_distress_count,
        COUNT(*) as entity_count
    FROM indicators
    WHERE year = ?
    """
    params = [year]
    
    if iso_code and iso_code != "ALL":
        query += " AND iso_code = ?"
        params.append(iso_code)
    if region and region != "ALL":
        query += " AND region = ?"
        params.append(region)
        
    cur.execute(query, params)
    current = dict(cur.fetchone())
    
    # Previous comparison point (5 years prior: year - 5, e.g., 2019 vs 2024)
    prev_year = max(1980, year - 5)
    params_prev = [prev_year]
    query_prev = query.replace("WHERE year = ?", "WHERE year = ?", 1)
    cur.execute(query_prev, params_prev + params[1:])
    prev = dict(cur.fetchone())
    
    # Sparkline history for last 10 years
    spark_query = """
    SELECT year, 
           AVG(health_resilience_score) as resilience,
           AVG(health_expenditure_pct_gdp) as exp_gdp,
           AVG(health_expenditure_per_capita_usd) as exp_pc,
           AVG(out_of_pocket_expenditure_pct) as oope,
           AVG(life_expectancy_years) as life_exp,
           AVG(physicians_per_1000) as phys
    FROM indicators
    WHERE year BETWEEN ? AND ?
    """
    spark_params = [max(1980, year - 10), year]
    if iso_code and iso_code != "ALL":
        spark_query += " AND iso_code = ?"
        spark_params.append(iso_code)
    if region and region != "ALL":
        spark_query += " AND region = ?"
        spark_params.append(region)
    spark_query += " GROUP BY year ORDER BY year ASC"
    
    cur.execute(spark_query, spark_params)
    spark_rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    # Currency conversion for per-capita metric
    multiplier = 84.25 if currency.upper() == "INR" else 1.0
    curr_symbol = "₹" if currency.upper() == "INR" else "$"
    
    curr_pc = (current["avg_exp_pc"] or 0) * multiplier
    prev_pc = (prev["avg_exp_pc"] or 0) * multiplier
    
    def calc_delta(curr, old):
        if not old or old == 0:
            return 0.0
        return round(((curr - old) / old) * 100, 2)
        
    return {
        "year": year,
        "compare_year": prev_year,
        "currency": currency.upper(),
        "currency_symbol": curr_symbol,
        "entity_count": current.get("entity_count", 0),
        "cards": [
            {
                "id": "resilience",
                "label": "HEALTH CAPITAL & RESILIENCE INDEX",
                "taxonomy": "SOVEREIGN ROI",
                "value": round(current.get("avg_resilience") or 0, 1),
                "unit": "PTS / 100",
                "delta": calc_delta(current.get("avg_resilience") or 0, prev.get("avg_resilience") or 0),
                "delta_label": "vs 5y Prior",
                "semantic": "resilience",
                "sparkline": [round(s["resilience"], 1) for s in spark_rows]
            },
            {
                "id": "exp_gdp",
                "label": "FISCAL CONTRIBUTION / CAPEX",
                "taxonomy": "GVA & OUTLAY",
                "value": round(current.get("avg_exp_gdp") or 0, 2),
                "unit": "% OF GDP",
                "delta": calc_delta(current.get("avg_exp_gdp") or 0, prev.get("avg_exp_gdp") or 0),
                "delta_label": "vs 5y Prior",
                "semantic": "gdp",
                "sparkline": [round(s["exp_gdp"], 2) for s in spark_rows]
            },
            {
                "id": "exp_pc",
                "label": "ANNUAL HEALTH CAPITAL OUTLAY",
                "taxonomy": "PER CAPITA",
                "value": round(curr_pc, 1),
                "unit": f"{curr_symbol} / CAPITA",
                "delta": calc_delta(curr_pc, prev_pc),
                "delta_label": "vs 5y Prior",
                "semantic": "gdp",
                "sparkline": [round(s["exp_pc"] * multiplier, 1) for s in spark_rows]
            },
            {
                "id": "oope",
                "label": "OUT-OF-POCKET EXPENDITURE (OOPE)",
                "taxonomy": "DISTRESS TRIGGER",
                "value": round(current.get("avg_oope") or 0, 1),
                "unit": "% OF HEALTH EXP",
                "delta": calc_delta(current.get("avg_oope") or 0, prev.get("avg_oope") or 0),
                "delta_label": "vs 5y Prior",
                "semantic": "deficit" if (current.get("avg_oope") or 0) > 35 else "resilience",
                "sparkline": [round(s["oope"], 1) for s in spark_rows]
            },
            {
                "id": "life_exp",
                "label": "SOVEREIGN LIFE EXPECTANCY",
                "taxonomy": "DEMOGRAPHIC RETENTION",
                "value": round(current.get("avg_life_exp") or 0, 1),
                "unit": "YEARS",
                "delta": calc_delta(current.get("avg_life_exp") or 0, prev.get("avg_life_exp") or 0),
                "delta_label": "vs 5y Prior",
                "semantic": "resilience",
                "sparkline": [round(s["life_exp"], 1) for s in spark_rows]
            },
            {
                "id": "workforce",
                "label": "PHYSICIAN DENSITY MATRIX",
                "taxonomy": "INFRASTRUCTURE",
                "value": round(current.get("avg_phys") or 0, 2),
                "unit": "PER 1K POPULATION",
                "delta": calc_delta(current.get("avg_phys") or 0, prev.get("avg_phys") or 0),
                "delta_label": "vs 5y Prior",
                "semantic": "resilience",
                "sparkline": [round(s["phys"], 2) for s in spark_rows]
            }
        ]
    }

def get_timeseries_data(
    iso_codes: List[str],
    indicators: List[str],
    start_year: int = 1980,
    end_year: int = 2024
) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    
    valid_indicators = [
        "life_expectancy_years", "health_expenditure_pct_gdp",
        "health_expenditure_per_capita_usd", "out_of_pocket_expenditure_pct",
        "physicians_per_1000", "hospital_beds_per_1000", "infant_mortality_per_1000",
        "uhc_service_coverage_index", "health_resilience_score", "tb_incidence_per_100k",
        "hiv_prevalence_pct", "clean_water_access_pct"
    ]
    
    clean_inds = [i for i in indicators if i in valid_indicators]
    if not clean_inds:
        clean_inds = ["life_expectancy_years", "health_expenditure_pct_gdp"]
        
    select_fields = ", ".join(clean_inds)
    
    placeholders = ",".join(["?"] * len(iso_codes))
    query = f"""
    SELECT iso_code, country, year, {select_fields}
    FROM indicators
    WHERE iso_code IN ({placeholders}) AND year BETWEEN ? AND ?
    ORDER BY iso_code ASC, year ASC
    """
    params = list(iso_codes) + [start_year, end_year]
    cur.execute(query, params)
    
    rows = cur.fetchall()
    conn.close()
    
    # Structure by iso_code
    series_map = {}
    for r in rows:
        iso = r["iso_code"]
        country = r["country"]
        if iso not in series_map:
            series_map[iso] = {
                "iso_code": iso,
                "country": country,
                "years": [],
                "data": {ind: [] for ind in clean_inds}
            }
        series_map[iso]["years"].append(r["year"])
        for ind in clean_inds:
            series_map[iso]["data"][ind].append(r[ind])
            
    return {
        "indicators": clean_inds,
        "start_year": start_year,
        "end_year": end_year,
        "series": list(series_map.values())
    }

def get_cross_country_comparison(indicator: str, year: int = 2024, region: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    
    valid_indicators = [
        "life_expectancy_years", "health_expenditure_pct_gdp",
        "health_expenditure_per_capita_usd", "out_of_pocket_expenditure_pct",
        "physicians_per_1000", "hospital_beds_per_1000", "infant_mortality_per_1000",
        "uhc_service_coverage_index", "health_resilience_score", "tb_incidence_per_100k",
        "ncd_mortality_pct_30_70", "dpt_immunization_pct"
    ]
    if indicator not in valid_indicators:
        indicator = "health_resilience_score"
        
    query = f"""
    SELECT i.iso_code, i.country, i.region, c.income_group, c.population_2024, i.{indicator} as val,
           i.out_of_pocket_expenditure_pct as oope, i.health_resilience_score as resilience
    FROM indicators i
    JOIN countries c ON i.iso_code = c.iso_code
    WHERE i.year = ?
    """
    params = [year]
    if region and region != "ALL":
        query += " AND i.region = ?"
        params.append(region)
        
    query += f" ORDER BY i.{indicator} DESC LIMIT ?"
    params.append(limit)
    
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_correlation_data(x_indicator: str, y_indicator: str, year: int = 2024, region: Optional[str] = None) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    
    valid_indicators = [
        "life_expectancy_years", "health_expenditure_pct_gdp",
        "health_expenditure_per_capita_usd", "out_of_pocket_expenditure_pct",
        "physicians_per_1000", "hospital_beds_per_1000", "infant_mortality_per_1000",
        "uhc_service_coverage_index", "health_resilience_score", "clean_water_access_pct",
        "ncd_mortality_pct_30_70", "diabetes_prevalence_pct"
    ]
    if x_indicator not in valid_indicators:
        x_indicator = "health_expenditure_pct_gdp"
    if y_indicator not in valid_indicators:
        y_indicator = "life_expectancy_years"
        
    query = f"""
    SELECT i.iso_code, i.country, i.region, c.income_group, c.population_2024,
           i.{x_indicator} as x, i.{y_indicator} as y,
           i.health_resilience_score as resilience, i.out_of_pocket_expenditure_pct as oope
    FROM indicators i
    JOIN countries c ON i.iso_code = c.iso_code
    WHERE i.year = ?
    """
    params = [year]
    if region and region != "ALL":
        query += " AND i.region = ?"
        params.append(region)
        
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    x_vals = [r["x"] for r in rows if r["x"] is not None and r["y"] is not None]
    y_vals = [r["y"] for r in rows if r["x"] is not None and r["y"] is not None]
    
    from analytics import compute_correlation
    r_val = compute_correlation(x_vals, y_vals)
    
    return {
        "x_indicator": x_indicator,
        "y_indicator": y_indicator,
        "year": year,
        "pearson_r": round(r_val, 3),
        "r_squared": round(r_val ** 2, 3),
        "points": rows
    }

def get_radar_comparison(iso_codes: List[str], year: int = 2024) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    
    placeholders = ",".join(["?"] * len(iso_codes))
    query = f"""
    SELECT iso_code, country,
           uhc_service_coverage_index,
           (physicians_per_1000 * 20.0) as phys_scaled,
           (hospital_beds_per_1000 * 10.0) as beds_scaled,
           (life_expectancy_years / 85.0 * 100.0) as life_scaled,
           (100.0 - out_of_pocket_expenditure_pct) as fin_protection,
           dpt_immunization_pct,
           clean_water_access_pct,
           (100.0 - infant_mortality_per_1000 * 1.5) as child_survival
    FROM indicators
    WHERE iso_code IN ({placeholders}) AND year = ?
    """
    params = list(iso_codes) + [year]
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    radar_labels = [
        "UHC Coverage Index",
        "Workforce Density",
        "Bed Capacity",
        "Longevity Index",
        "Financial Protection (100 - OOPE)",
        "Immunization Shield",
        "Clean Water Access",
        "Child Survival Baseline"
    ]
    
    series = []
    for r in rows:
        series.append({
            "iso_code": r["iso_code"],
            "country": r["country"],
            "scores": [
                round(min(100.0, max(0.0, r["uhc_service_coverage_index"] or 0)), 1),
                round(min(100.0, max(0.0, r["phys_scaled"] or 0)), 1),
                round(min(100.0, max(0.0, r["beds_scaled"] or 0)), 1),
                round(min(100.0, max(0.0, r["life_scaled"] or 0)), 1),
                round(min(100.0, max(0.0, r["fin_protection"] or 0)), 1),
                round(min(100.0, max(0.0, r["dpt_immunization_pct"] or 0)), 1),
                round(min(100.0, max(0.0, r["clean_water_access_pct"] or 0)), 1),
                round(min(100.0, max(0.0, r["child_survival"] or 0)), 1)
            ]
        })
        
    return {
        "labels": radar_labels,
        "year": year,
        "series": series
    }

def get_grid_records(
    search: str = "",
    iso_code: str = "ALL",
    region: str = "ALL",
    income_group: str = "ALL",
    year: int = 2024,
    sort_by: str = "health_resilience_score",
    sort_dir: str = "DESC",
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    
    where_clauses = ["i.year = ?"]
    params = [year]

    if iso_code and iso_code.upper() != "ALL":
        where_clauses.append("i.iso_code = ?")
        params.append(iso_code.strip().upper())
    
    if search:
        where_clauses.append("(i.country LIKE ? OR i.iso_code LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if region and region != "ALL":
        where_clauses.append("i.region = ?")
        params.append(region)
    if income_group and income_group != "ALL":
        where_clauses.append("c.income_group = ?")
        params.append(income_group)
        
    where_sql = " AND ".join(where_clauses)
    
    # Count total
    count_sql = f"SELECT COUNT(*) FROM indicators i JOIN countries c ON i.iso_code = c.iso_code WHERE {where_sql}"
    cur.execute(count_sql, params)
    total_count = cur.fetchone()[0]
    
    # Whitelist sort column to prevent SQL injection
    sort_columns = {
        "iso_code": "i.iso_code", "country": "i.country", "region": "i.region",
        "income_group": "c.income_group", "year": "i.year",
        "life_expectancy_years": "i.life_expectancy_years",
        "infant_mortality_per_1000": "i.infant_mortality_per_1000",
        "physicians_per_1000": "i.physicians_per_1000",
        "hospital_beds_per_1000": "i.hospital_beds_per_1000",
        "health_expenditure_pct_gdp": "i.health_expenditure_pct_gdp",
        "health_expenditure_per_capita_usd": "i.health_expenditure_per_capita_usd",
        "out_of_pocket_expenditure_pct": "i.out_of_pocket_expenditure_pct",
        "uhc_service_coverage_index": "i.uhc_service_coverage_index",
        "health_resilience_score": "i.health_resilience_score"
    }
    sort_expression = sort_columns.get(sort_by, "i.health_resilience_score")
        
    direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"
    
    total_pages = (total_count + page_size - 1) // page_size
    page = min(page, max(total_pages, 1))
    offset = (page - 1) * page_size
    
    data_sql = f"""
    SELECT i.iso_code, i.country, i.region, c.income_group, i.year,
           i.life_expectancy_years, i.infant_mortality_per_1000,
           i.physicians_per_1000, i.hospital_beds_per_1000,
           i.health_expenditure_pct_gdp, i.health_expenditure_per_capita_usd,
           i.out_of_pocket_expenditure_pct, i.uhc_service_coverage_index,
           i.health_resilience_score, i.oope_distress_alert
    FROM indicators i
    JOIN countries c ON i.iso_code = c.iso_code
    WHERE {where_sql}
    ORDER BY {sort_expression} {direction}, i.country ASC
    LIMIT ? OFFSET ?
    """
    cur.execute(data_sql, params + [page_size, offset])
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    return {
        "page": page,
        "page_size": page_size,
        "total": total_count,
        "total_pages": total_pages,
        "records": rows
    }
