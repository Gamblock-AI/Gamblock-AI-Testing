# Cross-system testing tools

This folder owns checks that combine multiple component repositories. It
contains the evaluation runner, runtime projection, public-evidence validator,
context validator, and their unit tests. The runner writes one canonical
aggregate report into each technology folder.

Run from the testing repository root:

```sh
python3 docs/tools/run_evaluation.py --workspace-root ..
python3 docs/tools/verify_public_evidence.py
./docs/tools/verify-ai-context.sh
python3 -m unittest discover -s docs/tools/tests -p 'test_*.py'
```

The runner writes the single canonical human-readable result to
`<technology>/report.md`; `docs/testing-index.md` only links to those reports.
