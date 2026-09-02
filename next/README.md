# Next.js / website testing

This folder defines the testing scope for the Next.js website. Website source,
fixtures, and production unit tests remain in `../gamblock-ai-website/` in the
umbrella workspace; they are not copied here.

The cross-system runner invokes the selected website unit-test command and
records only aggregate status, duration, and an output hash in the canonical
summary:

```sh
python3 orchestration/scripts/run_evaluation.py --workspace-root .. --run-code-tests
```

Do not publish URLs, account data, credentials, or raw browser output.
