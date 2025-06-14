# fix: Adding path for "src" module
import sys
import os
import random
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.generate_test_cases import generate_sat_formula, generate_unsat_formula


def test_generate_sat_formula_structure():
    num_vars = random.randint(1000, 5000)
    num_clauses = random.randint(1000, 5000)
    clauses = generate_sat_formula(num_vars, num_clauses)
    assert len(clauses) >= num_clauses

    for cl in clauses[:num_clauses]:
        assert len(cl) == 3
        for lit in cl:
            assert 1 <= abs(lit) <= num_vars


def test_generate_unsat_formula_structure():
    num_vars = random.randint(1000, 5000)
    num_clauses = random.randint(1000, 5000)
    clauses = generate_unsat_formula(num_vars, num_clauses)
    assert len(clauses) >= num_clauses
    assert [1] in clauses
    assert [-1] in clauses
    for cl in clauses:
        for lit in cl:
            assert 1 <= abs(lit) <= num_vars


def test_generate_unsat_formula_unsat():
    clauses = generate_unsat_formula(random.randint(1000, 5000), random.randint(1000, 5000))
    assert [1] in clauses
    assert [-1] in clauses
