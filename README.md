# Ontario Bridge Repair Priorities

Feras Elghandour · Public-sector data analysis, decision support and infrastructure risk

Which provincial bridges and culverts should Ontario repair first, and where is the repair backlog building? This project turns the Ministry of Transportation's open bridge-inspection file (5,053 structures, inspections 2000–2020) into a ranked repair list, regional and corridor findings, and four recommendations. The deterioration model is backtested against what actually happened.

**Report:** [`docs/index.html`](docs/index.html) (open it locally, or turn on GitHub Pages from `/docs`)
**Full ranked list:** [`out/priority_list.csv`](out/priority_list.csv)
**Business analysis:** [`BUSINESS_ANALYSIS.md`](BUSINESS_ANALYSIS.md)

## Key findings

| # | Finding | Evidence |
|---|---|---|
| 1 | **The north is falling behind.** 7.2% of Northwestern Region structures are poor (BCI < 60), compared with 0.3% in Central Region. | Condition bands by MTO region |
| 2 | **Culverts are the hidden backlog.** They are 40.7% of structures but 73.3% of poor ones. 137 culverts show a last inspection in 2017 or earlier. | Condition by structure type; inspection dates |
| 3 | **Need rises steeply with age.** 0.9% of structures under 20 years old are fair or poor; past 80 years it is 44.2%. A large group built in the 1950s–1970s is now 41–80 years old. | Condition by age in 2020 |
| 4 | **The pipeline is growing.** 118 structures were projected to fall below BCI 60 between 2020 and 2025, and 390 by 2030, if left untouched. | Per-structure deterioration trends |
| 5 | **Highway 17 carries the most repair need:** 41 of its 310 structures were poor, about to become poor, or fair and declining fast. Next: Highway 401 (33) and Highway 11 (26). | Corridor roll-up |

## Recommendations

1. **Rebalance capital toward northern corridors.** A province-wide average can meet its target while Highways 17 and 11 fall behind.
2. **Create a dedicated culvert inspection and replacement stream**, so culverts stop competing with high-profile bridges for the same budget.
3. **Fund the "fair window."** 52 structures were projected to turn poor by 2023, and 107 more were fair and losing more than 0.5 BCI points a year. MTO guidance identifies the 60–70 band as the most economical time to repair.
4. **Publish current data, with traffic volume and completed-work history.** The open file stops at 2020, and 36.2% of records have no county.

## Method

| Step | What it does |
|---|---|
| `src/prepare.py` | Cleans the MTO file. Assigns MTO condition bands (good 70+, fair 60–70, poor < 60). Derives age, years since major work and deck area. Fits each structure's BCI trend since the later of 2008 and its last major rehab, restarting after any jump of more than 5 points (a repair). |
| `src/analyse.py` | Holds out 18 records with conflicting data (built 2016 or later but BCI under 65). Builds a percentile-based priority score, then assigns rule-based tiers. Produces the regional, structure-type, age and corridor views. Tests five weightings. |
| `src/backtest.py` | Uses only inspections to 2016 to predict which structures fall below 60 by 2020, and compares the trend model with a condition-only rule. |
| `src/build_report.py` | Writes the self-contained HTML report. |

**Priority score:** 50% condition need, 25% deterioration speed, 15% size (deck or culvert area, a stand-in for consequence because the open data has no traffic counts), 10% time since major work.

**How far to trust it**
- Under four alternative weightings, the top 50 kept 34–43 of the same structures. 21 structures appear in the top 50 under every weighting.
- In the backtest, the trend model and the condition-only rule each flagged 85 structures and both caught 12 of the 27 that actually fell below 60. The trend did not pick better structures than current condition, but it forecast 2020 BCI within a median 2.0 points.
- **Conclusion:** use condition to choose which structures, and trends to size the coming workload.

## Limits

- The BCI measures state of repair, not safety or load capacity.
- The public file was last updated in June 2021, so many structures here will have been repaired since. Verify against MTO's current records before acting.
- Projections are straight-line, no-intervention extrapolations.
- Size stands in for consequence. The data has no traffic volume, detour length or freight use.
- 11 records have missing or zero coordinates and 52 have no BCI.

## Reproduce

```bash
./run_all.sh        # Python 3.10+, pandas, numpy, openpyxl
```

The script rebuilds every file in `out/` and `docs/` from the raw CSV and runs the unit tests in `tests/`.

## Data and licence

Data: Ontario Ministry of Transportation, [Bridge conditions](https://data.ontario.ca/dataset/bridge-conditions), Open Government Licence – Ontario. Contains information licensed under the Open Government Licence – Ontario. The analysis code is MIT-licensed.
