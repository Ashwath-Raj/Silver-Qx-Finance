# Routing and placement experiment — O2 Portfolio QAOA

- Instance source status: `SYNTHETIC_DEMO_NOT_OFFICIAL`
- Fixed QAOA parameters: γ=1.28694986, β=1.31752548
- Shots per trial: 4096
- Compiler optimization level: 0
- Seeds per processor/strategy: 5
- Simulator: ideal Aer; no official hardware noise model is configured.

## Median resource metrics and mean sampled probabilities

| Processor | Strategy | Median CX | Median depth | Median SWAP diagnostic | Mean valid probability | Mean optimal probability |
|---|---|---:|---:|---:|---:|---:|
| A | Trivial + Basic | 27 | 53 | 5 | 0.5621 | 0.1087 |
| A | Trivial + SABRE | 18 | 34 | 2 | 0.5577 | 0.1089 |
| A | SABRE layout + SABRE routing | 18 | 44 | 2 | 0.5620 | 0.1082 |
| B | Trivial + Basic | 36 | 56 | 8 | 0.5570 | 0.1090 |
| B | Trivial + SABRE | 24 | 39 | 4 | 0.5585 | 0.1051 |
| B | SABRE layout + SABRE routing | 15 | 33 | 1 | 0.5607 | 0.1098 |

The strongest resource reductions were observed on Processor B with SABRE layout plus SABRE routing. On Processor A, trivial layout plus SABRE routing gave the lowest observed median depth. Probability differences are modest and should not be called statistically significant from five seeds. SWAP count is a separate diagnostic compile; CX/depth are measured after native-basis compilation.

These results are synthetic-instance, ideal-simulation measurements—not official noisy-device results, and not evidence of quantum advantage.
