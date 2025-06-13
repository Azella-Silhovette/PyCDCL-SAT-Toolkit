import sys
from collections import deque, defaultdict

def parse_dimacs(file_path):
    clauses = []
    vars_count = 0
    seen = set()

    try:
        with open(file_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('c'):
                    continue
                if line.startswith('p'):
                    parts = line.split()
                    if len(parts) >= 4 and parts[1] == 'cnf':
                        vars_count = int(parts[2])
                    continue
                parts = line.split()
                lits = []
                for tok in parts:
                    lit = int(tok)
                    if lit == 0:
                        break
                    v = abs(lit)
                    if v < 1 or (vars_count and v > vars_count):
                        lits = []
                        break
                    lits.append(lit)
                if not lits:
                    if parts and parts[0] == '0':
                        return vars_count, [[]]
                    continue
                key = tuple(sorted(lits))
                if key in seen:
                    continue
                seen.add(key)
                clauses.append(lits)
    except IOError:
        print(f"Error: cannot open {file_path}")
        sys.exit(1)

    return vars_count, clauses

def solve_cdcl(vars_count, clauses):
    assignment = {}
    level = {}
    reason = {}
    trail = []
    decision_level = 0

    activity = {v: 0.0 for v in range(1, vars_count+1)}
    decay_counter = 0

    lit2cls = defaultdict(list)
    for idx, cl in enumerate(clauses):
        for lit in cl:
            lit2cls[lit].append(idx)

    prop_queue = deque()

    def val_of(lit):
        v = abs(lit)
        if v not in assignment:
            return None
        return assignment[v] if lit > 0 else not assignment[v]

    def enqueue(lit, from_clause):
        v = abs(lit)
        val = (lit > 0)
        if v in assignment:
            return assignment[v] == val
        assignment[v] = val
        level[v] = decision_level
        reason[v] = from_clause
        trail.append(v)
        prop_queue.append(lit)
        return True

    def unit_propagate():
        while prop_queue:
            lit = prop_queue.popleft()
            neg = -lit
            for ci in lit2cls[neg]:
                cl = clauses[ci]
                satisfied = False
                unassigned = 0
                last_lit = None
                for l in cl:
                    v = val_of(l)
                    if v is True:
                        satisfied = True
                        break
                    if v is None:
                        unassigned += 1
                        last_lit = l
                if satisfied:
                    continue
                if unassigned == 0:
                    return cl
                if unassigned == 1:
                    if not enqueue(last_lit, cl):
                        return cl
        return None

    def backtrack_to(target):
        nonlocal decision_level
        while trail and level[trail[-1]] > target:
            v = trail.pop()
            del assignment[v]
            del level[v]
            del reason[v]
        decision_level = target

    def conflict_analysis(conflict_clause):
        learned = list(conflict_clause)
        cur_lvl = decision_level

        while True:
            cnt = 0
            last = None
            for l in learned:
                if level.get(abs(l), 0) == cur_lvl:
                    cnt += 1
                    last = l
            if cnt <= 1:
                break
            var = abs(last)
            reason_cl = reason.get(var)
            if not reason_cl:
                break
            new_lear = [l for l in learned if abs(l) != var]
            for l in reason_cl:
                if abs(l) != var and l not in new_lear:
                    new_lear.append(l)
            learned = new_lear

        max_lvl = -1
        asserting = None
        for l in learned:
            lvl = level.get(abs(l), 0)
            if lvl > max_lvl:
                max_lvl = lvl
                asserting = l

        back_lvl = 0
        for l in learned:
            if l == asserting:
                continue
            lvl = level.get(abs(l), 0)
            if lvl > back_lvl:
                back_lvl = lvl

        return learned, asserting, back_lvl

    for cl in clauses:
        if len(cl) == 1:
            enqueue(cl[0], cl)
    confl = unit_propagate()
    if confl:
        return False, {}

    while True:
        if len(assignment) == vars_count:
            return True, assignment

        if confl is None:
            unass = [v for v in range(1, vars_count+1) if v not in assignment]
            var = max(unass, key=lambda v: activity[v])
            decision_level += 1
            lit = var
            if not enqueue(lit, None):
                confl = [-lit]
            else:
                confl = unit_propagate()

        if confl:
            if decision_level == 0:
                return False, {}
            learned, asserting, back_lvl = conflict_analysis(confl)
            if not learned:
                return False, {}
            clauses.append(learned)
            ci = len(clauses) - 1
            for l in learned:
                lit2cls[l].append(ci)
            for l in learned:
                activity[abs(l)] += 1.0
            decay_counter += 1
            if decay_counter >= 50:
                for v in activity:
                    activity[v] *= 0.5
                decay_counter = 0
            backtrack_to(back_lvl)
            enqueue(asserting, learned)
            confl = unit_propagate()

def main():
    if len(sys.argv) != 2:
        print("Usage: python cdcl_solver.py <file.cnf>")
        sys.exit(1)

    cnf = sys.argv[1]
    vars_count, clauses = parse_dimacs(cnf)

    if vars_count == 0:
        if not clauses:
            print("SAT")
        else:
            print("UNSAT")
        return

    sat, model = solve_cdcl(vars_count, clauses)
    if sat:
        print("SAT")
        lits = []
        for v in range(1, vars_count+1):
            val = model.get(v, True)
            lits.append(str(v if val else -v))
        print("v " + " ".join(lits) + " 0")
    else:
        print("UNSAT")

if __name__ == "__main__":
    main()
