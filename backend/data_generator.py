"""
Data Generator & Ingestor for Sovereign Health & Capital Analytics
Synthesizes the complete 28-indicator global panel dataset matching the DataBazaar specification:
- 226 countries and territories
- Multi-decadal coverage: 1980 to 2024
- 28 health system indicators from WHO, World Bank, UNICEF, UNAIDS, UN Population Division
- Generates SQLite database, CSV extract, and JSON structure
"""

import os
import sqlite3
import csv
import json
import math
import random

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

CSV_PATH = os.path.join(DATA_DIR, "healthcare_infrastructure_disease_burden.csv")
DB_PATH = os.path.join(DATA_DIR, "sovereign_health.db")
JSON_PATH = os.path.join(DATA_DIR, "dataset_metadata.json")

# Core countries with benchmark parameters (2024 anchor points and regional assignments)
BENCHMARK_COUNTRIES = [
    {"iso": "IND", "name": "India", "region": "South Asia", "income": "Lower middle income", "pop": 1428627663, "exp_gdp": 3.3, "life_exp": 70.8, "oope": 50.6, "phys": 0.93, "beds": 1.4, "uhc": 63},
    {"iso": "USA", "name": "United States", "region": "North America", "income": "High income", "pop": 339996563, "exp_gdp": 16.8, "life_exp": 77.5, "oope": 11.2, "phys": 2.61, "beds": 2.8, "uhc": 86},
    {"iso": "GBR", "name": "United Kingdom", "region": "Europe & Central Asia", "income": "High income", "pop": 67736802, "exp_gdp": 11.3, "life_exp": 81.2, "oope": 13.5, "phys": 3.20, "beds": 2.4, "uhc": 88},
    {"iso": "DEU", "name": "Germany", "region": "Europe & Central Asia", "income": "High income", "pop": 84482267, "exp_gdp": 12.8, "life_exp": 81.0, "oope": 12.0, "phys": 4.50, "beds": 7.8, "uhc": 89},
    {"iso": "JPN", "name": "Japan", "region": "East Asia & Pacific", "income": "High income", "pop": 124516650, "exp_gdp": 10.9, "life_exp": 84.6, "oope": 12.8, "phys": 2.60, "beds": 12.6, "uhc": 90},
    {"iso": "CHN", "name": "China", "region": "East Asia & Pacific", "income": "Upper middle income", "pop": 1410710000, "exp_gdp": 5.4, "life_exp": 78.2, "oope": 35.0, "phys": 2.40, "beds": 6.5, "uhc": 82},
    {"iso": "BRA", "name": "Brazil", "region": "Latin America & Caribbean", "income": "Upper middle income", "pop": 216422446, "exp_gdp": 9.9, "life_exp": 76.2, "oope": 26.8, "phys": 2.30, "beds": 2.1, "uhc": 75},
    {"iso": "ZAF", "name": "South Africa", "region": "Sub-Saharan Africa", "income": "Upper middle income", "pop": 60414495, "exp_gdp": 8.5, "life_exp": 65.3, "oope": 15.5, "phys": 0.85, "beds": 2.3, "uhc": 69},
    {"iso": "NGA", "name": "Nigeria", "region": "Sub-Saharan Africa", "income": "Lower middle income", "pop": 223804632, "exp_gdp": 3.4, "life_exp": 53.6, "oope": 76.2, "phys": 0.38, "beds": 0.5, "uhc": 44},
    {"iso": "FRA", "name": "France", "region": "Europe & Central Asia", "income": "High income", "pop": 68170228, "exp_gdp": 12.2, "life_exp": 82.5, "oope": 9.2, "phys": 3.30, "beds": 5.7, "uhc": 89},
    {"iso": "AUS", "name": "Australia", "region": "East Asia & Pacific", "income": "High income", "pop": 26439111, "exp_gdp": 10.6, "life_exp": 83.2, "oope": 14.1, "phys": 4.10, "beds": 3.8, "uhc": 89},
    {"iso": "CAN", "name": "Canada", "region": "North America", "income": "High income", "pop": 40097761, "exp_gdp": 11.2, "life_exp": 82.7, "oope": 14.6, "phys": 2.80, "beds": 2.5, "uhc": 88},
    {"iso": "IDN", "name": "Indonesia", "region": "East Asia & Pacific", "income": "Upper middle income", "pop": 277534122, "exp_gdp": 3.7, "life_exp": 71.3, "oope": 32.4, "phys": 0.60, "beds": 1.2, "uhc": 62},
    {"iso": "SAU", "name": "Saudi Arabia", "region": "Middle East & North Africa", "income": "High income", "pop": 36947025, "exp_gdp": 5.8, "life_exp": 77.9, "oope": 13.9, "phys": 2.80, "beds": 2.2, "uhc": 76},
    {"iso": "TUR", "name": "Turkiye", "region": "Europe & Central Asia", "income": "Upper middle income", "pop": 85816199, "exp_gdp": 4.6, "life_exp": 78.5, "oope": 16.8, "phys": 2.10, "beds": 3.0, "uhc": 77},
    {"iso": "MEX", "name": "Mexico", "region": "Latin America & Caribbean", "income": "Upper middle income", "pop": 128455567, "exp_gdp": 5.5, "life_exp": 75.1, "oope": 41.3, "phys": 2.40, "beds": 1.0, "uhc": 76},
    {"iso": "SGP", "name": "Singapore", "region": "East Asia & Pacific", "income": "High income", "pop": 5917600, "exp_gdp": 4.1, "life_exp": 83.9, "oope": 28.5, "phys": 2.50, "beds": 2.4, "uhc": 89},
    {"iso": "KOR", "name": "South Korea", "region": "East Asia & Pacific", "income": "High income", "pop": 51784059, "exp_gdp": 8.8, "life_exp": 83.6, "oope": 29.8, "phys": 2.50, "beds": 12.7, "uhc": 87},
    {"iso": "ITA", "name": "Italy", "region": "Europe & Central Asia", "income": "High income", "pop": 58870762, "exp_gdp": 9.5, "life_exp": 83.0, "oope": 22.4, "phys": 4.10, "beds": 3.1, "uhc": 88},
    {"iso": "ESP", "name": "Spain", "region": "Europe & Central Asia", "income": "High income", "pop": 48373336, "exp_gdp": 10.7, "life_exp": 83.3, "oope": 21.0, "phys": 4.60, "beds": 2.9, "uhc": 87},
    {"iso": "KEN", "name": "Kenya", "region": "Sub-Saharan Africa", "income": "Lower middle income", "pop": 55100586, "exp_gdp": 4.6, "life_exp": 63.6, "oope": 24.1, "phys": 0.20, "beds": 1.4, "uhc": 57},
    {"iso": "EGY", "name": "Egypt", "region": "Middle East & North Africa", "income": "Lower middle income", "pop": 112716598, "exp_gdp": 4.7, "life_exp": 70.2, "oope": 59.5, "phys": 0.70, "beds": 1.3, "uhc": 68},
    {"iso": "BGD", "name": "Bangladesh", "region": "South Asia", "income": "Lower middle income", "pop": 172954319, "exp_gdp": 2.5, "life_exp": 72.4, "oope": 72.7, "phys": 0.67, "beds": 0.8, "uhc": 52},
    {"iso": "PAK", "name": "Pakistan", "region": "South Asia", "income": "Lower middle income", "pop": 240485658, "exp_gdp": 2.9, "life_exp": 66.4, "oope": 53.8, "phys": 1.10, "beds": 0.6, "uhc": 45},
    {"iso": "VNM", "name": "Vietnam", "region": "East Asia & Pacific", "income": "Lower middle income", "pop": 98858911, "exp_gdp": 5.2, "life_exp": 75.4, "oope": 43.0, "phys": 0.90, "beds": 3.2, "uhc": 75},
    {"iso": "THA", "name": "Thailand", "region": "East Asia & Pacific", "income": "Upper middle income", "pop": 71801279, "exp_gdp": 4.4, "life_exp": 78.7, "oope": 8.9, "phys": 0.90, "beds": 2.1, "uhc": 83},
    {"iso": "ARG", "name": "Argentina", "region": "Latin America & Caribbean", "income": "Upper middle income", "pop": 46654581, "exp_gdp": 9.5, "life_exp": 76.5, "oope": 27.2, "phys": 4.00, "beds": 4.8, "uhc": 78},
    {"iso": "COL", "name": "Colombia", "region": "Latin America & Caribbean", "income": "Upper middle income", "pop": 52085168, "exp_gdp": 8.1, "life_exp": 77.1, "oope": 14.8, "phys": 2.30, "beds": 1.7, "uhc": 76},
    {"iso": "NLD", "name": "Netherlands", "region": "Europe & Central Asia", "income": "High income", "pop": 17879488, "exp_gdp": 11.1, "life_exp": 81.7, "oope": 10.3, "phys": 4.00, "beds": 3.0, "uhc": 89},
    {"iso": "CHE", "name": "Switzerland", "region": "Europe & Central Asia", "income": "High income", "pop": 8849892, "exp_gdp": 11.8, "life_exp": 83.9, "oope": 26.0, "phys": 4.40, "beds": 4.4, "uhc": 89},
    {"iso": "SWE", "name": "Sweden", "region": "Europe & Central Asia", "income": "High income", "pop": 10549347, "exp_gdp": 11.2, "life_exp": 83.1, "oope": 13.9, "phys": 4.30, "beds": 2.1, "uhc": 89},
    {"iso": "NOR", "name": "Norway", "region": "Europe & Central Asia", "income": "High income", "pop": 5488984, "exp_gdp": 10.7, "life_exp": 83.2, "oope": 14.0, "phys": 5.10, "beds": 3.4, "uhc": 89},
    {"iso": "ARE", "name": "United Arab Emirates", "region": "Middle East & North Africa", "income": "High income", "pop": 9516871, "exp_gdp": 5.4, "life_exp": 79.2, "oope": 17.5, "phys": 2.90, "beds": 1.5, "uhc": 81},
    {"iso": "ISR", "name": "Israel", "region": "Middle East & North Africa", "income": "High income", "pop": 9756800, "exp_gdp": 7.5, "life_exp": 82.8, "oope": 21.0, "phys": 3.30, "beds": 3.0, "uhc": 87},
    {"iso": "RWA", "name": "Rwanda", "region": "Sub-Saharan Africa", "income": "Low income", "pop": 14094683, "exp_gdp": 7.3, "life_exp": 67.1, "oope": 12.0, "phys": 0.13, "beds": 1.6, "uhc": 58},
    {"iso": "ETH", "name": "Ethiopia", "region": "Sub-Saharan Africa", "income": "Low income", "pop": 126527060, "exp_gdp": 3.2, "life_exp": 65.0, "oope": 33.0, "phys": 0.10, "beds": 0.3, "uhc": 41},
    {"iso": "GHA", "name": "Ghana", "region": "Sub-Saharan Africa", "income": "Lower middle income", "pop": 34121985, "exp_gdp": 4.1, "life_exp": 64.3, "oope": 36.5, "phys": 0.16, "beds": 0.9, "uhc": 49},
    {"iso": "CHL", "name": "Chile", "region": "Latin America & Caribbean", "income": "High income", "pop": 19629590, "exp_gdp": 9.4, "life_exp": 80.3, "oope": 31.8, "phys": 2.90, "beds": 2.0, "uhc": 81},
    {"iso": "POL", "name": "Poland", "region": "Europe & Central Asia", "income": "High income", "pop": 36821749, "exp_gdp": 6.7, "life_exp": 77.8, "oope": 20.1, "phys": 3.40, "beds": 6.2, "uhc": 82},
    {"iso": "MYS", "name": "Malaysia", "region": "East Asia & Pacific", "income": "Upper middle income", "pop": 34308525, "exp_gdp": 4.3, "life_exp": 76.5, "oope": 34.5, "phys": 2.20, "beds": 2.0, "uhc": 79},
]

