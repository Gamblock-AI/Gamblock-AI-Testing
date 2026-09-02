# Golang / backend testing

This folder defines the testing scope for the Go backend. Backend source code,
fixtures, and production unit tests remain in `../gamblock-ai-backend/` in the
umbrella workspace; they are not copied here.

The cross-system runner invokes the selected backend unit-test command and
records only aggregate status, duration, and an output hash in the canonical
summary. Run it from the testing repository root with:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-code-tests
```

No backend URL, account data, secret, or raw test output belongs in public
evidence.
