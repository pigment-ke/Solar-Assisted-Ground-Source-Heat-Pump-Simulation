import numpy as np
import pandas as pd

# Heat pump COP versus entering water temperature
EWT = np.arange(25, 40, 0.5)
COP_ref = 6.0
EWT_ref = 30.0
dCOP_dT = -0.20

COP_cooling = np.maximum(2.0, COP_ref + dCOP_dT * (EWT - EWT_ref))

df = pd.DataFrame({"EWT_C": EWT, "COP_cooling": COP_cooling})
df.to_csv("hp_cop_table.csv", index=False)

print("HP COP table:")
print(df.to_string(index=False))
print(f"\nAt UGT=30C: COP = {np.interp(30, EWT, COP_cooling):.2f}")
print(f"At EWT=34C: COP = {np.interp(34, EWT, COP_cooling):.2f} (degraded)")
