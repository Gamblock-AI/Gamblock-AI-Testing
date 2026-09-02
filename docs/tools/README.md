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

Running the tool is part of the mandatory test handoff, but it does not commit
or push changes. After it finishes, inspect `git status`/`git diff`, run the
validators, and provide the test receipt specified in
[`../ai/testing-run-receipt.md`](../ai/testing-run-receipt.md). If a component
test was run without this synchronization, report it as an incomplete or
blocked evidence handoff rather than implying that the testing repository was
updated.
