# Mixed-fleet bus scheduling

Verification code for *Mixed-Fleet Bus Scheduling with Fixed Routes and Flexible Minibuses*.
The case has twelve stops, two fixed-route directions and direct minibus assignments.
The objective combines normalized operating and energy costs with a vehicle-class congestion credit.

## Exact reference with standard Python

    python reference.py

The script enumerates 1,326 pairs of large-bus counts and assigns the least feasible number of medium buses in each direction. It takes the aggregate route demands and the total minibus cost as inputs. The expected normalized score is 6268.946555. One optimal allocation uses 24 large and five medium buses forward, and 26 large and two medium buses in reverse. The direct minibus component is fixed for this case.

## Verify the underlying integer model and rerun the three searches

The drivers below require the authors' separate source modules. Place goal.py, FPSOHHO.py, HHO.py and MSPSO.py in an original/ directory to run this part. The exact reference above runs on its own. The tested environment is Python 3.10.18 on Windows with PuLP's bundled CBC solver.

    python -m pip install -r requirements.txt
    python verify_case.py original > fresh_case.json
    python check_search.py original fresh_case.json fresh_runs.csv

For Windows PowerShell 5.1, write the JSON using the following command.

    python verify_case.py original | Out-File -Encoding utf8 fresh_case.json

The first driver computes the direct allocations from the demand matrix, checks feasibility and resolves the original integer model with the four fixed-route counts released. It prints the numerical reference and the positive minibus allocations as JSON. Run it before the second driver.

The second driver compares archived HHO, MSPSO and FPSOHHO implementations on one demand matrix. It uses seeds 0–19, 30 particles, a nominal 120-iteration schedule and 6,500 calls to the common fitness evaluator per algorithm per seed. Each final incumbent is checked against the original integer evaluator. The output CSV has 60 rows. The mean scores are 8552.5 (HHO), 6352.2 (MSPSO) and 6441.6 (FPSOHHO). Lower values are better.

The ten-run historical statistics in the manuscript used a different protocol. These drivers reproduce the independent twenty-seed comparison.

## License

The MIT License covers the code distributed in this repository. Separately obtained original modules retain their own licensing terms.
