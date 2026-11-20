"""Inject findings into the HTML template to make a self-contained report."""
import json, pandas as pd
f = json.load(open("out/findings.json")); b = json.load(open("out/backtest.json"))
pr = pd.read_csv("out/priority_list.csv").head(200)
pr["slope_bci_per_yr"] = pr["slope_bci_per_yr"].round(2)
pr["YEAR BUILT"] = pr["YEAR BUILT"].astype("Int64")
pr["proj_year_below_60"] = pr["proj_year_below_60"].astype("Int64")
f["top200"] = json.loads(pr.to_json(orient="records"))
f.pop("top25", None)
html = open("src/template.html").read().replace("__FINDINGS__", json.dumps(f, separators=(",", ":"))).replace("__BACKTEST__", json.dumps(b))
open("out/index.html", "w").write(html); print(len(html))
