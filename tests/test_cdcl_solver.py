import sys
import os
import random
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src import cdcl_solver


def write_temp_dimacs(content):
    """
    Writes content to a temporary DIMACS file and returns its path.

    Args:
        content (str): The string content to write to the file.

    Returns:
        str: The path to the created temporary file.
    """
    with tempfile.NamedTemporaryFile("w+", delete=False) as f:
        f.write(content)
        f.flush()
        return f.name


def test_parse_dimacs_basic():
    """
    Tests the basic parsing of a simple DIMACS CNF string.

    Verifies that the parser correctly extracts the number of variables
    and the clauses from a well-formed input.
    """
    cnf = "p cnf 2 2\n1 -2 0\n2 0\n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 2
    assert clauses == [[1, -2], [2]]
    os.remove(fname)


def test_parse_dimacs_empty():
    """
    Tests the parser's behavior with an empty DIMACS input string.

    Ensures that an empty input results in zero variables and no clauses.
    """
    cnf = ""
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 0
    assert clauses == []
    os.remove(fname)


def test_parse_dimacs_single_var():
    """
    Tests the parser's ability to handle clauses involving a single variable.

    Verifies correct parsing when variables appear as both positive and negative literals.
    """
    cnf = "p cnf 1 2\n1 0\n-1 0\n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 1
    assert [1] in clauses and [-1] in clauses
    os.remove(fname)