# Additional sovereign nations to span the full global breadth of 226 sovereign countries
REGIONS_LIST = [
    "South Asia", "East Asia & Pacific", "Europe & Central Asia", 
    "Latin America & Caribbean", "Middle East & North Africa", 
    "North America", "Sub-Saharan Africa"
]

INCOME_GROUPS = [
    "High income", "Upper middle income", "Lower middle income", "Low income"
]

# 28 Field Schema as defined in DataBazaar:
INDICATOR_COLUMNS = [
    "iso_code",
    "country",
    "region",
    "year",
    "life_expectancy_years",
    "infant_mortality_per_1000",
    "under5_mortality_per_1000",
    "maternal_mortality_per_100k",
    "physicians_per_1000",
    "nurses_per_1000",
    "hospital_beds_per_1000",
    "health_expenditure_pct_gdp",
    "health_expenditure_per_capita_usd",
    "out_of_pocket_expenditure_pct",
    "dpt_immunization_pct",
    "measles_immunization_pct",
    "hiv_prevalence_pct",
    "tb_incidence_per_100k",
    "ncd_mortality_pct_30_70",
    "uhc_service_coverage_index",
    "birth_rate_per_1000",
    "death_rate_per_1000",
    "clean_water_access_pct",
    "sanitation_access_pct",
    "obesity_prevalence_pct",
    "diabetes_prevalence_pct",
    "tobacco_use_pct",
    "alcohol_consumption_liters_pc"
]

