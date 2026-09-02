# Model testing

This folder documents the testing-repository boundary for model evaluation.
Model source, datasets, fixtures, and production evaluation tests remain in
`../gamblock-ai-model/` in the umbrella workspace; they are not copied here.

Model replay and the runtime projection are started by the cross-system runner:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-model-replay
```

Add the model repository unit tests to the same receipt when requested:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-model-replay --run-model-tests
```

The replay includes the historical evidence snapshot, runtime projection, and
a separate text-and-registrable-domain-grouped deployment candidate. The resulting
summary contains aggregate metrics, slices, ablations, camouflage robustness,
short-DOM robustness,
threshold sensitivity, calibration, repeated grouped validation,
duplicate/leakage counts, split-manifest integrity, offline speed,
split-audit status, ONNX parity, and
the four visual artifact hashes. The PNGs are generated in the model
repository under `model/evidence/visuals/`. Aggregate JSON evidence is stored under
`model/evidence/aggregate/`. Raw URLs, DOM text, history, row identifiers, predictions,
and temporary candidate artifacts remain local in ignored `model/private/`.

The current progress-evaluation checkpoint is accuracy, precision, recall, and
F1-score >= 90%, with FPR <= 5%. It is a provisional reporting threshold and
does not alter the PKM proposal or promote a candidate model.

Repeated grouped validation evaluates the selected candidate with a fixed
configuration and policy to measure stability. It is not a nested estimate of
generalization after hyperparameter selection.
