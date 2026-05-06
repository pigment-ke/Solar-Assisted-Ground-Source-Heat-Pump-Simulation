import pandas as pd
import os
import sys

print("=" * 65)
print("  SA-GSHP SIMULATION VALIDATION REPORT")
print("=" * 65)

# Get the project root directory
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
results_dir = os.path.join(project_root, "results")
scop_df = pd.read_csv(os.path.join(results_dir, "scop_annual.csv"))
gt_df = pd.read_csv(os.path.join(results_dir, "ground_temp_20yr.csv"))

checks = [
    ("SCOP (Year 1)", scop_df.iloc[0]["SCOP_system"], 4.5, 0.3),
    ("Annual elec. SA-GSHP", scop_df.iloc[0]["E_total_kWh"], 15556, 1500),
    ("Ground drift (20yr)", gt_df.iloc[-1]["T_ground_with_regen_C"] - 30.0, 0.8, 0.3),
    ("Ground drift unmanaged", gt_df.iloc[-1]["T_ground_without_regen_C"] - 30.0, 4.2, 0.5),
]

all_pass = True
for name, got, target, tolerance in checks:
    diff = abs(got - target)
    status = "PASS" if diff <= tolerance else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"{name:<30} Got: {got:>8.2f}  Target: {target:>8.2f}  {status}")

print("-" * 65)
if all_pass:
    print("ALL CHECKS PASSED")
else:
    print("SOME CHECKS FAILED")
print("=" * 65)
