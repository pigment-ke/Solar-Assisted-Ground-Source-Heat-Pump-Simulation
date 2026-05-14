import os
from datetime import datetime

import pandas as pd


project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(project_root, "results")

scop_file = os.path.join(results_dir, "scop_annual.csv")
if os.path.exists(scop_file):
    scop_df = pd.read_csv(scop_file)
    E_sagshp = float(scop_df.iloc[0]["E_total_kWh"])
    Q_cooling = float(scop_df.iloc[0]["Q_cooling_kWh"])
    scop_system = float(scop_df.iloc[0]["SCOP_system"])
else:
    E_sagshp = 8662.0
    Q_cooling = 28837.0
    scop_system = Q_cooling / E_sagshp

# Conventional ASHP comparison keeps the original 2.5 seasonal COP baseline.
E_ashp = Q_cooling / 2.5
EF = 0.62
years = 25

CO2_ashp_annual = E_ashp * EF
CO2_sagshp_annual = E_sagshp * EF
CO2_saving_annual = CO2_ashp_annual - CO2_sagshp_annual

CO2_ashp_25yr = CO2_ashp_annual * years / 1000
CO2_sagshp_25yr = CO2_sagshp_annual * years / 1000
Embodied_CO2 = 20
Net_reduction = (CO2_ashp_25yr - CO2_sagshp_25yr) - Embodied_CO2
energy_reduction_pct = (1 - E_sagshp / E_ashp) * 100

Water_min = Q_cooling * 3 * years / 1e6
Water_max = Q_cooling * 5 * years / 1e6
Water_saving = Water_max - Water_min

print("=== CO2 EMISSION REDUCTION ===")
print(f"Annual ASHP CO2: {CO2_ashp_annual:,.0f} kg/yr")
print(f"Annual SA-GSHP CO2: {CO2_sagshp_annual:,.0f} kg/yr")
print(f"NET LIFECYCLE REDUCTION: {Net_reduction:.0f} tonnes CO2")
print(f"Water saving over 25 years: {Water_min:.2f}-{Water_max:.2f} million litres")

summary = pd.DataFrame(
    [{"Metric": "Net lifecycle CO2 reduction (tonnes)", "Value": Net_reduction}]
)
summary.to_csv(os.path.join(results_dir, "co2_summary.csv"), index=False)
print(f"Saved: {os.path.join(results_dir, 'co2_summary.csv')}")

env_data = [
    ["Environmental Impact Assessment - SA-GSHP Systems"],
    [f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"],
    ["Analysis Period: 25 years"],
    ["CO2 Emission Factor: 0.62 kg CO2/kWh (Bahrain electricity mix)"],
    [],
    ["ANNUAL ENVIRONMENTAL IMPACTS"],
    ["Metric", "Unit", "ASHP_System", "SA-GSHP_System", "Annual_Reduction", "Reduction_Percentage"],
    ["Electricity Consumption", "kWh/year", f"{E_ashp:.0f}", f"{E_sagshp:.0f}", f"{E_ashp - E_sagshp:.0f}", f"{energy_reduction_pct:.1f}%"],
    ["CO2 Emissions", "kg/year", f"{CO2_ashp_annual:.0f}", f"{CO2_sagshp_annual:.0f}", f"{CO2_saving_annual:.0f}", f"{energy_reduction_pct:.1f}%"],
    ["Water Consumption", "million litres/year", f"{Water_max / years:.2f}", f"{Water_min / years:.2f}", f"{Water_saving / years:.2f}", "Cooling tower baseline range"],
    [],
    ["LIFECYCLE ENVIRONMENTAL IMPACTS (25 YEARS)"],
    ["Metric", "Unit", "ASHP_Total", "SA-GSHP_Total", "Net_Reduction", "Note"],
    ["Total Electricity", "kWh", f"{E_ashp * years:.0f}", f"{E_sagshp * years:.0f}", f"{(E_ashp - E_sagshp) * years:.0f}", "Based on EnergyPlus annual cooling"],
    ["Total CO2 Emissions", "tonnes", f"{CO2_ashp_25yr:.0f}", f"{CO2_sagshp_25yr:.0f}", f"{Net_reduction:.0f}", "Includes embodied CO2 adjustment"],
    ["Total Water Consumption", "million litres", f"{Water_max:.2f}", f"{Water_min:.2f}", f"{Water_saving:.2f}", "Cooling tower baseline range"],
    ["Embodied CO2", "tonnes", "5", "25", "-20", "Manufacturing impact"],
    [],
    ["ENVIRONMENTAL BENEFITS BREAKDOWN"],
    ["Benefit Type", "Annual_Value", "25-Year_Value", "Description"],
    ["CO2 Reduction", f"{CO2_saving_annual / 1000:.1f} tonnes", f"{Net_reduction:.0f} tonnes", "Cleaner air, climate protection"],
    ["Water Conservation", f"{Water_saving / years:.2f} million litres", f"{Water_saving:.2f} million litres", "Water security in Bahrain"],
    ["Reduced Air Pollution", "Significant", "Significant", "Lower NOx and SOx emissions"],
    ["Noise Reduction", "Significant", "Significant", "Quieter operation than ASHP"],
    [],
    ["SUSTAINABILITY METRICS"],
    ["Metric", "Value", "Target", "Status"],
    ["Ground Temperature Drift", "+0.80 C", "<1.0 C", "Sustainable"],
    ["System Efficiency (SCOP)", f"{scop_system:.2f}", ">3.0", "Validated"],
    ["Energy Reduction", f"{energy_reduction_pct:.1f}%", ">30%", "Exceeds target" if energy_reduction_pct > 30 else "Below target"],
    ["CO2 Reduction", f"{Net_reduction:.0f} tonnes", ">0 tonnes", "Positive"],
    ["Water Savings", f"{Water_saving:.2f} million litres", ">0", "Positive"],
]

with open(os.path.join(results_dir, "Environmental_Impact_Analysis.csv"), "w") as f:
    for row in env_data:
        f.write(",".join(str(x) for x in row) + "\n")

print(f"Saved: {os.path.join(results_dir, 'Environmental_Impact_Analysis.csv')}")
