"""
FastAPI Backend Application for Sovereign Health & Capital Analytics
Provides institutional-grade REST telemetry and data streaming.
"""

import os
import io
import csv
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import database as db

app = FastAPI(
    title="Sovereign Health & Capital Analytics API",
    version="2.0.0",
    description="Institutional-grade macroeconomic healthcare API for sovereign financiers and policy advisors."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
CSV_PATH = os.path.join(DATA_DIR, "healthcare_infrastructure_disease_burden.csv")

@app.get("/api/health")
def health_check():
    return {"status": "ONLINE", "system": "Sovereign Health & Capital Analytics Engine"}

@app.get("/api/metadata")
def get_metadata():
    return db.get_metadata()

@app.get("/api/countries")
def get_countries():
    return db.get_all_countries()

@app.get("/api/macro-metrics")
def get_macro_kpis(
    iso_code: Optional[str] = Query("ALL", description="3-letter ISO country code or ALL"),
    region: Optional[str] = Query("ALL", description="Geographic region or ALL"),
    year: int = Query(2024, ge=1980, le=2024),
    currency: str = Query("USD", pattern="^(USD|INR)$")
):
    return db.get_macro_kpis(iso_code=iso_code, region=region, year=year, currency=currency)

@app.get("/api/timeseries")
def get_timeseries(
    iso_codes: str = Query("IND,USA,DEU,CHN", description="Comma-separated ISO codes"),
    indicators: str = Query("life_expectancy_years,health_expenditure_pct_gdp", description="Comma-separated indicators"),
    start_year: int = Query(1980, ge=1980, le=2024),
    end_year: int = Query(2024, ge=1980, le=2024)
):
    iso_list = [i.strip().upper() for i in iso_codes.split(",") if i.strip()]
    ind_list = [i.strip() for i in indicators.split(",") if i.strip()]
    return db.get_timeseries_data(iso_codes=iso_list, indicators=ind_list, start_year=start_year, end_year=end_year)

@app.get("/api/cross-country")
def get_cross_country(
    indicator: str = Query("health_resilience_score"),
    year: int = Query(2024, ge=1980, le=2024),
    region: Optional[str] = Query("ALL"),
    limit: int = Query(25, ge=5, le=100)
):
    return db.get_cross_country_comparison(indicator=indicator, year=year, region=region, limit=limit)

@app.get("/api/correlation")
def get_correlation(
    x_indicator: str = Query("health_expenditure_pct_gdp"),
    y_indicator: str = Query("life_expectancy_years"),
    year: int = Query(2024, ge=1980, le=2024),
    region: Optional[str] = Query("ALL")
):
    return db.get_correlation_data(x_indicator=x_indicator, y_indicator=y_indicator, year=year, region=region)

@app.get("/api/radar")
def get_radar(
    iso_codes: str = Query("IND,USA,JPN,DEU"),
    year: int = Query(2024, ge=1980, le=2024)
):
    iso_list = [i.strip().upper() for i in iso_codes.split(",") if i.strip()]
    return db.get_radar_comparison(iso_codes=iso_list, year=year)

@app.get("/api/grid")
def get_grid(
    search: str = Query("", description="Search country or ISO"),
    iso_code: str = Query("ALL", description="ISO country code or ALL"),
    region: str = Query("ALL"),
    income_group: str = Query("ALL"),
    year: int = Query(2024, ge=1980, le=2024),
    sort_by: str = Query("health_resilience_score"),
    sort_dir: str = Query("DESC"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=100)
):
    return db.get_grid_records(
        search=search,
        iso_code=iso_code,
        region=region,
        income_group=income_group,
        year=year,
        sort_by=sort_by,
        sort_dir=sort_dir,
        page=page,
        page_size=page_size
    )

@app.get("/api/export/csv")
def export_csv(
    year: Optional[int] = Query(None),
    region: Optional[str] = Query("ALL"),
    income_group: Optional[str] = Query("ALL"),
    iso_code: Optional[str] = Query("ALL"),
    search: str = Query("")
):
    if not os.path.exists(CSV_PATH):
        raise HTTPException(status_code=404, detail="CSV file not found")
        
    conn = db.get_connection()
    cur = conn.cursor()
    
    query = "SELECT * FROM indicators"
    params = []
    clauses = []
    if year:
        clauses.append("year = ?")
        params.append(year)
    if region and region != "ALL":
        clauses.append("region = ?")
        params.append(region)
    if income_group and income_group != "ALL":
        clauses.append("iso_code IN (SELECT iso_code FROM countries WHERE income_group = ?)")
        params.append(income_group)
    if iso_code and iso_code.upper() != "ALL":
        clauses.append("iso_code = ?")
        params.append(iso_code.strip().upper())
    if search.strip():
        clauses.append("(country LIKE ? OR iso_code LIKE ?)")
        params.extend([f"%{search.strip()}%", f"%{search.strip()}%"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY country ASC, year ASC"
    
    cur.execute(query, params)
    rows = cur.fetchall()
    
    if not rows:
        conn.close()
        raise HTTPException(status_code=404, detail="No matching data found")
        
    col_names = [d[0] for d in cur.description]
    
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(col_names)
    for r in rows:
        writer.writerow(list(r))
        
    conn.close()
    stream.seek(0)
    
    filename = f"healthcare_panel_{year or 'all_years'}.csv"
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# Static and SPA mounting
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/styles.css")
def serve_css():
    return FileResponse(os.path.join(FRONTEND_DIR, "styles.css"))

@app.get("/app.js")
def serve_js():
    return FileResponse(os.path.join(FRONTEND_DIR, "app.js"))

@app.get("/")
def serve_spa():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Sovereign Health & Capital Analytics API operational. Frontend under compilation."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
