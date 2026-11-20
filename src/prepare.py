"""Clean the MTO bridge conditions file and derive condition, age and deterioration features."""
import numpy as np, pandas as pd, sys
RAW = sys.argv[1] if len(sys.argv) > 1 else "data/bridge_condition_open_data_2020_en.csv"
YEARS = list(range(2000, 2021))

def band(b):
    if pd.isna(b): return "No BCI"
    return "Poor (<60)" if b < 60 else ("Fair (60-70)" if b < 70 else "Good (70+)")

def deterioration(row):
    """Slope of BCI per year since the later of last major rehab and 2008, using inspections only.
    Upward jumps > 5 points are treated as repairs: the fit restarts after the last such jump."""
    start = max(2008, row["LAST MAJOR REHAB"] if pd.notna(row["LAST MAJOR REHAB"]) else 0)
    pts = [(y, row[str(y)]) for y in YEARS if y >= start and pd.notna(row[str(y)])]
    # restart after last repair-like jump
    for i in range(len(pts) - 1, 0, -1):
        if pts[i][1] - pts[i - 1][1] > 5:
            pts = pts[i:]; break
    if len(pts) < 3 or pts[-1][0] - pts[0][0] < 4:
        return np.nan, len(pts)
    x = np.array([p[0] for p in pts], float); y = np.array([p[1] for p in pts], float)
    return float(np.polyfit(x, y, 1)[0]), len(pts)

def main():
    df = pd.read_csv(RAW, encoding="utf-8-sig", low_memory=False)
    df = df.rename(columns={"ID (SITE N°)": "ID"})
    for y in YEARS: df[str(y)] = pd.to_numeric(df[str(y)], errors="coerce")
    df["BCI"] = pd.to_numeric(df["CURRENT BCI"], errors="coerce")
    df["insp_date"] = pd.to_datetime(df["LAST INSPECTION DATE"], errors="coerce", format="%m/%d/%Y")
    df["band"] = df["BCI"].map(band)
    df["age_2020"] = 2020 - df["YEAR BUILT"]
    last_work = df[["YEAR BUILT", "LAST MAJOR REHAB"]].max(axis=1)
    df["yrs_since_major_work"] = 2020 - last_work
    df["deck_area_m2"] = df["DECK / CULVERTS LENGTH (m)"] * df["WIDTH TOTAL (m)"]
    res = df.apply(deterioration, axis=1, result_type="expand")
    df["slope_bci_per_yr"], df["n_points"] = res[0], res[1]
    # projected year BCI crosses 60 (only for declining structures currently >= 60)
    dec = df["slope_bci_per_yr"] < -0.05
    yrs = (df["BCI"] - 60) / (-df["slope_bci_per_yr"])
    df["proj_year_below_60"] = np.where(dec & (df["BCI"] >= 60), np.floor(2020 + yrs), np.nan)
    df.to_pickle("out/bridges_clean.pkl")
    print(df.shape, df["slope_bci_per_yr"].notna().sum(), "with trend")
    print(df["slope_bci_per_yr"].describe())

if __name__ == "__main__":
    main()
