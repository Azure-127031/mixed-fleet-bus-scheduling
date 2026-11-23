"""Check the twelve-stop instance in the author's goal.py. Run with its folder as argument."""
import json, sys, math, hashlib
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[1]).resolve()))
import goal as g
import pulp

def evaluate(x):
    model, flow, *_ = g.solve_scheduling(x)
    assert pulp.LpStatus[model.status] == 'Optimal'
    return pulp.value(model.objective), {f'{i+1}-{j+1}': v for (i,j,k),v in flow.items() if k == 2}

routes = (g.fixed_route1, g.fixed_route2)
demands = (g.route1_total_demand, g.route2_total_demand)
peaks = tuple(max(x.values()) for x in (g.route1_segment_passengers, g.route2_segment_passengers))
distances = [g.calc_route_distance(r) for r in routes]
def unit(k, length):
    return length*(g.D[k]/g.D_norm + g.c_e*g.e_consume[k]/g.E_norm)-g.k_val[k]/g.J_norm
mini = {(i,j): math.ceil(g.demand_matrix[i][j]/g.R[2]) for i in g.all_stations for j in g.all_stations if i!=j and (i,j) not in g.fixed_legs and g.demand_matrix[i][j]}
assert all(unit(2,g.dist_matrix[i][j])>0 for i in g.all_stations for j in g.all_stations if i!=j)
minicost = sum(n*unit(2,g.dist_matrix[i][j]) for (i,j),n in mini.items())
assert sum(mini.values()) <= g.avail_vehicles[2]
best = math.inf
for b1 in range(g.avail_vehicles[0]+1):
    for b2 in range(g.avail_vehicles[0]-b1+1):
        counts = []
        cost = minicost
        for b,d,peak,length in zip((b1,b2),demands,peaks,distances):
            med = max(0,math.ceil((max(d,peak)-g.R[0]*0.6*b)/(g.R[1]*0.4)))
            counts.extend([b,med])
            cost += b*unit(0,length)+med*unit(1,length)
        if counts[1]+counts[3] <= g.avail_vehicles[1] and cost < best:
            best, optimum = cost, counts
cbc_best, dispatch = evaluate(optimum)
assert abs(cbc_best-best)<1e-6 and dispatch=={f'{i+1}-{j+1}':n for (i,j),n in mini.items()}
initial=[]
for i,d in enumerate(demands):
    initial.extend([max(5+i, math.ceil(d*.5/(g.R[0]*.6))),max(3+i, math.ceil(d*.5/(g.R[1]*.4)))])
initial_value,initial_dispatch = evaluate(initial+[1]*36)
tail_value,tail_dispatch = evaluate(initial+[77]*144)
assert abs(initial_value-tail_value)<1e-6 and initial_dispatch==tail_dispatch
# Also solve the supplied model with the four pinned route counts released.
model, *_ = g.solve_scheduling(initial)
for v in model.variables():
    if v.name in {'bus_count_route1','bus_count_route2','midbus_count_route1','midbus_count_route2'}:
        v.bounds(0,None)
status=model.solve(pulp.PULP_CBC_CMD(msg=False,gapRel=0))
assert pulp.LpStatus[status]=='Optimal' and abs(pulp.value(model.objective)-best)<1e-6
exceed=[(i,j) for i,j in mini if g.dist_matrix[i][j]*60/g.v[2]>g.MAX_WAIT_TIME]
result=dict(model_sha256=hashlib.sha256(Path(g.__file__).read_bytes()).hexdigest(), passengers=sum(map(sum,g.demand_matrix)), routes_demand=demands,peak_loads=peaks,route_length=distances, route_legs=len(g.fixed_legs), od_positive=sum(x>0 for row in g.demand_matrix for x in row), mini_links=len(mini), minibuses=sum(mini.values()), minibus_term=minicost, exact_counts=optimum, exact_score=best,cbc_score=pulp.value(model.objective), original_initial_counts=initial,original_initial_score=initial_value,identical_score_with_changed_tail=tail_value,over_five_minute_served_links=len(exceed), over_five_fixed_links=sum(t[0] for t in g.fixed_legs_time_status.values()), minibus_by_od=dispatch)
print(json.dumps(result,indent=2))