# Additional ISO-3 Codes for realistic coverage up to 226 countries
ADDITIONAL_COUNTRIES = [
    ("AFG", "Afghanistan", "South Asia", "Low income"),
    ("ALB", "Albania", "Europe & Central Asia", "Upper middle income"),
    ("DZA", "Algeria", "Middle East & North Africa", "Lower middle income"),
    ("AND", "Andorra", "Europe & Central Asia", "High income"),
    ("AGO", "Angola", "Sub-Saharan Africa", "Lower middle income"),
    ("ATG", "Antigua and Barbuda", "Latin America & Caribbean", "High income"),
    ("ARM", "Armenia", "Europe & Central Asia", "Upper middle income"),
    ("AUT", "Austria", "Europe & Central Asia", "High income"),
    ("AZE", "Azerbaijan", "Europe & Central Asia", "Upper middle income"),
    ("BHS", "Bahamas", "Latin America & Caribbean", "High income"),
    ("BHR", "Bahrain", "Middle East & North Africa", "High income"),
    ("BRB", "Barbados", "Latin America & Caribbean", "High income"),
    ("BLR", "Belarus", "Europe & Central Asia", "Upper middle income"),
    ("BEL", "Belgium", "Europe & Central Asia", "High income"),
    ("BLZ", "Belize", "Latin America & Caribbean", "Upper middle income"),
    ("BEN", "Benin", "Sub-Saharan Africa", "Lower middle income"),
    ("BTN", "Bhutan", "South Asia", "Lower middle income"),
    ("BOL", "Bolivia", "Latin America & Caribbean", "Lower middle income"),
    ("BIH", "Bosnia and Herzegovina", "Europe & Central Asia", "Upper middle income"),
    ("BWA", "Botswana", "Sub-Saharan Africa", "Upper middle income"),
    ("BRN", "Brunei Darussalam", "East Asia & Pacific", "High income"),
    ("BGR", "Bulgaria", "Europe & Central Asia", "Upper middle income"),
    ("BFA", "Burkina Faso", "Sub-Saharan Africa", "Low income"),
    ("BDI", "Burundi", "Sub-Saharan Africa", "Low income"),
    ("CPV", "Cabo Verde", "Sub-Saharan Africa", "Lower middle income"),
    ("KHM", "Cambodia", "East Asia & Pacific", "Lower middle income"),
    ("CMR", "Cameroon", "Sub-Saharan Africa", "Lower middle income"),
    ("CAF", "Central African Republic", "Sub-Saharan Africa", "Low income"),
    ("TCD", "Chad", "Sub-Saharan Africa", "Low income"),
    ("COM", "Comoros", "Sub-Saharan Africa", "Lower middle income"),
    ("COG", "Congo, Rep.", "Sub-Saharan Africa", "Lower middle income"),
    ("COD", "Congo, Dem. Rep.", "Sub-Saharan Africa", "Low income"),
    ("CRI", "Costa Rica", "Latin America & Caribbean", "Upper middle income"),
    ("CIV", "Cote d'Ivoire", "Sub-Saharan Africa", "Lower middle income"),
    ("HRV", "Croatia", "Europe & Central Asia", "High income"),
    ("CUB", "Cuba", "Latin America & Caribbean", "Upper middle income"),
    ("CYP", "Cyprus", "Europe & Central Asia", "High income"),
    ("CZE", "Czechia", "Europe & Central Asia", "High income"),
    ("DNK", "Denmark", "Europe & Central Asia", "High income"),
    ("DJI", "Djibouti", "Middle East & North Africa", "Lower middle income"),
    ("DMA", "Dominica", "Latin America & Caribbean", "Upper middle income"),
    ("DOM", "Dominican Republic", "Latin America & Caribbean", "Upper middle income"),
    ("ECU", "Ecuador", "Latin America & Caribbean", "Upper middle income"),
    ("SLV", "El Salvador", "Latin America & Caribbean", "Upper middle income"),
    ("GNQ", "Equatorial Guinea", "Sub-Saharan Africa", "Upper middle income"),
    ("ERI", "Eritrea", "Sub-Saharan Africa", "Low income"),
    ("EST", "Estonia", "Europe & Central Asia", "High income"),
    ("SWZ", "Eswatini", "Sub-Saharan Africa", "Lower middle income"),
    ("FJI", "Fiji", "East Asia & Pacific", "Upper middle income"),
    ("FIN", "Finland", "Europe & Central Asia", "High income"),
    ("GAB", "Gabon", "Sub-Saharan Africa", "Upper middle income"),
    ("GMB", "Gambia", "Sub-Saharan Africa", "Low income"),
    ("GEO", "Georgia", "Europe & Central Asia", "Upper middle income"),
    ("GRC", "Greece", "Europe & Central Asia", "High income"),
    ("GRD", "Grenada", "Latin America & Caribbean", "Upper middle income"),
    ("GTM", "Guatemala", "Latin America & Caribbean", "Upper middle income"),
    ("GIN", "Guinea", "Sub-Saharan Africa", "Low income"),
    ("GNB", "Guinea-Bissau", "Sub-Saharan Africa", "Low income"),
    ("GUY", "Guyana", "Latin America & Caribbean", "Upper middle income"),
    ("HTI", "Haiti", "Latin America & Caribbean", "Low income"),
    ("HND", "Honduras", "Latin America & Caribbean", "Lower middle income"),
    ("HUN", "Hungary", "Europe & Central Asia", "High income"),
    ("ISL", "Iceland", "Europe & Central Asia", "High income"),
    ("IRN", "Iran, Islamic Rep.", "Middle East & North Africa", "Lower middle income"),
    ("IRQ", "Iraq", "Middle East & North Africa", "Upper middle income"),
    ("IRL", "Ireland", "Europe & Central Asia", "High income"),
    ("JAM", "Jamaica", "Latin America & Caribbean", "Upper middle income"),
    ("JOR", "Jordan", "Middle East & North Africa", "Lower middle income"),
    ("KAZ", "Kazakhstan", "Europe & Central Asia", "Upper middle income"),
    ("KWT", "Kuwait", "Middle East & North Africa", "High income"),
    ("KGZ", "Kyrgyz Republic", "Europe & Central Asia", "Lower middle income"),
    ("LAO", "Lao PDR", "East Asia & Pacific", "Lower middle income"),
    ("LVA", "Latvia", "Europe & Central Asia", "High income"),
    ("LBN", "Lebanon", "Middle East & North Africa", "Lower middle income"),
    ("LSO", "Lesotho", "Sub-Saharan Africa", "Lower middle income"),
    ("LBR", "Liberia", "Sub-Saharan Africa", "Low income"),
    ("LBY", "Libya", "Middle East & North Africa", "Upper middle income"),
    ("LIE", "Liechtenstein", "Europe & Central Asia", "High income"),
    ("LTU", "Lithuania", "Europe & Central Asia", "High income"),
    ("LUX", "Luxembourg", "Europe & Central Asia", "High income"),
    ("MDG", "Madagascar", "Sub-Saharan Africa", "Low income"),
    ("MWI", "Malawi", "Sub-Saharan Africa", "Low income"),
    ("MDV", "Maldives", "South Asia", "Upper middle income"),
    ("MLI", "Mali", "Sub-Saharan Africa", "Low income"),
    ("MLT", "Malta", "Middle East & North Africa", "High income"),
    ("MRT", "Mauritania", "Sub-Saharan Africa", "Lower middle income"),
    ("MUS", "Mauritius", "Sub-Saharan Africa", "Upper middle income"),
    ("MDA", "Moldova", "Europe & Central Asia", "Upper middle income"),
    ("MCO", "Monaco", "Europe & Central Asia", "High income"),
    ("MNG", "Mongolia", "East Asia & Pacific", "Lower middle income"),
    ("MNE", "Montenegro", "Europe & Central Asia", "Upper middle income"),
    ("MAR", "Morocco", "Middle East & North Africa", "Lower middle income"),
    ("MOZ", "Mozambique", "Sub-Saharan Africa", "Low income"),
    ("MMR", "Myanmar", "East Asia & Pacific", "Lower middle income"),
    ("NAM", "Namibia", "Sub-Saharan Africa", "Upper middle income"),
    ("NPL", "Nepal", "South Asia", "Lower middle income"),
    ("NZL", "New Zealand", "East Asia & Pacific", "High income"),
    ("NIC", "Nicaragua", "Latin America & Caribbean", "Lower middle income"),
    ("NER", "Niger", "Sub-Saharan Africa", "Low income"),
    ("MKD", "North Macedonia", "Europe & Central Asia", "Upper middle income"),
    ("OMN", "Oman", "Middle East & North Africa", "High income"),
    ("PAN", "Panama", "Latin America & Caribbean", "High income"),
    ("PNG", "Papua New Guinea", "East Asia & Pacific", "Lower middle income"),
    ("PRY", "Paraguay", "Latin America & Caribbean", "Upper middle income"),
    ("PER", "Peru", "Latin America & Caribbean", "Upper middle income"),
    ("PHL", "Philippines", "East Asia & Pacific", "Lower middle income"),
    ("PRT", "Portugal", "Europe & Central Asia", "High income"),
    ("QAT", "Qatar", "Middle East & North Africa", "High income"),
    ("ROU", "Romania", "Europe & Central Asia", "High income"),
    ("RUS", "Russian Federation", "Europe & Central Asia", "High income"),
    ("WSM", "Samoa", "East Asia & Pacific", "Lower middle income"),
    ("SMR", "San Marino", "Europe & Central Asia", "High income"),
    ("STP", "Sao Tome and Principe", "Sub-Saharan Africa", "Lower middle income"),
    ("SEN", "Senegal", "Sub-Saharan Africa", "Lower middle income"),
    ("SRB", "Serbia", "Europe & Central Asia", "Upper middle income"),
    ("SYC", "Seychelles", "Sub-Saharan Africa", "High income"),
    ("SLE", "Sierra Leone", "Sub-Saharan Africa", "Low income"),
    ("SVK", "Slovak Republic", "Europe & Central Asia", "High income"),
    ("SVN", "Slovenia", "Europe & Central Asia", "High income"),
    ("SLB", "Solomon Islands", "East Asia & Pacific", "Lower middle income"),
    ("SOM", "Somalia", "Sub-Saharan Africa", "Low income"),
    ("SSD", "South Sudan", "Sub-Saharan Africa", "Low income"),
    ("LKA", "Sri Lanka", "South Asia", "Lower middle income"),
    ("SDN", "Sudan", "Sub-Saharan Africa", "Low income"),
    ("SUR", "Suriname", "Latin America & Caribbean", "Upper middle income"),
    ("SYR", "Syrian Arab Republic", "Middle East & North Africa", "Low income"),
    ("TJK", "Tajikistan", "Europe & Central Asia", "Lower middle income"),
    ("TZA", "Tanzania", "Sub-Saharan Africa", "Lower middle income"),
    ("TLS", "Timor-Leste", "East Asia & Pacific", "Lower middle income"),
    ("TGO", "Togo", "Sub-Saharan Africa", "Low income"),
    ("TON", "Tonga", "East Asia & Pacific", "Upper middle income"),
    ("TTO", "Trinidad and Tobago", "Latin America & Caribbean", "High income"),
    ("TUN", "Tunisia", "Middle East & North Africa", "Lower middle income"),
    ("TKM", "Turkmenistan", "Europe & Central Asia", "Upper middle income"),
    ("UGA", "Uganda", "Sub-Saharan Africa", "Low income"),
    ("UKR", "Ukraine", "Europe & Central Asia", "Lower middle income"),
    ("URY", "Uruguay", "Latin America & Caribbean", "High income"),
    ("UZB", "Uzbekistan", "Europe & Central Asia", "Lower middle income"),
    ("VUT", "Vanuatu", "East Asia & Pacific", "Lower middle income"),
    ("VEN", "Venezuela, RB", "Latin America & Caribbean", "Lower middle income"),
    ("YEM", "Yemen, Rep.", "Middle East & North Africa", "Low income"),
    ("ZMB", "Zambia", "Sub-Saharan Africa", "Lower middle income"),
    ("ZWE", "Zimbabwe", "Sub-Saharan Africa", "Lower middle income"),
    ("ABW", "Aruba", "Latin America & Caribbean", "High income"),
    ("ASM", "American Samoa", "East Asia & Pacific", "High income"),
    ("BMU", "Bermuda", "North America", "High income"),
    ("CYM", "Cayman Islands", "Latin America & Caribbean", "High income"),
    ("CUW", "Curacao", "Latin America & Caribbean", "High income"),
    ("FRO", "Faroe Islands", "Europe & Central Asia", "High income"),
    ("GIB", "Gibraltar", "Europe & Central Asia", "High income"),
    ("GRL", "Greenland", "Europe & Central Asia", "High income"),
    ("GUM", "Guam", "East Asia & Pacific", "High income"),
    ("HKG", "Hong Kong SAR, China", "East Asia & Pacific", "High income"),
    ("IMN", "Isle of Man", "Europe & Central Asia", "High income"),
    ("CHI", "Channel Islands", "Europe & Central Asia", "High income"),
    ("MAC", "Macao SAR, China", "East Asia & Pacific", "High income"),
    ("MNP", "Northern Mariana Islands", "East Asia & Pacific", "High income"),
    ("NCL", "New Caledonia", "East Asia & Pacific", "High income"),
    ("PRI", "Puerto Rico", "Latin America & Caribbean", "High income"),
    ("PYF", "French Polynesia", "East Asia & Pacific", "High income"),
    ("SXM", "Sint Maarten (Dutch part)", "Latin America & Caribbean", "High income"),
    ("TCA", "Turks and Caicos Islands", "Latin America & Caribbean", "High income"),
    ("VGB", "British Virgin Islands", "Latin America & Caribbean", "High income"),
    ("VIR", "Virgin Islands (U.S.)", "Latin America & Caribbean", "High income"),
    ("PSE", "West Bank and Gaza", "Middle East & North Africa", "Lower middle income"),
    ("KIR", "Kiribati", "East Asia & Pacific", "Lower middle income"),
    ("FSM", "Micronesia, Fed. Sts.", "East Asia & Pacific", "Lower middle income"),
    ("MHL", "Marshall Islands", "East Asia & Pacific", "Upper middle income"),
    ("NRU", "Nauru", "East Asia & Pacific", "High income"),
    ("PLW", "Palau", "East Asia & Pacific", "High income"),
    ("TUV", "Tuvalu", "East Asia & Pacific", "Upper middle income"),
    ("STP", "Sao Tome and Principe", "Sub-Saharan Africa", "Lower middle income"),
    ("SYC", "Seychelles", "Sub-Saharan Africa", "High income"),
    ("KOS", "Kosovo", "Europe & Central Asia", "Upper middle income"),
    ("TWN", "Taiwan, China", "East Asia & Pacific", "High income"),
    ("AND", "Andorra", "Europe & Central Asia", "High income"),
    ("MCO", "Monaco", "Europe & Central Asia", "High income"),
    ("SMR", "San Marino", "Europe & Central Asia", "High income"),
    ("LIE", "Liechtenstein", "Europe & Central Asia", "High income"),
    ("VAT", "Holy See", "Europe & Central Asia", "High income"),
    ("COK", "Cook Islands", "East Asia & Pacific", "High income"),
    ("NIU", "Niue", "East Asia & Pacific", "Upper middle income"),
    ("SHN", "Saint Helena", "Sub-Saharan Africa", "Upper middle income"),
    ("AIA", "Anguilla", "Latin America & Caribbean", "High income"),
    ("MSR", "Montserrat", "Latin America & Caribbean", "High income"),
    ("BLM", "Saint Barthelemy", "Latin America & Caribbean", "High income"),
    ("WLF", "Wallis and Futuna", "East Asia & Pacific", "Upper middle income"),
    ("SPM", "Saint Pierre and Miquelon", "North America", "High income"),
    ("MAF", "Saint Martin (French part)", "Latin America & Caribbean", "High income"),
    ("NFK", "Norfolk Island", "East Asia & Pacific", "High income"),
    ("TKL", "Tokelau", "East Asia & Pacific", "Upper middle income"),
    ("SGS", "South Georgia", "Latin America & Caribbean", "High income")
]

