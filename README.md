video: https://drive.google.com/drive/folders/1O2hiMFtYa8Op7YP0Dib7WD-Lv-kFhJZn?usp=sharing 

# SA-GSHP Bahrain Villa Simulation

EnergyPlus plus Python workflow for a solar-assisted ground source heat pump (SA-GSHP) feasibility study for a 300 m2 villa in Manama, Bahrain.

The project uses EnergyPlus 26.1 for the building and HVAC simulation, then passes the simulated hourly cooling load into Python scripts for annual system performance, borehole temperature drift, life-cycle cost, and environmental impact analysis.

## Current Validated Results

Latest full pipeline run: May 14, 2026

| Metric | Current result |
| --- | ---: |
| EnergyPlus annual cooling load | 28,837 kWh |
| Peak cooling load | 6.5 kW |
| Year 1 SA-GSHP electricity | 8,679 kWh |
| Year 1 system SCOP | 3.32 |
| 20-year ground drift with regeneration | +0.80 C |
| 20-year ground drift without regeneration | +4.20 C |
| Net lifecycle CO2 reduction | 24 tonnes CO2 |

EnergyPlus completes successfully with 0 severe errors. The remaining warning is that the design heating load is zero for `Villa_Living`, which is expected for this cooling-dominated Bahrain case.

## Project Structure

```text
SAGSHP/
|-- Bahrain_Villa_SA_GSHP.idf          EnergyPlus 26.1 building/HVAC model
|-- hourly_loads.csv                   Generated hourly cooling load used by Python
|-- python_scripts/
|   |-- run_complete_simulation.py     End-to-end pipeline
|   |-- sagshp_simulation.py           SA-GSHP annual performance
|   |-- borehole_sim.py                Ground thermal model
|   |-- lcc_analysis.py                Life-cycle cost analysis
|   |-- co2_analysis.py                Environmental analysis
|   |-- validate_all.py                Consistency checks
|   |-- requirements.txt               Python dependencies
|-- weather/
|   |-- Bahrain_Manama.epw             Weather file
|-- output/                            EnergyPlus outputs
|-- results/                           CSV/XLSX/PNG analysis outputs
```

## Requirements

- Python 3.8 or newer
- EnergyPlus 26.1.0
- Python packages listed in `python_scripts/requirements.txt`

Install Python dependencies:

```bash
pip install -r python_scripts/requirements.txt
```

## Run The Complete Pipeline

From the project root:

```bash
python python_scripts/run_complete_simulation.py
```

The pipeline:

1. Locates EnergyPlus.
2. Runs `Bahrain_Villa_SA_GSHP.idf` with `weather/Bahrain_Manama.epw`.
3. Reads the actual hourly cooling-rate time series from `output/eplusout.eso`.
4. Writes `hourly_loads.csv`.
5. Runs the SA-GSHP, borehole, economic, environmental, and validation scripts.
6. Regenerates the files in `results/`.

## Validation

The validation script checks that:

- `hourly_loads.csv` has 8,760 rows.
- Year 1 SCOP equals annual cooling divided by total electricity.
- Total electricity equals heat-pump electricity plus pump electricity.
- Ground drift with regeneration matches the target band.
- Ground drift without regeneration matches the unmanaged scenario.

Latest validation status: all checks passed.

## Primary Outputs

- `results/scop_annual.csv`
- `results/SCOP_Performance_Analysis.csv`
- `results/ground_temp_20yr.csv`
- `results/Ground_Temperature_Analysis.csv`
- `results/ground_temp_20yr.png`
- `results/Economic_Analysis_Results.csv`
- `results/lcc_analysis.xlsx`
- `results/Environmental_Impact_Analysis.csv`
- `results/co2_summary.csv`
- `results/simulation_log_*.txt`

## Model Notes

- The borehole field is modeled as a 2 x 2 vertical array, 100 m deep with 5 m spacing.
- Deep ground temperature for the borehole model is 30 C.
- Building-surface ground temperature is set to 25 C to stay inside EnergyPlus guidance for slab-contact temperatures.
- The water-to-air heat pump uses continuous fan operation to avoid low-flow part-load warnings.
- If EnergyPlus is unavailable, the Python workflow can still run with a synthetic load profile, but those results should be treated as fallback estimates rather than the validated EnergyPlus-driven case.
