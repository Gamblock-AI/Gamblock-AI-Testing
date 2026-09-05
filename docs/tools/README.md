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
To run and synchronize one component without rewriting other reports, pass its
component name, for example:

```sh
python3 docs/tools/run_evaluation.py \
  --workspace-root .. --run-code-tests --component browser_extension
```

The Flutter report tracks the cross-platform browser-support runtime contract.
Android is required and Windows is optional/non-gating. It requires one Android
device, four Android browsers, and optionally five Windows browsers;
the existing Chrome-only Windows helper is not sufficient evidence. The runner
does not simulate either runtime.

For model evaluation, it also writes the permanent aggregate JSON evidence to
`model/evidence/aggregate/` and the allowlisted aggregate-generated charts to
`model/evidence/visuals/`. Sensitive model inputs remain in ignored
`model/private/` and are never copied into public evidence.

The runner uses the single active `docs/config/targets.json` configuration.
There is no report selector or parallel target configuration. The
current report and target contract are reviewed together before evidence is
published.

Running the tool is part of the mandatory test handoff, but it does not commit
or push changes. After it finishes, inspect `git status`/`git diff`, run the
validators, and provide the test receipt specified in
[`../ai/testing-run-receipt.md`](../ai/testing-run-receipt.md). If a component
test was run without this synchronization, report it as an incomplete or
blocked evidence handoff rather than implying that the testing repository was
updated.