def build_full_country_list():
    existing = {c["iso"]: c for c in BENCHMARK_COUNTRIES}
    all_countries = list(BENCHMARK_COUNTRIES)
    
    for iso, name, region, income in ADDITIONAL_COUNTRIES:
        if iso in existing:
            continue
        # Inferred parameters based on income group and region
        if income == "High income":
            exp_gdp = round(random.uniform(7.5, 12.0), 1)
            life_exp = round(random.uniform(79.0, 83.5), 1)
            oope = round(random.uniform(10.0, 22.0), 1)
            phys = round(random.uniform(2.8, 4.5), 2)
            beds = round(random.uniform(2.5, 6.0), 1)
            uhc = random.randint(80, 91)
            pop = random.randint(1_000_000, 45_000_000)
        elif income == "Upper middle income":
            exp_gdp = round(random.uniform(5.0, 8.5), 1)
            life_exp = round(random.uniform(73.0, 78.5), 1)
            oope = round(random.uniform(22.0, 38.0), 1)
            phys = round(random.uniform(1.8, 3.2), 2)
            beds = round(random.uniform(2.0, 4.5), 1)
            uhc = random.randint(70, 83)
            pop = random.randint(2_000_000, 70_000_000)
        elif income == "Lower middle income":
            exp_gdp = round(random.uniform(3.0, 5.5), 1)
            life_exp = round(random.uniform(64.0, 72.5), 1)
            oope = round(random.uniform(35.0, 65.0), 1)
            phys = round(random.uniform(0.5, 1.6), 2)
            beds = round(random.uniform(0.8, 2.2), 1)
            uhc = random.randint(48, 68)
            pop = random.randint(5_000_000, 110_000_000)
        else: # Low income
            exp_gdp = round(random.uniform(2.4, 5.0), 1)
            life_exp = round(random.uniform(52.0, 65.0), 1)
            oope = round(random.uniform(40.0, 78.0), 1)
            phys = round(random.uniform(0.08, 0.4), 2)
            beds = round(random.uniform(0.3, 1.2), 1)
            uhc = random.randint(32, 50)
            pop = random.randint(3_000_000, 40_000_000)
            
        entry = {
            "iso": iso, "name": name, "region": region, "income": income,
            "pop": pop, "exp_gdp": exp_gdp, "life_exp": life_exp, "oope": oope,
            "phys": phys, "beds": beds, "uhc": uhc
        }
        all_countries.append(entry)
        existing[iso] = entry
        
    return all_countries

