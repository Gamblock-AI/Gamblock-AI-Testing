# Model testing

This folder documents the testing-repository boundary for model evaluation.
Model source, datasets, fixtures, and production evaluation tests remain in
`../gamblock-ai-model/` in the umbrella workspace; they are not copied here.

Model replay and the runtime projection are started by the cross-system runner:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-model-replay
```

The resulting summary contains aggregate metrics only. Raw URLs, DOM text,
history, and row identifiers must remain local.
