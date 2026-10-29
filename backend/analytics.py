"""
Analytics and Financial Econometric Engine for Sovereign Health & Capital Analytics
Implements calculations for:
- Currency conversions (USD <-> INR)
- Out-of-pocket expenditure (OOPE) distress triggers
- Health Economic Resilience Index
- Macroeconomic correlation matrices
- Regional weighted aggregations
"""

import math
import numpy as np

USD_TO_INR_RATE = 84.25

def convert_currency(usd_value, target_currency="USD"):
    if usd_value is None:
        return 0.0
    if target_currency.upper() == "INR":
        return round(usd_value * USD_TO_INR_RATE, 2)
    return round(usd_value, 2)

def calculate_oope_status(oope_pct):
    if oope_pct < 20.0:
        return {
            "tier": "Resilient / Universal Shield",
            "code": "LOW",
            "color": "#4e6dea",
            "is_distress": False,
            "badge_class": "badge-resilience"
        }
    elif oope_pct < 35.0:
        return {
            "tier": "Moderate Outlay Exposure",
            "code": "MODERATE",
            "color": "#6a74a7",
            "is_distress": False,
            "badge_class": "badge-gdp"
        }
    elif oope_pct < 50.0:
        return {
            "tier": "Elevated Household Strain",
            "code": "ELEVATED",
            "color": "#ea6941",
            "is_distress": True,
            "badge_class": "badge-liquidity"
        }
    else:
        return {
            "tier": "Severe Catastrophic Distress",
            "code": "CRITICAL_DEFICIT",
            "color": "#ffb4ab",
            "is_distress": True,
            "badge_class": "badge-deficit"
        }

def compute_correlation(x_vals, y_vals):
    if len(x_vals) < 3 or len(y_vals) < 3:
        return 0.0
    x = np.array(x_vals, dtype=float)
    y = np.array(y_vals, dtype=float)
    
    # Filter non-finite
    mask = np.isfinite(x) & np.isfinite(y)
    if np.sum(mask) < 3:
        return 0.0
    
    x = x[mask]
    y = y[mask]
    std_x = np.std(x)
    std_y = np.std(y)
    if std_x == 0 or std_y == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])