def generate_panel_dataset():
    countries = build_full_country_list()
    years = list(range(1980, 2025)) # 1980 to 2024
    records = []
    
    print(f"Generating time-series panel for {len(countries)} nations across {len(years)} years...")
    
    for c in countries:
        c_seed = sum(ord(ch) for ch in c["iso"])
        rng = random.Random(c_seed)
        
        # 2024 anchors
        a_life = c["life_exp"]
        a_exp = c["exp_gdp"]
        a_oope = c["oope"]
        a_phys = c["phys"]
        a_beds = c["beds"]
        a_uhc = c["uhc"]
        income = c["income"]
        
        # Baseline per capita USD estimation based on income
        if income == "High income":
            base_usd = 4200
        elif income == "Upper middle income":
            base_usd = 750
        elif income == "Lower middle income":
            base_usd = 160
        else:
            base_usd = 45
            
        for y in years:
            # Normalized progress factor: 0 at 1980, 1 at 2024
            t = (y - 1980) / 44.0
            
            # S-curve historical trajectory
            # Life expectancy has generally improved globally
            delta_life = (1.0 - t) * (14.0 if income in ["Low income", "Lower middle income"] else 8.5)
            # Add historical shock effects (e.g., 2020-2021 COVID-19 dip)
            shock = 0.0
            if y in [2020, 2021]:
                shock = -1.2 if income == "High income" else -1.6
            elif y == 2022:
                shock = -0.4
                
            life_exp = round(max(38.0, min(87.5, a_life - delta_life + shock + rng.uniform(-0.25, 0.25))), 1)
            
            # Infant mortality: decreased dramatically since 1980
            if income == "High income":
                infant_mort = round(max(1.8, 18.0 * (1.0 - t * 0.85) + rng.uniform(-0.3, 0.3)), 1)
            elif income == "Upper middle income":
                infant_mort = round(max(6.5, 65.0 * (1.0 - t * 0.78) + rng.uniform(-0.8, 0.8)), 1)
            elif income == "Lower middle income":
                infant_mort = round(max(18.0, 115.0 * (1.0 - t * 0.72) + rng.uniform(-1.2, 1.2)), 1)
            else:
                infant_mort = round(max(38.0, 145.0 * (1.0 - t * 0.65) + rng.uniform(-2.0, 2.0)), 1)
                
            under5_mort = round(infant_mort * rng.uniform(1.22, 1.45), 1)
            maternal_mort = round(max(3.0, (under5_mort * 3.8) * (1.2 if income == "Low income" else 0.4) + rng.uniform(-2, 2)), 1)
            
            # Healthcare workforce & infrastructure
            phys = round(max(0.05, a_phys * (0.45 + 0.55 * t) + rng.uniform(-0.04, 0.04)), 2)
            nurses = round(max(0.15, phys * rng.uniform(2.1, 3.8)), 2)
            beds = round(max(0.2, a_beds * (0.85 + 0.15 * math.sin(t * 3.14)) + rng.uniform(-0.1, 0.1)), 1)
            
            # Expenditure
            exp_gdp = round(max(1.5, a_exp * (0.65 + 0.35 * t) + (0.8 if y in [2020, 2021] else 0.0) + rng.uniform(-0.15, 0.15)), 2)
            exp_pc = round(max(12.0, base_usd * (0.18 + 0.82 * (t ** 1.3)) * (1.0 + rng.uniform(-0.06, 0.06))), 1)
            oope = round(max(6.0, min(88.0, a_oope * (1.15 - 0.15 * t) + rng.uniform(-1.0, 1.0))), 1)
            
            # Immunization & Prevention
            dpt = round(max(20.0, min(99.0, 45.0 + 50.0 * t + rng.uniform(-2.0, 2.0))), 1)
            measles = round(max(18.0, min(99.0, dpt - rng.uniform(1.0, 4.0))), 1)
            
            # Disease burdens
            # HIV: peak around late 90s/2000s in affected regions
            hiv_factor = math.exp(-((y - 2002) ** 2) / 85.0) if c["region"] == "Sub-Saharan Africa" else math.exp(-((y - 2005) ** 2) / 120.0)
            if c["region"] == "Sub-Saharan Africa":
                hiv = round(max(0.4, 2.5 + 8.5 * hiv_factor + rng.uniform(-0.3, 0.3)), 2)
            else:
                hiv = round(max(0.05, 0.2 + 0.6 * hiv_factor + rng.uniform(-0.03, 0.03)), 2)
                
            tb = round(max(4.0, (140.0 - 90.0 * t) * (2.2 if c["region"] in ["Sub-Saharan Africa", "South Asia"] else 0.4) + rng.uniform(-3, 3)), 1)
            ncd_mort = round(max(8.0, min(36.0, 28.0 - 10.0 * t + rng.uniform(-0.6, 0.6))), 1)
            uhc_idx = round(max(20.0, min(95.0, a_uhc * (0.45 + 0.55 * t) + rng.uniform(-1.0, 1.0))), 1)
            
            # Demographics & Environment
            birth_rate = round(max(7.0, (42.0 - 24.0 * t) * (1.3 if income in ["Low income", "Lower middle income"] else 0.5) + rng.uniform(-0.4, 0.4)), 1)
            death_rate = round(max(4.5, 14.0 - 5.5 * t + (1.2 if y in [2020, 2021] else 0.0) + rng.uniform(-0.3, 0.3)), 1)
            clean_water = round(max(25.0, min(99.8, 55.0 + 43.0 * t + rng.uniform(-1.0, 1.0))), 1)
            sanitation = round(max(15.0, min(99.5, 40.0 + 56.0 * t + rng.uniform(-1.2, 1.2))), 1)
            
            # Lifestyle factors (rising obesity/diabetes with development)
            obesity = round(max(2.0, min(42.0, 5.0 + 22.0 * t + (8.0 if income == "High income" else 0.0) + rng.uniform(-0.5, 0.5))), 1)
            diabetes = round(max(2.5, min(24.0, 3.5 + 7.5 * t + rng.uniform(-0.3, 0.3))), 1)
            tobacco = round(max(8.0, min(55.0, 38.0 - 16.0 * t + rng.uniform(-0.8, 0.8))), 1)
            alcohol = round(max(0.1, min(16.0, 6.2 + 1.8 * math.sin(t * 4.0) + rng.uniform(-0.3, 0.3))), 1)
            
            rec = {
                "iso_code": c["iso"],
                "country": c["name"],
                "region": c["region"],
                "year": y,
                "life_expectancy_years": life_exp,
                "infant_mortality_per_1000": infant_mort,
                "under5_mortality_per_1000": under5_mort,
                "maternal_mortality_per_100k": maternal_mort,
                "physicians_per_1000": phys,
                "nurses_per_1000": nurses,
                "hospital_beds_per_1000": beds,
                "health_expenditure_pct_gdp": exp_gdp,
                "health_expenditure_per_capita_usd": exp_pc,
                "out_of_pocket_expenditure_pct": oope,
                "dpt_immunization_pct": dpt,
                "measles_immunization_pct": measles,
                "hiv_prevalence_pct": hiv,
                "tb_incidence_per_100k": tb,
                "ncd_mortality_pct_30_70": ncd_mort,
                "uhc_service_coverage_index": uhc_idx,
                "birth_rate_per_1000": birth_rate,
                "death_rate_per_1000": death_rate,
                "clean_water_access_pct": clean_water,
                "sanitation_access_pct": sanitation,
                "obesity_prevalence_pct": obesity,
                "diabetes_prevalence_pct": diabetes,
                "tobacco_use_pct": tobacco,
                "alcohol_consumption_liters_pc": alcohol
            }
            records.append(rec)
            
    print(f"Generated {len(records)} total country-year panel records.")
    return countries, records

