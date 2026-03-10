#!/usr/bin/env python3
"""
extract_excerpts.py

Extracts 50 stratified Item-7 (MD&A) excerpts for the human validation survey.
Stratified by LLM readability score tercile (low / medium / high), with each
firm appearing at most once.

Output: excerpts.json  (loaded by index.html)

Usage:
    python extract_excerpts.py
"""

import pandas as pd
import numpy as np
import json
import re
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────
BASE      = Path("/Users/cemsinanozturk/Desktop/thesis_combine")
SCORES    = BASE / "llm_readability_scores_CORRECTED.csv"
TEXT_ROOT = BASE / "thesis_ui_project/SP1500allNew"
OUT       = Path(__file__).parent / "excerpts.json"

SEED       = 42
N          = 50    # total excerpts
SKIP_W     = 150   # skip opening boilerplate words
TAKE_W     = 300   # excerpt length in words

TERCILE_TARGETS = {"low": 17, "medium": 17, "high": 16}
# ───────────────────────────────────────────────────────────────────────────


def load_scores() -> pd.DataFrame:
    """Load firm-year overall readability scores for stratification."""

    # Prefer the firm-year combined file (small, already aggregated)
    combined = BASE / "clean_pipeline/data/readability_llm_combined.csv"
    if combined.exists():
        print("Loading combined scores from clean_pipeline ...")
        df = pd.read_csv(combined, dtype={"cik": str})
        # Identify the score column: anything that is not cik or fiscal_year
        score_col = next(c for c in df.columns if c not in ("cik", "fiscal_year"))
        df = df.rename(columns={score_col: "score"})
        df["year"] = df["fiscal_year"].astype(int)
        print(f"  {len(df):,} firm-year records (column: '{score_col}')")
        return df[["cik", "year", "score"]]

    # Fallback: read the large scores file (only Item7, needed columns)
    print(f"Loading scores from llm_readability_scores_CORRECTED.csv …")
    print("  (this file is large — may take ~30 s)")
    df = pd.read_csv(
        SCORES,
        usecols=["id", "overall_readability_score", "ff48_name"],
        dtype={"id": str, "ff48_name": str},
    )
    df = df[df["id"].str.endswith("_Item7.txt")].copy()
    m  = df["id"].str.extract(r"^(?P<cik>\d+)_(?P<year>\d{4})_Item7\.txt$")
    df = df.join(m).dropna(subset=["cik", "year"])
    df["year"] = df["year"].astype(int)

    # Average in case of duplicate rows
    df = (
        df.groupby(["cik", "year"], as_index=False)["overall_readability_score"]
        .mean()
        .rename(columns={"overall_readability_score": "score"})
    )
    print(f"  {len(df):,} unique Item-7 documents")
    return df[["cik", "year", "score"]]


def read_excerpt(cik: str, year: int) -> str | None:
    """Read a 300-word window from words 150-450 of the Item-7 file."""
    path = TEXT_ROOT / str(year) / cik / f"{cik}_{year}_Item7.txt"
    if not path.exists():
        return None
    raw   = path.read_text(encoding="utf-8", errors="ignore")
    words = re.sub(r"\s+", " ", raw).strip().split()
    if len(words) < SKIP_W + TAKE_W:
        return None
    return " ".join(words[SKIP_W : SKIP_W + TAKE_W])


def main() -> None:
    rng = np.random.default_rng(SEED)

    df = load_scores()

    # Assign tercile labels based on score distribution
    df["tercile"] = pd.qcut(
        df["score"], q=3, labels=["low", "medium", "high"]
    )

    excerpts   = []
    used_ciks  = set()
    counts     = {t: 0 for t in TERCILE_TARGETS}

    for tercile, target in TERCILE_TARGETS.items():
        pool = (
            df[df["tercile"] == tercile]
            .sample(frac=1, random_state=SEED)  # shuffle
            .reset_index(drop=True)
        )
        collected = 0
        for _, row in pool.iterrows():
            if collected >= target:
                break
            if row["cik"] in used_ciks:
                continue
            text = read_excerpt(row["cik"], row["year"])
            if text is None:
                continue
            used_ciks.add(row["cik"])
            collected += 1
            excerpts.append(
                {
                    "internal_id": f"{row['cik']}_{row['year']}",
                    "tercile":     tercile,
                    "text":        text,
                }
            )
        counts[tercile] = collected
        print(f"  {tercile:6s}: {collected}/{target} excerpts collected")

    total = sum(counts.values())
    if total < N:
        print(f"\nWARNING: only {total} excerpts collected (target {N}).")
        print("Check that TEXT_ROOT points to the 10-K text files.")

    # Shuffle for presentation order (raters should not see a pattern)
    rng.shuffle(excerpts)
    for i, exc in enumerate(excerpts, 1):
        exc["display_order"] = i

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(excerpts, indent=2, ensure_ascii=False))
    print(f"\nSaved {len(excerpts)} excerpts to {OUT}")
    print("Next step: push this folder to GitHub and enable GitHub Pages.")


if __name__ == "__main__":
    main()
