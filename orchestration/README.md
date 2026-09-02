# Cross-system orchestration

This folder is the only owner of checks that combine multiple component
repositories. It contains the evaluation runner, runtime projection, public
evidence validator, and their unit tests.

Run from the testing repository root:

```sh
python3 orchestration/scripts/run_evaluation.py --workspace-root ..
python3 orchestration/scripts/verify_public_evidence.py
python3 -m unittest discover -s orchestration/tests -p 'test_*.py'
```

The runner writes the single canonical human-readable result to
`reports/testing-summary.md`; component folders do not maintain a second
summary.
