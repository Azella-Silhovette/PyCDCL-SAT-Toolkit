import sys
from collections import defaultdict, deque

def parse_dimacs(filename):
    clauses = []
    num_vars = 0
    with open(filename) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('c'):
                continue
            if line.startswith('p'):
                parts = line.split()
                num_vars = int(parts[2])
                continue
            lits = [int(x) for x in line.split() if int(x) != 0]
            if lits:
                clauses.append(lits)
    return clauses, num_vars

class CDCLSolver:
    def __init__(self, clauses, num_vars):
        self.clauses = [list(c) for c in clauses]
        self.num_vars = num_vars
        self.assign_val = [0]*(num_vars+1)
        self.assign_level = [0]*(num_vars+1)
        self.reason = [None]*(num_vars+1)
        self.level = 0
        self.watch_lit_to_clauses = defaultdict(list)
        self.watchers = {}
        self.assign_stack = []
        self.prop_queue = deque()
        self.var_activity = [0.0]*(num_vars+1)
        self.decay = 0.95
        self.conflict_count = 0
        self.decay_interval = 50
        for i, clause in enumerate(self.clauses):
            if len(clause) >= 2:
                w1, w2 = clause[0], clause[1]
            elif len(clause) == 1:
                w1 = w2 = clause[0]
            else:
                raise ValueError("Empty clause encountered (UNSAT).")
            self.watchers[i] = [w1, w2]
            self.watch_lit_to_clauses[w1].append(i)
            if w2 != w1:
                self.watch_lit_to_clauses[w2].append(i)

    def assign_var(self, lit, level, reason):
        var = abs(lit)
        self.assign_val[var] = 1 if lit > 0 else -1
        self.assign_level[var] = level
        self.reason[var] = reason
        self.assign_stack.append((var, lit, level))
        self.prop_queue.append(lit)

    def propagate(self):
        while self.prop_queue:
            lit = self.prop_queue.popleft()
            target = -lit
            for ci in list(self.watch_lit_to_clauses[target]):
                w1, w2 = self.watchers[ci]
                if w1 == target:
                    other = w2
                    idx_watch = 0
                elif w2 == target:
                    other = w1
                    idx_watch = 1
                else:
                    continue
                var_o = abs(other)
                val_o = self.assign_val[var_o]
                if val_o != 0 and ((other > 0 and val_o == 1) or (other < 0 and val_o == -1)):
                    continue
                found_new = False
                for lit2 in self.clauses[ci]:
                    if lit2 == w1 or lit2 == w2:
                        continue
                    var2 = abs(lit2)
                    val2 = self.assign_val[var2]
                    if val2 == 0 or (lit2 > 0 and val2 == 1) or (lit2 < 0 and val2 == -1):
                        self.watchers[ci][idx_watch] = lit2
                        self.watch_lit_to_clauses[lit2].append(ci)
                        self.watch_lit_to_clauses[target].remove(ci)
                        found_new = True
                        break
                if not found_new:
                    if self.assign_val[abs(other)] != 0:
                        return ci
                    self.assign_var(other, self.level, ci)
        return None

    def branch_var(self):
        best_var = None
        best_act = -1.0
        for v in range(1, self.num_vars+1):
            if self.assign_val[v] == 0:
                act = self.var_activity[v]
                if act > best_act:
                    best_act = act
                    best_var = v
        if best_var is None:
            return None
        return best_var

    def backtrack(self, backtrack_level):
        while self.assign_stack and self.assign_stack[-1][2] > backtrack_level:
            var, lit, lvl = self.assign_stack.pop()
            self.assign_val[var] = 0
            self.assign_level[var] = 0
            self.reason[var] = None

    def solve(self):
        for i, clause in enumerate(self.clauses):
            if len(clause) == 1:
                lit = clause[0]
                var = abs(lit)
                val = 1 if lit > 0 else -1
                if self.assign_val[var] != 0:
                    if self.assign_val[var] != val:
                        return False
                    continue
                self.assign_var(lit, 0, None)
        conflict = self.propagate()
        if conflict is not None:
            return False
        while True:
            if all(self.assign_val[i] != 0 for i in range(1, self.num_vars+1)):
                return True
            var = self.pick_branch_var()
            if var is None:
                return True
            self.level += 1
            self.assign_var(var, self.level, None)
            while True:
                conflict = self.propagate()
                if conflict is None:
                    break
                if not self.resolve_conflict(conflict):
                    return False

    def resolve_conflict(self, clause_idx):
        if self.level == 0:
            return False
        self.conflict_count += 1
        learned = list(self.clauses[clause_idx])
        while True:
            curr_level_lits = [lit for lit in learned if self.assign_level[abs(lit)] == self.level]
            if len(curr_level_lits) <= 1:
                break
            last_assigned = None
            for (var, lit, lvl) in reversed(self.assign_stack):
                if lvl != self.level:
                    continue
                if lit in learned:
                    last_assigned = lit
                    break
            if last_assigned is None:
                break
            var_last = abs(last_assigned)
            reason_idx = self.reason[var_last]
            if reason_idx is None:
                break
            reason_clause = self.clauses[reason_idx]
            pos, neg = last_assigned, -last_assigned
            new_clause = [lit for lit in learned if lit != pos and lit != neg]
            for lit in reason_clause:
                if lit != pos and lit != neg and lit not in new_clause:
                    new_clause.append(lit)
            learned = new_clause
        for lit in learned:
            v = abs(lit)
            self.var_activity[v] += 1.0
        if self.conflict_count % self.decay_interval == 0:
            for i in range(1, self.num_vars+1):
                self.var_activity[i] *= self.decay
        backtrack_level = 0
        for lit in learned:
            lvl = self.assign_level[abs(lit)]
            if lvl != self.level and lvl > backtrack_level:
                backtrack_level = lvl
        self.backtrack(backtrack_level)
        self.level = backtrack_level
        self.clauses.append(learned)
        ci = len(self.clauses) - 1
        if len(learned) >= 2:
            w1, w2 = learned[0], learned[1]
        elif len(learned) == 1:
            w1 = w2 = learned[0]
        else:
            return False
        self.watchers[ci] = [w1, w2]
        self.watch_lit_to_clauses[w1].append(ci)
        if w2 != w1:
            self.watch_lit_to_clauses[w2].append(ci)
        if len(learned) == 1:
            lit0 = learned[0]
            var0 = abs(lit0)
            if self.assign_val[var0] == 0:
                self.assign_var(lit0, self.level, ci)
        return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cdcl_solver.py <input.cnf>", file=sys.stderr)
        sys.exit(1)
    clauses, num_vars = parse_dimacs(sys.argv[1])
    solver = CDCLSolver(clauses, num_vars)
    sat = solver.solve()
    if sat:
        res = []
        for i in range(1, num_vars+1):
            val = solver.assign_val[i]
            if val == 1:
                res.append(str(i))
            elif val == -1:
                res.append(str(-i))
            else:
                res.append(str(i))
        print("SAT")
        print("v " + " ".join(res) + " 0")
    else:
        print("UNSAT")
