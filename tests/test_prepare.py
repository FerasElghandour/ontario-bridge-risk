import sys, os, unittest
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from prepare import band, deterioration, YEARS

def row(hist, major=np.nan):
    r = {str(y): np.nan for y in YEARS}; r.update({str(k): v for k, v in hist.items()}); r["LAST MAJOR REHAB"] = major
    return pd.Series(r)

class T(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(band(59.99), "Poor (<60)"); self.assertEqual(band(60), "Fair (60-70)")
        self.assertEqual(band(70), "Good (70+)"); self.assertEqual(band(np.nan), "No BCI")
    def test_linear_decline(self):
        s, n = deterioration(row({2010: 80, 2012: 78, 2014: 76, 2016: 74}))
        self.assertAlmostEqual(s, -1.0, places=6); self.assertEqual(n, 4)
    def test_repair_jump_restarts_trend(self):
        s, n = deterioration(row({2008: 70, 2010: 65, 2012: 85, 2014: 84, 2016: 83}))
        self.assertAlmostEqual(s, -0.5, places=6); self.assertEqual(n, 3)
    def test_too_few_points(self):
        s, n = deterioration(row({2018: 70, 2020: 69}))
        self.assertTrue(np.isnan(s))
    def test_ignores_before_major_rehab(self):
        s, n = deterioration(row({2008: 50, 2010: 48, 2014: 90, 2016: 89, 2018: 88}, major=2013))
        self.assertAlmostEqual(s, -0.5, places=6)

if __name__ == "__main__":
    unittest.main()
