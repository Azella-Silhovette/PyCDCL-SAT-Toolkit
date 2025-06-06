# PyCDCL-SAT-Toolkit

PyCDCL-SAT-Toolkit is a lightweight Python-based toolkit for experimenting with Conflict-Driven Clause Learning (CDCL) SAT solving and automated test-case generation. It consists of two main scripts:

1. **`cdcl_solver.py`**  
   - Implements a standard CDCL algorithm to solve Boolean formulas in DIMACS CNF format.  
   - Uses watched‐literal data structures for efficient unit propagation.  
   - Learns new clauses upon conflicts and backtracks appropriately.  
   - Parses any valid CNF file, handles unit clauses at decision level 0, and outputs “SAT” (with a satisfying assignment) or “UNSAT”.

2. **`generate_test_cases.py`**  
   - Randomly constructs “guaranteed-SAT” 3-CNF formulas by first selecting a hidden assignment, then generating each clause so that it cannot falsify that assignment.  
   - Builds “guaranteed-UNSAT” formulas by inserting a contradictory unit pair (e.g. `[1]` and `[-1]`) and padding with random 3-literal clauses.  
   - Ensures every variable appears at least once in the final clause list.  
   - Produces CNF files of configurable size (default: 100 variables, 300/400/600 clauses) for solver benchmarking.

## Repository Structure

PyCDCL-SAT-Toolkit/
 ├── README.md
 ├── LICENSE
 ├── .gitignore
 ├── requirements.txt
 ├── src/
 │   ├── cdcl_solver.py
 │   └── generate_test_cases.py
 ├── examples/
 │   ├── sat_case_300.cnf
 │   ├── sat_case_400.cnf
 │   ├── sat_case_600.cnf
 │   └── unsat_case.cnf
 └── tests/
 ├── test_solver.py
 └── test_case_generation.py

- **`src/`**  
  Contains the two Python scripts:  
  - `cdcl_solver.py`: a standalone CDCL SAT solver.  
  - `generate_test_cases.py`: a script to generate random SAT/UNSAT CNF test files.

- **`examples/`**  
  Pre-generated CNF files for quick testing:  
  - `sat_case_300.cnf`, `sat_case_400.cnf`, `sat_case_600.cnf` (SAT instances).  
  - `unsat_case.cnf` (UNSAT instance).

- **`tests/`**  
  Unit tests (using `pytest`) to verify basic solver correctness and test-case generation.

## Usage

1. Generating Test Cases:

   ```bash
   python src/generate_test_cases.py
   ```

- By default, this script uses:
  - `num_vars = 100`
  - Clause sizes: 300, 400, 600 for SAT cases
  - 300 clauses (with a contradictory unit pair) for the UNSAT case
- Output files will be created in the current working directory:
  - `sat_case_300.cnf`
  - `sat_case_400.cnf`
  - `sat_case_600.cnf`
  - `unsat_case.cnf`

You can modify the script directly or enhance it to accept command-line arguments for custom `num_vars` and `num_clauses`.

### 2. Solving a DIMACS CNF File

```
python src/cdcl_solver.py examples/sat_case_300.cnf
```

- **SAT**
  If the formula is satisfiable, the script will print:

  ```
  v <lit1> <lit2> … <litN> 0
  ```

  where each `<lit>` is a nonzero integer (positive for true, negative for false).

- **UNSAT**
  If the formula is unsatisfiable, the script will print:

  ```
  UNSAT
  ```

## Contribution

Contributions are welcome! If you’d like to add new features, improve performance, or fix bugs, please:

1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes (`git commit -m "Add <feature/bugfix>"`).
4. Push to your fork and submit a Pull Request.
