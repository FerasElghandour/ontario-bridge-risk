"""Findings, transparent priority score, sensitivity check and exports."""
import json, numpy as np, pandas as pd
df = pd.read_pickle("out/bridges_clean.pkl")
act = df[df["BCI"].notna()].copy()
# Records whose build year says "new" but whose BCI says "worn" most likely mix a replacement's
# build year with the old structure's inspection history. Hold them out of the ranking for review.
conflict = (act["YEAR BUILT"] >= 2016) & (act["BCI"] < 65)
conflicts = act[conflict][["ID", "STRUCTURE NAME", "HIGHWAY NAME", "YEAR BUILT", "BCI"]]
act = act[~conflict].copy()

def pct(s, ascending=True):
    return s.rank(pct=True, ascending=ascending)

slope = act["slope_bci_per_yr"].fillna(act["slope_bci_per_yr"].median())
comp = pd.DataFrame({
    "C": pct(act["BCI"], ascending=False),          # lower BCI -> higher need
    "D": pct(slope, ascending=False),               # faster decline -> higher need
    "S": pct(act["deck_area_m2"].fillna(act["deck_area_m2"].median())),  # larger asset -> larger consequence/cost
    "T": pct(act["yrs_since_major_work"].fillna(act["yrs_since_major_work"].median())),
}, index=act.index)
W = {"base": (0.50, 0.25, 0.15, 0.10), "condition_heavy": (0.70, 0.15, 0.10, 0.05),
     "trend_heavy": (0.35, 0.40, 0.15, 0.10), "size_heavy": (0.40, 0.20, 0.30, 0.10),
     "equal": (0.25, 0.25, 0.25, 0.25)}
for k, w in W.items():
    act[f"score_{k}"] = (comp.values * np.array(w)).sum(axis=1) * 100
act["priority_score"] = act["score_base"].round(1)
act["rank"] = act["priority_score"].rank(ascending=False, method="first").astype(int)
top50 = set(act.nsmallest(50, "rank").index)
stab = {k: len(top50 & set(act.nlargest(50, f"score_{k}").index)) for k in W}
core = set.intersection(*[set(act.nlargest(50, f"score_{k}").index) for k in W])
act["robust_top50"] = act.index.isin(core)

def tier(r):
    if r["BCI"] < 60: return "1 - Poor now"
    if pd.notna(r["proj_year_below_60"]) and r["proj_year_below_60"] <= 2023: return "2 - Projected poor by 2023"
    if r["BCI"] < 70 and r["slope_bci_per_yr"] < -0.5: return "3 - Fair and declining fast"
    return "4 - Monitor"
act["tier"] = act.apply(tier, axis=1)

n = len(act)
f = {}
f["n_structures"] = int(len(df)); f["n_with_bci"] = n
f["data_conflicts"] = json.loads(conflicts.to_json(orient="records"))
f["bad_coords"] = int(((df.LATITUDE < 41) | (df.LONGITUDE > -74) | df.LATITUDE.isna()).sum())
f["bands"] = act["band"].value_counts().to_dict()
f["bands_pct"] = (act["band"].value_counts(normalize=True) * 100).round(1).to_dict()
f["region"] = (pd.crosstab(act.REGION, act.band, normalize="index") * 100).round(1).reset_index().to_dict("records")
f["region_counts"] = pd.crosstab(act.REGION, act.band).reset_index().to_dict("records")
cat = pd.crosstab(act.CATEGORY, act.band)
f["category"] = cat.reset_index().to_dict("records")
f["culvert_share_all"] = round(100 * (act.CATEGORY == "Culvert").mean(), 1)
f["culvert_share_poor"] = round(100 * (act.loc[act.BCI < 60, "CATEGORY"] == "Culvert").mean(), 1)
f["tiers"] = act["tier"].value_counts().sort_index().to_dict()
proj = act["proj_year_below_60"].value_counts().sort_index()
f["projected_cross_60"] = {int(k): int(v) for k, v in proj[proj.index <= 2030].items()}
f["proj_by_2025"] = int((act["proj_year_below_60"] <= 2025).sum())
f["proj_by_2030"] = int((act["proj_year_below_60"] <= 2030).sum())
f["median_slope"] = round(float(act["slope_bci_per_yr"].median()), 2)
f["n_with_trend"] = int(act["slope_bci_per_yr"].notna().sum())
age_bins = pd.cut(act["age_2020"], [0, 20, 40, 60, 80, 200], labels=["0-20", "21-40", "41-60", "61-80", "80+"])
f["age"] = act.groupby(age_bins, observed=True).agg(n=("BCI", "size"), mean_bci=("BCI", "mean"),
          pct_poor_fair=("BCI", lambda s: 100 * (s < 70).mean())).round(1).reset_index().astype({"age_2020": str}).to_dict("records")
