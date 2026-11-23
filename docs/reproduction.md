# Reproducing the 12-stop case

[Repository home](../README.md) · [中文说明](../README.zh-CN.md)

## From inputs to reference value

The [integer model](../original/goal.py) contains the ordered stop coordinates, directed passenger demand matrix, two fixed-route sequences and class-specific costs and capacities. Four outer decisions pin the numbers of large and medium buses in the forward and reverse directions. CBC allocates nonnegative integer numbers of minibuses.

All minibus marginal costs in this instance are positive. Each directed pair outside the fixed legs therefore takes the smallest number of minibuses that covers its demand, rounded up at ten seats per minibus. The total is 224, within the fleet limit of 250. This fixes 2889.713184 units of the objective. Each route must cover the larger of its aggregate demand and its peak segment load. With 30 effective seats per large bus and eight per medium bus, every pair of large-bus counts determines the minimum number of medium buses required. The [reference calculation](../reference.py) uses these aggregates. The [independent check](../verify_case.py) derives them from the original model and solves the integer program with the four fixed counts released.

The five-minute minibus filter in the original model applies to fixed-route legs. Fixed-route and direct demand constraints can cover overlapping passenger flows. The reported objective quantifies this allocation model on one corridor.

## Keep a fresh set of outputs

The main command, `python reproduce.py`, uses temporary files. To retain the generated JSON and CSV alongside the repository, run the following from its root after installing [the pinned dependencies](../requirements.txt).

```sh
python verify_case.py original > fresh_case.json
python check_search.py original fresh_case.json fresh_runs.csv
```

Windows PowerShell 5.1 users can write the first output in UTF-8 with `python verify_case.py original | Out-File -Encoding utf8 fresh_case.json`. The archived comparison used Python 3.10.18, NumPy 2.2.6, Matplotlib 3.10.7 and PuLP 3.3.0 with CBC. The GitHub workflow uses Windows and CPython 3.10.11 with the same pinned package versions. The plotting import in the original model is used in a headless environment by the one-command runner.

## Read a run

Each row in [runs.csv](../results/runs.csv) represents one algorithm and one seed.

| CSV field | Meaning |
| --- | --- |
| `seed`, `algorithm` | Seeds 0 through 19, paired across HHO, MSPSO and FPSOHHO. |
| `fitness_calls` | Calls to the common evaluator, including initialization and repeated candidates. Each run has a budget of 6,500. |
| `distinct_schedules` | Number of distinct four-integer schedules queried after bounding and rounding. |
| `best_score` | Lowest normalized objective seen by the common evaluator in that run. |
| `large_forward`, `medium_forward`, `large_reverse`, `medium_reverse` | Four fixed-route counts attached to the reported score. |

Each run uses 30 particles and a nominal horizon of 120 iterations for parameter schedules. Runs stop at the callback budget. Candidates rejected inside an algorithm before reaching the common evaluator consume no calls. Each final incumbent is rescored by the original integer evaluator. The checker compares integer decisions exactly and floating-point values with an absolute tolerance of 0.000001. A difference raises an error naming the affected field or run.

The archived [case record](../results/case.json) contains the CBC objective, the enumerated reference, directional counts, input source hash and every positive minibus allocation. Keys in `minibus_by_od` are one-based origin–destination stop pairs. Rebuild the overview image with `python docs/plot_case.py`.
