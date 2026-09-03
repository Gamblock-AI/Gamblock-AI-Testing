# Golang / backend testing

This folder defines the testing scope for the Go backend. Backend source code,
fixtures, and production unit tests remain in `../gamblock-ai-backend/` in the
umbrella workspace; they are not copied here.

The cross-system runner invokes the selected backend unit-test command and,
when an isolated PostgreSQL `DATABASE_URL` is configured, the tagged
integration command. It records only aggregate status, duration, and output
hashes in the canonical summary. Run it from the testing repository root with:

```sh
python3 docs/tools/run_evaluation.py \
  --workspace-root .. --run-code-tests --component backend
```

No backend URL, account data, secret, or raw test output belongs in public
evidence.

`backend_unit` covers the normal Go suite. `backend_integration` covers
PostgreSQL migration, transaction, encryption, and concurrent aggregate
idempotency checks through `make test-integration`; without an isolated
database it remains `pending`. CI enables this check with the backend
repository variable `ENABLE_CI_TESTS=true` and a disposable PostgreSQL service.
