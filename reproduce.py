"""Rebuild the case and all seeded runs, then compare them to the archived outputs."""

import csv
import json
import math
import os
from pathlib import Path
from statistics import mean
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
TOLERANCE = 1e-6


def compare(actual, expected, field):
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError(f"{field}: field names differ")
        for key in expected:
            compare(actual[key], expected[key], f"{field}.{key}")
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise ValueError(f"{field}: lengths differ")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{field}[{index}]")
    elif isinstance(expected, float):
        if not math.isclose(actual, expected, rel_tol=0, abs_tol=TOLERANCE):
            raise ValueError(f"{field}: expected {expected}, got {actual}")
    elif actual != expected:
        raise ValueError(f"{field}: expected {expected}, got {actual}")


def read_runs(path):
    runs = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (row["algorithm"], int(row["seed"]))
            if key in runs:
                raise ValueError(f"{path}: duplicate run {key}")
            runs[key] = {
                field: float(value) if field == "best_score" else int(value)
                for field, value in row.items() if field not in ("algorithm", "seed")
            }
    keys = {(algorithm, seed) for algorithm in ("HHO", "MSPSO", "FPSOHHO") for seed in range(20)}
    if runs.keys() != keys:
        raise ValueError(f"{path}: expected 20 seeds for each of the three algorithms")
    return runs


def main():
    env = {**os.environ, "MPLBACKEND": "Agg", "PYTHONIOENCODING": "utf-8"}
    options = {"env": env, "cwd": ROOT, "check": True}
    with TemporaryDirectory() as directory:
        case_file = Path(directory) / "case.json"
        runs_file = Path(directory) / "runs.csv"
        with case_file.open("wb") as output:
            subprocess.run([sys.executable, "verify_case.py", "original"], stdout=output, **options)
        case = json.loads(case_file.read_text(encoding="utf-8-sig"))
        archived_case = json.loads((ROOT / "results/case.json").read_text(encoding="utf-8-sig"))
        compare(case, archived_case, "case")
        print(f"Exact objective: {case['exact_score']:.6f}. Running the three searches...", flush=True)
        subprocess.run([sys.executable, "check_search.py", "original", case_file, runs_file], **options)
        runs = read_runs(runs_file)
        compare(runs, read_runs(ROOT / "results/runs.csv"), "runs")

    print("Algorithm   Mean score   Optimum hits")
    for algorithm in ("MSPSO", "FPSOHHO", "HHO"):
        scores = [row["best_score"] for (name, _), row in runs.items() if name == algorithm]
        hits = sum(abs(score - case["exact_score"]) <= TOLERANCE for score in scores)
        print(f"{algorithm:<9}   {mean(scores):>8.1f}   {hits:>2}/20")
    print("Verified the case and all 60 archived runs.")


if __name__ == "__main__":
    main()