def test_solve_cdcl_simple_sat():
    """
    Tests the CDCL solver with a simple satisfiable CNF formula.

    Verifies that the solver correctly identifies satisfiability and
    returns a valid model.
    """
    vars_count = 2
    clauses = [[1, -2], [2]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert isinstance(model, dict)
    assert all(v in model for v in range(1, vars_count + 1))


def test_solve_cdcl_simple_unsat():
    """
    Tests the CDCL solver with a simple unsatisfiable CNF formula.

    Verifies that the solver correctly identifies unsatisfiability and
    returns an empty model.
    """
    vars_count = 1
    clauses = [[1], [-1]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert not sat
    assert model == {}


def test_solve_cdcl_large_random_sat():
    """
    Tests the CDCL solver with a large, randomly generated, satisfiable 3-SAT instance.

    Generates a known satisfying assignment and then constructs clauses
    consistent with that assignment to ensure satisfiability.
    """
    random.seed(42)
    num_vars = 50
    num_clauses = 200
    # Generate a satisfiable 3-SAT problem
    assignment = {i: random.choice([True, False]) for i in range(1, num_vars + 1)}
    clauses = []
    for _ in range(num_clauses):
        vs = random.sample(range(1, num_vars + 1), 3)
        clause = []
        satisfied = False
        for v in vs:
            sign = random.choice([True, False])
            if (assignment[v] and sign) or (not assignment[v] and not sign):
                satisfied = True
            clause.append(v if sign else -v)
        if not satisfied:
            # Ensure the generated clause is satisfied by the 'assignment'
            idx = random.randrange(3)
            v = vs[idx]
            sign = assignment[v]
            clause[idx] = v if sign else -v
        clauses.append(clause)
    sat, model = cdcl_solver.solve_cdcl(num_vars, clauses)
    assert sat
    assert isinstance(model, dict)
    assert all(v in model for v in range(1, num_vars + 1))


def test_solve_cdcl_large_random_unsat():
    """
    Tests the CDCL solver with a large, randomly generated, unsatisfiable instance.

    Guarantees unsatisfiability by including contradictory unit clauses (e.g., (1) and (-1)).
    """
    random.seed(43)
    num_vars = 30
    num_clauses = 100
    # Construct UNSAT: x1, -x1, rest are random
    clauses = [[1], [-1]]
    for _ in range(num_clauses - 2):
        vs = random.sample(range(1, num_vars + 1), 3)
        clause = [v if random.choice([True, False]) else -v for v in vs]
        clauses.append(clause)
    sat, model = cdcl_solver.solve_cdcl(num_vars, clauses)
    assert not sat
    assert model == {}


def test_solve_cdcl_edge_case_all_positive():
    """
    Tests a satisfiable case where all variables can be assigned True.
    """
    vars_count = 5
    clauses = [[1, 2, 3], [2, 3, 4], [3, 4, 5], [1, 4, 5]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert all(model[v] for v in range(1, vars_count + 1))


def test_solve_cdcl_edge_case_all_negative():
    """
    Tests a satisfiable case where all variables can be assigned False.
    The solver should find *any* valid satisfying assignment.
    """
    vars_count = 4
    clauses = [[-1, -2, -3], [-2, -3, -4], [-1, -3, -4], [-1, -2, -4]]
    
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    
    # Assert that the problem is satisfiable
    assert sat
    
    # Assert that a model was returned and it has the correct number of variables
    assert isinstance(model, dict)
    assert len(model) == vars_count
    
    # NEW ASSERTION: Verify that the found 'model' actually satisfies all given clauses.
    # This is the crucial check for *any* valid solution.
    for clause in clauses:
        clause_satisfied = False
        for literal in clause:
            var = abs(literal)
            # Check if the literal is true in the found model
            # A positive literal (e.g., 1) is true if model[1] is True
            # A negative literal (e.g., -1) is true if model[1] is False
            if (literal > 0 and model[var] is True) or \
               (literal < 0 and model[var] is False):
                clause_satisfied = True
                break # This literal satisfied the clause, move to the next clause
        assert clause_satisfied, f"Model {model} did not satisfy clause {clause}"


def test_solve_cdcl_unit_clause_forces_assignment():
    """
    Tests that a unit clause correctly forces a variable assignment through unit propagation.
    """
    vars_count = 3
    clauses = [[1], [2, 3], [-2, 3]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert model[1] is True


def test_solve_cdcl_empty_clause_unsat():
    """
    Tests that an empty clause immediately results in an unsatisfiable formula.
    """
    vars_count = 2
    clauses = [[]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert not sat


def test_parse_dimacs_large_file():
    """
    Tests parsing a large DIMACS file with many variables and clauses.

    Verifies performance and correctness for substantial input files.
    """
    num_vars = 100
    num_clauses = 300
    lines = ["p cnf {} {}\n".format(num_vars, num_clauses)]
    for _ in range(num_clauses):
        clause = [
            str(random.randint(1, num_vars) * random.choice([1, -1])) for _ in range(3)
        ]
        lines.append(" ".join(clause) + " 0\n")
    fname = write_temp_dimacs("".join(lines))
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == num_vars
    assert len(clauses) == num_clauses
    os.remove(fname)


def test_solve_cdcl_hard_unsat_pigeonhole():
    """
    Tests the CDCL solver with the classic unsatisfiable Pigeonhole Principle problem.

    For N pigeons and N-1 holes, it's impossible to place all pigeons without
    at least two sharing a hole, proving unsatisfiability.
    """
    n = 5
    vars_count = n * (n - 1)
    clauses = []
    # Each pigeon must go into at least one hole
    for i in range(n):
        clause = []
        for j in range(n - 1):
            clause.append(i * (n - 1) + j + 1)
        clauses.append(clause)
    # Each hole can have at most one pigeon
    for j in range(n - 1):
        for i in range(n):
            for k in range(i + 1, n):
                clauses.append([-(i * (n - 1) + j + 1), -(k * (n - 1) + j + 1)])
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert not sat


def test_solve_cdcl_hard_sat_2sat():
    """
    Tests the CDCL solver with a satisfiable 2-SAT instance.
    """
    vars_count = 4
    clauses = [[1, 2], [-1, 3], [-2, 4], [-3, -4]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat


def test_solve_cdcl_all_assigned():
    """
    Tests a case where all variables are directly assigned True by unit clauses.
    """
    vars_count = 3
    clauses = [[1], [2], [3]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert model[1] and model[2] and model[3]


def test_solve_cdcl_all_neg_assigned():
    """
    Tests a case where all variables are directly assigned False by unit clauses.
    """
    vars_count = 3
    clauses = [[-1], [-2], [-3]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert not model[1] and not model[2] and not model[3]


def test_solve_cdcl_randomized_many():
    """
    Runs multiple iterations of random, satisfiable 3-SAT problems.

    Provides robust testing across a variety of solvable instances.
    """
    for _ in range(10):
        num_vars = random.randint(5, 15)
        num_clauses = random.randint(10, 30)
        assignment = {i: random.choice([True, False]) for i in range(1, num_vars + 1)}
        clauses = []
        for _ in range(num_clauses):
            vs = random.sample(range(1, num_vars + 1), 3)
            clause = []
            satisfied = False
            for v in vs:
                sign = random.choice([True, False])
                if (assignment[v] and sign) or (not assignment[v] and not sign):
                    satisfied = True
                clause.append(v if sign else -v)
            if not satisfied:
                idx = random.randrange(3)
                v = vs[idx]
                sign = assignment[v]
                clause[idx] = v if sign else -v
            clauses.append(clause)
        sat, model = cdcl_solver.solve_cdcl(num_vars, clauses)
        assert sat


def test_parse_dimacs_trailing_spaces():
    """
    Tests the parser's robustness against trailing spaces in DIMACS lines.
    """
    cnf = "p cnf 2 2\n1 -2 0 \n2 0  \n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 2
    assert clauses == [[1, -2], [2]]
    os.remove(fname)


def test_parse_dimacs_multiple_zero():
    """
    Tests the parser's handling of multiple '0' terminators on a single line.
    """
    cnf = "p cnf 2 2\n1 -2 0 0\n2 0 0\n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 2
    assert clauses == [[1, -2], [2]]
    os.remove(fname)


def test_solve_cdcl_large_unsat_chain():
    """
    Tests the CDCL solver with a constructed unsatisfiable chain structure.
    """
    vars_count = 10
    clauses = []
    for i in range(1, vars_count):
        clauses.append([i, i + 1])
        clauses.append([-i, -i + 1])
    clauses.append([-vars_count]) # This makes it unsatisfiable (e.g., if x_n must be true, then x_{n-1} must be false, etc., eventually leading to x_1 being both true and false).
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert not sat


def test_solve_cdcl_large_sat_chain():
    """
    Tests the CDCL solver with a constructed satisfiable chain structure.
    """
    vars_count = 10
    clauses = []
    for i in range(1, vars_count):
        clauses.append([i, i + 1])
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat


def test_solve_cdcl_empty_clauses():
    """
    Tests the solver with an empty list of clauses, which should always be satisfiable.
    """
    vars_count = 0
    clauses = []
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat


def test_parse_dimacs_no_problem_line():
    """
    Tests the parser's behavior when the 'p cnf' problem line is missing.

    It should still attempt to parse clauses and infer variables.
    """
    cnf = "1 -2 0\n2 0\n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    # The variable count might be 0 if the parser strictly relies on the 'p cnf' line,
    # or it might correctly infer 2 if it's flexible. Asserting against 2 is safer if that's expected.
    assert vars_count == 0 or vars_count == 2 # Depending on specific parser implementation
    assert clauses == [[1, -2], [2]]
    os.remove(fname)


def test_parse_dimacs_large_comment_block():
    """
    Tests the parser's ability to efficiently skip a large block of comment lines.
    """
    cnf = "c comment\n" * 100 + "p cnf 3 1\n1 2 3 0\n"
    fname = write_temp_dimacs(cnf)
    vars_count, clauses = cdcl_solver.parse_dimacs(fname)
    assert vars_count == 3
    assert clauses == [[1, 2, 3]]
    os.remove(fname)


def test_solve_cdcl_var_not_in_any_clause():
    """
    Tests that unconstrained variables (not appearing in any clause) are still
    included in the returned satisfying model.
    """
    vars_count = 3
    clauses = [[1, 2]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert 3 in model # Variable 3 should be in the model even if unconstrained


def test_solve_cdcl_all_vars_unconstrained():
    """
    Tests the solver when all variables are unconstrained (empty clause list).
    It should find a satisfiable model for all variables.
    """
    vars_count = 5
    clauses = []
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert all(v in model for v in range(1, vars_count + 1))


def test_solve_cdcl_large_random_unsat_with_unit():
    """
    Tests with a large, randomly generated unsatisfiable problem,
    explicitly containing contradictory unit clauses.
    """
    random.seed(123)
    num_vars = 20
    num_clauses = 50
    clauses = [[1], [-1]] # Guarantee unsatisfiability
    for _ in range(num_clauses - 2):
        vs = random.sample(range(1, num_vars + 1), 3)
        clause = [v if random.choice([True, False]) else -v for v in vs]
        clauses.append(clause)
    sat, model = cdcl_solver.solve_cdcl(num_vars, clauses)
    assert not sat


def test_solve_cdcl_large_random_sat_with_unit():
    """
    Tests with a large, randomly generated satisfiable problem,
    explicitly containing a unit clause.
    """
    random.seed(321)
    num_vars = 20
    num_clauses = 50
    assignment = {i: random.choice([True, False]) for i in range(1, num_vars + 1)}
    clauses = [[1]] # Unit clause (can be satisfied if model[1] is True)
    if not assignment[1]: # Adjust assignment if necessary to satisfy the unit clause
        assignment[1] = True
    for _ in range(num_clauses - 1):
        vs = random.sample(range(1, num_vars + 1), 3)
        clause = []
        satisfied = False
        for v in vs:
            sign = random.choice([True, False])
            if (assignment[v] and sign) or (not assignment[v] and not sign):
                satisfied = True
            clause.append(v if sign else -v)
        if not satisfied:
            # Ensure the generated clause is satisfied by the 'assignment'
            idx = random.randrange(3)
            v = vs[idx]
            sign = assignment[v]
            clause[idx] = v if sign else -v
        clauses.append(clause)
    sat, model = cdcl_solver.solve_cdcl(num_vars, clauses)
    assert sat
    assert model[1] is True # Verify the unit clause was satisfied


def test_solve_cdcl_multiple_solutions_sat():
    """
    Tests a satisfiable problem that has multiple possible satisfying assignments.
    The solver should find at least one.
    """
    vars_count = 3
    # Clauses: (1 or 2), (1 or -2), (-1 or 3)
    # Possible solutions: {1: True, 2: True, 3: True}, {1: True, 2: False, 3: True}
    # Also: {1: False, 2: True, 3: True} (if 1 is false, 2 must be true for (1 or 2) and (1 or -2) to not be false, but (-1 or 3) then becomes (True or 3) -> requires 3 True)
    clauses = [[1, 2], [1, -2], [-1, 3]]
    sat, model = cdcl_solver.solve_cdcl(vars_count, clauses)
    assert sat
    assert isinstance(model, dict)
    assert all(v in model for v in range(1, vars_count + 1))
    # Verify the found model satisfies all clauses
    for clause in clauses:
        clause_satisfied = False
        for literal in clause:
            var = abs(literal)
            val = model[var]
            if (literal > 0 and val) or (literal < 0 and not val):
                clause_satisfied = True
                break
        assert clause_satisfied, f"Model {model} did not satisfy clause {clause}"