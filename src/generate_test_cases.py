import random

def write_cnf(filename, clauses, num_vars):
    with open(filename, 'w') as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(str(l) for l in cl) + " 0\n")

def generate_sat_formula(num_vars, num_clauses):
    assignment = {i: random.choice([True, False]) for i in range(1, num_vars+1)}
    clauses = []
    for _ in range(num_clauses):
        vs = random.sample(range(1, num_vars+1), 3)
        lits = []
        satisfied = False
        for v in vs:
            sign = random.choice([True, False])
            if (assignment[v] and sign) or (not assignment[v] and not sign):
                satisfied = True
            lit = v if sign else -v
            lits.append(lit)
        if not satisfied:
            idx = random.randrange(3)
            v = vs[idx]
            sign = assignment[v]
            lits[idx] = v if sign else -v
        clauses.append(lits)
    used = {abs(l) for cl in clauses for l in cl}
    for v in range(1, num_vars+1):
        if v not in used:
            others = random.sample([x for x in range(1, num_vars+1) if x != v], 2)
            lits = []
            for w in [v] + others:
                sign = random.choice([True, False])
                lit = w if sign else -w
                lits.append(lit)
            clauses.append(lits)
    return clauses

def generate_unsat_formula(num_vars, num_clauses):
    clauses = []
    clauses.append([1])
    clauses.append([-1])
    for _ in range(num_clauses - 2):
        vs = random.sample(range(1, num_vars+1), 3)
        lits = []
        for v in vs:
            sign = random.choice([True, False])
            lits.append(v if sign else -v)
        clauses.append(lits)
    used = {abs(l) for cl in clauses for l in cl}
    for v in range(1, num_vars+1):
        if v not in used:
            vs = [v] + random.sample([x for x in range(1, num_vars+1) if x != v], 2)
            lits = []
            for w in vs:
                sign = random.choice([True, False])
                lits.append(w if sign else -w)
            clauses.append(lits)
    return clauses

if __name__ == "__main__":
    random.seed(45)
    num_vars = 100
    for size in [300, 400, 600]:
        clauses = generate_sat_formula(num_vars, size)
        write_cnf(f"sat_case_{size}.cnf", clauses, num_vars)
    unsat_clauses = generate_unsat_formula(num_vars, 300)
    write_cnf("unsat_case.cnf", unsat_clauses, num_vars)