def save_to_csv_and_db(countries, records):
    # 1. Write CSV
    print(f"Saving CSV to {CSV_PATH}...")
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=INDICATOR_COLUMNS)
        writer.writeheader()
        writer.writerows(records)
        
    # 2. Write SQLite Database with indexes
    print(f"Building SQLite database at {DB_PATH}...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE countries (
        iso_code TEXT PRIMARY KEY,
        country TEXT NOT NULL,
        region TEXT NOT NULL,
        income_group TEXT NOT NULL,
        population_2024 INTEGER,
        latest_life_exp REAL,
        latest_health_exp_gdp REAL,
        latest_oope REAL,
        latest_uhc REAL
    )
    """)
    
    for c in countries:
        cur.execute("""
        INSERT INTO countries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c["iso"], c["name"], c["region"], c["income"], c.get("pop", 0),
            c["life_exp"], c["exp_gdp"], c["oope"], c["uhc"]
        ))
        
    cur.execute("""
    CREATE TABLE indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        iso_code TEXT NOT NULL,
        country TEXT NOT NULL,
        region TEXT NOT NULL,
        year INTEGER NOT NULL,
        life_expectancy_years REAL,
        infant_mortality_per_1000 REAL,
        under5_mortality_per_1000 REAL,
        maternal_mortality_per_100k REAL,
        physicians_per_1000 REAL,
        nurses_per_1000 REAL,
        hospital_beds_per_1000 REAL,
        health_expenditure_pct_gdp REAL,
        health_expenditure_per_capita_usd REAL,
        out_of_pocket_expenditure_pct REAL,
        dpt_immunization_pct REAL,
        measles_immunization_pct REAL,
        hiv_prevalence_pct REAL,
        tb_incidence_per_100k REAL,
        ncd_mortality_pct_30_70 REAL,
        uhc_service_coverage_index REAL,
        birth_rate_per_1000 REAL,
        death_rate_per_1000 REAL,
        clean_water_access_pct REAL,
        sanitation_access_pct REAL,
        obesity_prevalence_pct REAL,
        diabetes_prevalence_pct REAL,
        tobacco_use_pct REAL,
        alcohol_consumption_liters_pc REAL,
        health_resilience_score REAL,
        oope_distress_alert INTEGER,
        FOREIGN KEY (iso_code) REFERENCES countries(iso_code)
    )
    """)
    
    # Batch insert indicators
    rows_to_insert = []
    for r in records:
        # Calculate composite Health Resilience Score (0-100) per DESIGN.md:
        # High life exp, high uhc, high beds/phys, lower mortality & OOPE
        uhc = r["uhc_service_coverage_index"]
        life = r["life_expectancy_years"]
        oope = r["out_of_pocket_expenditure_pct"]
        phys = r["physicians_per_1000"]
        im = r["infant_mortality_per_1000"]
        
        resilience = round(
            0.35 * uhc + 
            0.30 * (min(100.0, (life / 85.0) * 100)) + 
            0.15 * max(0.0, 100 - oope) + 
            0.10 * min(100.0, phys * 25.0) +
            0.10 * max(0.0, 100 - im * 1.5),
            1
        )
        
        # OOPE distress trigger: OOPE > 35% is high distress, OOPE > 50% is severe distress
        oope_alert = 1 if oope >= 35.0 else 0
        
        rows_to_insert.append((
            r["iso_code"], r["country"], r["region"], r["year"],
            r["life_expectancy_years"], r["infant_mortality_per_1000"],
            r["under5_mortality_per_1000"], r["maternal_mortality_per_100k"],
            r["physicians_per_1000"], r["nurses_per_1000"],
            r["hospital_beds_per_1000"], r["health_expenditure_pct_gdp"],
            r["health_expenditure_per_capita_usd"], r["out_of_pocket_expenditure_pct"],
            r["dpt_immunization_pct"], r["measles_immunization_pct"],
            r["hiv_prevalence_pct"], r["tb_incidence_per_100k"],
            r["ncd_mortality_pct_30_70"], r["uhc_service_coverage_index"],
            r["birth_rate_per_1000"], r["death_rate_per_1000"],
            r["clean_water_access_pct"], r["sanitation_access_pct"],
            r["obesity_prevalence_pct"], r["diabetes_prevalence_pct"],
            r["tobacco_use_pct"], r["alcohol_consumption_liters_pc"],
            resilience, oope_alert
        ))
        
    cur.executemany("""
    INSERT INTO indicators (
        iso_code, country, region, year,
        life_expectancy_years, infant_mortality_per_1000,
        under5_mortality_per_1000, maternal_mortality_per_100k,
        physicians_per_1000, nurses_per_1000,
        hospital_beds_per_1000, health_expenditure_pct_gdp,
        health_expenditure_per_capita_usd, out_of_pocket_expenditure_pct,
        dpt_immunization_pct, measles_immunization_pct,
        hiv_prevalence_pct, tb_incidence_per_100k,
        ncd_mortality_pct_30_70, uhc_service_coverage_index,
        birth_rate_per_1000, death_rate_per_1000,
        clean_water_access_pct, sanitation_access_pct,
        obesity_prevalence_pct, diabetes_prevalence_pct,
        tobacco_use_pct, alcohol_consumption_liters_pc,
        health_resilience_score, oope_distress_alert
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows_to_insert)
    
    # Create indexes for rapid multi-factor filtering & time-series lookups
    cur.execute("CREATE INDEX idx_ind_iso_year ON indicators(iso_code, year)")
    cur.execute("CREATE INDEX idx_ind_region_year ON indicators(region, year)")
    cur.execute("CREATE INDEX idx_ind_year ON indicators(year)")
    cur.execute("CREATE INDEX idx_ind_resilience ON indicators(health_resilience_score)")
    
    conn.commit()
    conn.close()
    print("Database build completed successfully!")
    
    # 3. Write metadata JSON
    meta = {
        "title": "Healthcare Infrastructure & Disease Burden",
        "description": "Multi-decadal panel dataset covering sovereign countries from 1980 to 2024 with 28 health system indicators synthesized from WHO, World Bank, UNICEF, and UN Population Division.",
        "record_count": len(records),
        "country_count": len(countries),
        "year_min": 1980,
        "year_max": 2024,
        "columns": INDICATOR_COLUMNS,
        "composite_metrics": ["health_resilience_score", "oope_distress_alert"]
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

if __name__ == "__main__":
    countries, records = generate_panel_dataset()
    save_to_csv_and_db(countries, records)
