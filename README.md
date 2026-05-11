# Labor Market Analysis: The Perception Gap

Four interactive visualizations arguing that BLS headline labor market metrics structurally misrepresent actual U.S. labor market conditions. Built for CPSC 4530: Data Visualization and Exploration at the University of Tennessee at Chattanooga.

**Thesis:** Despite continuously reported job growth, the labor force has contracted, prime-age employment participation remains below pre-pandemic levels, headline unemployment suppresses millions of discouraged workers, and BLS figures have been revised away at record rates correlating with periods of economic contraction.

---

## Visualizations

### Viz 1 - The Two Surveys Tell Opposite Stories
Establishment (payroll) survey vs. Household (CPS) survey normalized to January 2010. The two surveys measure the same labor market using different instruments and have diverged by 4.4 million workers as of March 2026. Interactive buttons reveal the suppressed counter-metric and reframe the y-axis between two interpretations of the same data.

### Viz 2 - The Headline Hides the Floor
U-3 headline unemployment vs. U-6 broad unemployment alongside labor force participation and prime-age employment-population ratio. Approximately 6.3 million workers are currently invisible to the headline figure. Participation has not recovered to its January 2020 baseline despite five years of reported job growth.

### Viz 3 - Where Did the Money Go?
M2 money supply, Federal Reserve balance sheet, CPI, purchasing power, and real median personal income all indexed to 2010=100. Money supply grew 2.2x faster than real wages since 2010. The Fed balance sheet doubled within 12 months of pandemic QE. Surplus liquidity redirected into AI capital investment rather than wage compensation.

### Viz 4 - The Numbers That Never Were
Annual BLS benchmark revisions from 2007 through 2024. The three most recent years represent the largest consecutive overstatements ever recorded - a cumulative 2,552K jobs announced and later revised away. Overstatements cluster before the 2008 financial crisis and again before the current slowdown.

---

## Data Sources

| Dataset | Source | Access |
|---|---|---|
| BLS Employment Situation (PAYEMS, CE16OV, UNRATE, U6RATE, CIVPART, LNS12300060, CLF16OV) | Federal Reserve Bank of St. Louis FRED | FRED API |
| Federal Reserve Monetary Data (M2SL, WALCL, CPIAUCSL, MEPAINUSA672N) | Federal Reserve / Census Bureau via FRED | FRED API |
| BLS Annual Benchmark Revisions | BLS benchmark revision press releases | Manually compiled |

- FRED API: https://fred.stlouisfed.org
- BLS benchmark revisions: https://www.bls.gov/web/empsit/cesnaicsrev.htm

---

## Stack

- **Python 3.11**
- **Plotly** - interactive figure construction
- **pandas** - time series alignment and preprocessing
- **numpy** - purchasing power derivation, hidden unemployment conversion
- **fredapi** - programmatic FRED data retrieval

---

## Setup

```bash
pip install plotly pandas numpy fredapi
```

Run the interactive script:

```bash
python src/data_viz_interactive.py
```

Outputs four HTML files to `outputs/`. Open any in a browser - no server required.

---

## Project Structure

```
labor-market-analysis/
  src/
    data_viz_interactive.py
  outputs/
    viz1_survey_divergence.html
    viz2_unemployment_depth.html
    viz3_qe_wages.html
    viz4_bls_revisions.html
  README.md
  .gitignore
```

---

## Rhetorical Design

Visualizations were designed using the frameworks of Prantl et al. (2026) on pathos and aesthetic design and Lin et al. (2026) on visual rhetoric and persuasive cartography. Design choices - line weight, color saturation, controlled revelation via buttons, framing toggles - are documented inline in the source code.