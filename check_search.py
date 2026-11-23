"""Independent budget-matched diagnostic on the archived 12-stop instance.
Run after verify_case.py. Takes original source directory, case JSON, output CSV.
Counts requests to the common fitness callback, including initializer and duplicate calls.
"""
import sys, math, random, csv, json, os
from contextlib import redirect_stdout
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(sys.argv[1]).resolve()))
import goal as g
from FPSOHHO import FPSOHHO
from HHO import HHO
from MSPSO import MSPSO
record=json.loads(Path(sys.argv[2]).read_text(encoding='utf-8-sig'))
lengths=record['route_length']
c = [[l*(g.D[k]/g.D_norm+g.e_consume[k]*g.c_e/g.E_norm)-g.k_val[k]/g.J_norm for k in (0,1)] for l in lengths]
def score(counts):
    b,m,d,n=counts
    if b+d>50 or m+n>150 or 30*b+8*m<760 or 30*d+8*n<789:
        return 100000.
    return record['minibus_term']+c[0][0]*b+c[0][1]*m+c[1][0]*d+c[1][1]*n
for case in ([0,0,0,0], [24,5,26,2],[13,48,14,50],[10,65,20,30],[25,75,26,75]):
    assert abs(score(case)-g.objective(case))<1e-6
class Budget(BaseException): pass
class Counter:
    def __init__(self):
        self.calls=0; self.best=math.inf; self.counts=None; self.visited=set()
    def __call__(self,x):
        if self.calls==6500: raise Budget()
        self.calls+=1
        # The same projection is applied to trial points accepted by each implementation.
        counts=tuple(min(lim,max(0,round(float(v)))) for v,lim in zip(x,(50,150,50,150)))
        self.visited.add(counts)
        value=score(counts)
        if value<self.best:
            self.best=value;self.counts=counts
        return value
with Path(sys.argv[3]).open('w',newline='',encoding='utf-8') as out, open(os.devnull,'w',encoding='utf-8') as quiet:
    writer=csv.writer(out);writer.writerow(['seed','algorithm','fitness_calls','distinct_schedules','best_score','large_forward','medium_forward','large_reverse','medium_reverse'])
    for seed in range(20):
        for algo in (HHO,MSPSO,FPSOHHO):
            np.random.seed(seed);random.seed(seed);counter=Counter()
            try:
                with redirect_stdout(quiet):
                    solver=algo(counter,dimension=4,lb=np.zeros(4),ub=np.array([50,150,50,150]),pop_size=30,max_iter=120)
                    solver.optimize()
            except Budget:
                pass
            assert counter.calls==6500 and abs(g.objective(counter.counts)-counter.best)<1e-6
            writer.writerow([seed,algo.__name__,counter.calls,len(counter.visited),counter.best,*counter.counts]);out.flush()
