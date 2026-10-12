"""Legacy routing experiments are archived under experiments/legacy_synthetic/.
Run `python main.py --q <value>` for the Master Guide-controlled baseline.
The required baseline is fixed to optimization level 1, SABRE layout/routing,
transpiler seed 42, and 4096 shots. Supplementary compiler sweeps should be added
as separately labelled experiments after the required baseline is reproducible.
"""
if __name__ == "__main__":
    print("Run the Master Guide baseline with: python main.py --q <positive-q>")
