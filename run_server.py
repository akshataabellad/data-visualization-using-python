"""
Root execution launcher for Sovereign Health & Capital Analytics
Starts FastAPI backend server with static UI mounting on port 8000.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
sys.path.insert(0, BACKEND_DIR)

import uvicorn
import data_generator

def main():
    print("=" * 70)
    print("  SOVEREIGN HEALTH & CAPITAL ANALYTICS - INSTITUTIONAL TERMINAL")
    print("  Data Source: DataBazaar Healthcare Panel (1980-2024, 226 Nations)")
    print("=" * 70)
    
    # Check if database exists, otherwise build it
    db_path = os.path.join(BASE_DIR, "data", "sovereign_health.db")
    if not os.path.exists(db_path):
        print("[INFO] Initializing SQLite database and 28-indicator panel dataset...")
        countries, records = data_generator.generate_panel_dataset()
        data_generator.save_to_csv_and_db(countries, records)
    else:
        print(f"[OK] Database validated at {db_path}")

    print("\n[OK] Launching Uvicorn ASGI Server on http://127.0.0.1:8000")
    print("[OK] Interactive OpenAPI documentation at http://127.0.0.1:8000/docs")
    print("[OK] Institutional Dashboard live at http://127.0.0.1:8000\n")

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False, app_dir=BACKEND_DIR)

if __name__ == "__main__":
    main()
