import os
from datetime import datetime

import openpyxl
import pandas as pd


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(project_root, "results")

capex_ashp = {
    "Heat pump unit(s)": 2000,
    "Borehole drilling (4x100m)": 0,
    "HDPE piping and grouting": 0,
    "Solar thermal collectors": 0,
    "Installation and controls": 1000,
}
capex_sagshp = {
    "Heat pump unit(s)": 2500,
    "Borehole drilling (4x100m)": 3500,
    "HDPE piping and grouting": 500,
    "Solar thermal collectors": 1200,
    "Installation and controls": 1300,
}

scop_file = os.path.join(results_dir, "scop_annual.csv")
if os.path.exists(scop_file):
    scop_df = pd.read_csv(scop_file)
    E_sagshp = float(scop_df.iloc[0]["E_total_kWh"])
    Q_cooling = float(scop_df.iloc[0]["Q_cooling_kWh"])
else:
    E_sagshp = 8662.0
    Q_cooling = 28837.0

# Conventional ASHP comparison uses a 2.5 seasonal COP baseline.
E_ashp = Q_cooling / 2.5
Maint_ashp = 50.0
Maint_sagshp = 25.0
WaterChem_sagshp = 15.0
discount_rate = 0.035
analysis_years = 20
tariffs = [0.018, 0.025, 0.030, 0.040]


def pv_annuity(annual_cost, rate, years):
    if rate == 0:
        return annual_cost * years
    return annual_cost * (1 - (1 + rate) ** -years) / rate


def simple_payback(extra_capex, annual_savings):
    if annual_savings <= 0:
        return "No payback"
    return round(extra_capex / annual_savings, 1)


C_ashp_total = sum(capex_ashp.values())
C_sagshp_total = sum(capex_sagshp.values())
extra_capex = C_sagshp_total - C_ashp_total

rows = []
for tariff in tariffs:
    annual_ashp = E_ashp * tariff + Maint_ashp
    annual_sagshp = E_sagshp * tariff + Maint_sagshp + WaterChem_sagshp
    annual_savings = annual_ashp - annual_sagshp
    lcc_ashp = C_ashp_total + pv_annuity(annual_ashp, discount_rate, analysis_years)
    lcc_sagshp = C_sagshp_total + pv_annuity(annual_sagshp, discount_rate, analysis_years)
    npv = pv_annuity(annual_savings, discount_rate, analysis_years) - extra_capex
    rows.append(
        {
            "tariff": tariff,
            "annual_ashp": annual_ashp,
            "annual_sagshp": annual_sagshp,
            "annual_savings": annual_savings,
            "lcc_ashp": lcc_ashp,
            "lcc_sagshp": lcc_sagshp,
            "npv": npv,
            "payback": simple_payback(extra_capex, annual_savings),
        }
    )

base = next(row for row in rows if row["tariff"] == 0.030)

print("=== LCC ANALYSIS ===")
print(f"Annual ASHP electricity: {E_ashp:,.0f} kWh")
print(f"Annual SA-GSHP electricity: {E_sagshp:,.0f} kWh")
print(f"LCC ASHP @ 0.030 BHD/kWh: {base['lcc_ashp']:,.0f} BHD")
print(f"LCC SA-GSHP @ 0.030 BHD/kWh: {base['lcc_sagshp']:,.0f} BHD")
print(f"NPV @ 0.030 BHD/kWh: {base['npv']:,.0f} BHD")

economic_data = [
    ["SYSTEM COSTS - CAPITAL EXPENDITURE (CAPEX)"],
    ["Component", "ASHP_Cost_BHD", "SA-GSHP_Cost_BHD", "Cost_Difference_BHD"],
]
for component in capex_sagshp:
    economic_data.append([
        component,
        capex_ashp.get(component, 0),
        capex_sagshp.get(component, 0),
        capex_sagshp.get(component, 0) - capex_ashp.get(component, 0),
    ])

economic_data.extend([
    ["TOTAL CAPITAL COST", C_ashp_total, C_sagshp_total, extra_capex],
    [],
    ["ENERGY INPUTS"],
    ["Metric", "Value", "Unit"],
    ["EnergyPlus cooling load", f"{Q_cooling:.0f}", "kWh/year"],
    ["ASHP electricity baseline", f"{E_ashp:.0f}", "kWh/year"],
    ["SA-GSHP electricity", f"{E_sagshp:.0f}", "kWh/year"],
    [],
    ["LIFE CYCLE COST RESULTS"],
    ["Tariff_BHD_kWh", "ASHP_LCC_BHD", "SA_GSHP_LCC_BHD", "Annual_Savings_BHD", "NPV_BHD", "Simple_Payback_Years"],
])

for row in rows:
    economic_data.append([
        f"{row['tariff']:.3f}",
        f"{row['lcc_ashp']:.0f}",
        f"{row['lcc_sagshp']:.0f}",
        f"{row['annual_savings']:.0f}",
        f"{row['npv']:.0f}",
        row["payback"],
    ])

economic_data.extend([
    [],
    ["BASE CASE INDICATORS @ 0.030 BHD/kWh"],
    ["Metric", "Value", "Unit", "Interpretation"],
    ["Simple Payback Period", base["payback"], "years", "Time to recover extra capital cost"],
    ["Net Present Value", f"{base['npv']:.0f}", "BHD", "Positive values indicate economic benefit"],
    ["Benefit-Cost Ratio", f"{base['lcc_ashp'] / base['lcc_sagshp']:.2f}", "-", "Values above 1 favor SA-GSHP"],
])

csv_path = os.path.join(results_dir, "Economic_Analysis_Results.csv")
with open(csv_path, "w") as f:
    f.write("Life Cycle Cost Analysis - SA-GSHP vs ASHP\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Analysis Period: {analysis_years} years\n")
    f.write(f"Discount Rate: {discount_rate * 100:.1f}%\n\n")
    for row in economic_data:
        f.write(",".join(str(x) for x in row) + "\n")

print(f"Saved: {csv_path}")

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "LCC Analysis"
ws.append(["Metric", "Value"])
ws.append(["Annual ASHP electricity (kWh)", round(E_ashp, 2)])
ws.append(["Annual SA-GSHP electricity (kWh)", round(E_sagshp, 2)])
ws.append(["LCC ASHP @ 0.030 BHD/kWh", round(base["lcc_ashp"], 2)])
ws.append(["LCC SA-GSHP @ 0.030 BHD/kWh", round(base["lcc_sagshp"], 2)])
ws.append(["NPV @ 0.030 BHD/kWh", round(base["npv"], 2)])
ws.append(["Simple payback (years)", base["payback"]])
wb.save(os.path.join(results_dir, "lcc_analysis.xlsx"))
print("Saved: results/lcc_analysis.xlsx")
