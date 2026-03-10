# Human Validation Survey — Setup Guide

## Step 1: Generate the excerpts

Run the extraction script (takes ~30s due to large scores file):

```bash
cd /Users/cemsinanozturk/Desktop/thesis_combine/human_validation
python extract_excerpts.py
```

This produces `excerpts.json` (50 anonymised 300-word excerpts).
Check the console output — all three terciles should show 17/17/16.

---

## Step 2: Deploy to GitHub Pages (free)

### 2a. Create a new GitHub repository

Go to github.com → New repository.
- Name: `readability-survey` (or any name)
- Visibility: **Public** (required for free GitHub Pages)
- Do NOT initialise with README

### 2b. Push the two files

```bash
cd /Users/cemsinanozturk/Desktop/thesis_combine/human_validation
git init
git add index.html excerpts.json
git commit -m "Add readability survey"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/readability-survey.git
git push -u origin main
```

### 2c. Enable GitHub Pages

1. Go to your repo on GitHub
2. Settings → Pages
3. Source: **Deploy from a branch**
4. Branch: `main`, folder: `/ (root)`
5. Click Save
6. Wait ~60 seconds, then your URL will be:

```
https://YOUR_USERNAME.github.io/readability-survey/
```

### 2d. Share with raters

Send each rater this URL. Each rater:
- Opens the URL in any browser
- Enters their name
- Completes 50 ratings (progress is auto-saved locally)
- Downloads their CSV at the end
- Emails you the CSV file

---

## Step 3: Collect and analyse results

You will receive two CSV files (one per rater). Analyse with:

```python
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
import pingouin as pg

# Load rater CSVs
r1 = pd.read_csv("readability_ratings_Rater1.csv")
r2 = pd.read_csv("readability_ratings_Rater2.csv")

merged = r1.merge(r2, on="internal_id", suffixes=("_r1", "_r2"))

# --- Inter-rater reliability: ICC(2,1) ---
for dim in ["structural_clarity", "contextual_quality", "overall_readability"]:
    long = pd.DataFrame({
        "target": list(range(len(merged))) * 2,
        "rater":  ["r1"] * len(merged) + ["r2"] * len(merged),
        "score":  list(merged[f"{dim}_r1"]) + list(merged[f"{dim}_r2"])
    })
    icc = pg.intraclass_corr(data=long, targets="target", raters="rater", ratings="score")
    row = icc[icc["Type"] == "ICC2"]
    print(f"{dim}: ICC(2,1) = {row['ICC'].values[0]:.3f} "
          f"[{row['CI95%'].values[0][0]:.3f}, {row['CI95%'].values[0][1]:.3f}]")

# --- Convergent validity: human mean vs LLM scores ---
merged["human_overall_mean"] = (
    merged["overall_readability_r1"] + merged["overall_readability_r2"]
) / 2

# Load LLM scores (adjust path as needed)
llm = pd.read_csv("../clean_pipeline/data/readability_llm_combined.csv")
# ... merge on internal_id (cik_year) and compute Spearman rho
```

---

## Important notes

- **Raters do NOT see** firm names, CIK numbers, or years — only the text excerpt.
- Each rater's browser stores their progress locally (localStorage).
  If they clear their browser cache, progress will be lost. Advise them not to do this.
- The `internal_id` column in the CSV (`cik_year`) is used by you to match
  rater scores back to LLM scores. Do not share this column with raters.
- Sliders default to 5 (neutral) and are marked unset (grey) until moved.
  Raters must interact with all three sliders before advancing to the next excerpt.