act["COUNTY"] = act["COUNTY"].fillna("Not recorded")
hw = act.assign(p=(act.tier.str[0].isin(["1", "2", "3"]))).groupby("HIGHWAY NAME").agg(
    structures=("BCI", "size"), action=("p", "sum"), mean_bci=("BCI", "mean"),
    regions=("REGION", lambda s: ", ".join(sorted(s.dropna().unique())))).reset_index()
hw["action_pct"] = (100 * hw.action / hw.structures).round(1)
f["highway_hotspots"] = hw[hw.structures >= 20].sort_values("action", ascending=False).head(12).round(1).to_dict("records")
f["county_missing_pct"] = round(100 * df["COUNTY"].isna().mean(), 1)
insp_old = df[df.insp_date.dt.year <= 2017]
f["inspection_gap"] = {"last_inspected_2017_or_earlier": int(len(insp_old)),
                       "by_category": insp_old.CATEGORY.value_counts().to_dict(),
                       "missing_bci": int(df.BCI.isna().sum())}
f["stability_top50"] = stab; f["robust_core"] = len(core)
f["weights"] = W
f["deck_area_fair_poor_m2"] = int(act.loc[act.BCI < 70, "deck_area_m2"].sum())
cols = ["rank", "ID", "STRUCTURE NAME", "HIGHWAY NAME", "COUNTY", "REGION", "CATEGORY", "MATERIAL 1", "YEAR BUILT",
        "LAST MAJOR REHAB", "BCI", "slope_bci_per_yr", "proj_year_below_60", "deck_area_m2", "tier", "priority_score", "robust_top50",
        "LATITUDE", "LONGITUDE"]
pr = act.sort_values("rank")[cols]
pr.to_csv("out/priority_list.csv", index=False)
top = pr.head(25).copy()
top["slope_bci_per_yr"] = top["slope_bci_per_yr"].round(2)
f["top25"] = json.loads(top.to_json(orient="records"))
pts = act[["LATITUDE", "LONGITUDE", "BCI", "tier", "STRUCTURE NAME", "rank"]].dropna(subset=["LATITUDE", "LONGITUDE"])
pts = pts[(pts.LATITUDE.between(41, 57)) & (pts.LONGITUDE.between(-96, -74))]
f["map_points"] = [[round(a, 4), round(b, 4), round(c, 1), t[0], s, int(r)] for a, b, c, t, s, r in pts.itertuples(index=False)]
json.dump(f, open("out/findings.json", "w"), default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: v for k, v in f.items() if k not in ("top25", "map_points", "highway_hotspots", "age", "region", "region_counts")}, indent=1, default=str))
print(pd.DataFrame(f["highway_hotspots"]).to_string()); print(pd.DataFrame(f["age"]).to_string())
print(pr.head(15)[["rank","STRUCTURE NAME","HIGHWAY NAME","COUNTY","CATEGORY","BCI","slope_bci_per_yr","tier","priority_score"]].to_string())
