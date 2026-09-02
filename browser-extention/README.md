# Browser extension testing

This folder defines the testing scope for the passive browser extension.
Extension source, fixtures, and production unit tests remain in
`../browser_extension/` in the umbrella workspace; they are not copied here.

The cross-system runner invokes the selected extension unit-test command and
records only aggregate status, duration, and an output hash in the canonical
summary:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-code-tests
```

The extension remains passive: it must not classify, block, redirect, close
tabs, or render Pattern Interrupt. Do not publish DOM, URL, history, or raw
browser output.
