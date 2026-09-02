# Gamblock-AI Model Report

This is the canonical aggregate report for this technology. It is
generated from validated public evidence and aggregate command results.
Raw URL, domain, DOM, browsing history, screenshot, serial, credential,
participant, and raw log data are never included.

This report covers offline model replay, runtime projection, and text-and-domain grouped candidate evaluation only.

## Model replay

| Status | Evidence maturity | Test rows | Numeric gate | Audit |
|---|---|---:|---|---|
| passed | provisional | 2592 | True | False |

## Runtime projection

| Status | Accuracy | Precision | Recall | F1 | False-positive rate |
|---|---:|---:|---:|---:|---:|
| passed | 0.9881093935790726 | 0.9856584093872229 | 0.9754838709677419 | 0.9805447470817121 | 0.006292906178489702 |

## Text-and-domain grouped candidate

| Status | Evidence maturity | Test rows | Accuracy | Precision | Recall | F1 | FPR | Numeric gate | Split audit | ONNX parity |
|---|---|---:|---:|---:|---:|---:|---:|---|---|---|
| passed | verified | 2523 | 0.9659135949266746 | 0.9422336328626444 | 0.9470967741935484 | 0.9446589446589446 | 0.02574370709382151 | True | True | passed |

The text-and-domain grouped candidate is a separate research artifact. It does
not replace the active client model automatically.

## Text-and-domain grouped ablations

| Variant | Samples | Accuracy | Precision | Recall | F1 | FPR | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| deployed_hybrid | 2523 | 0.9659135949266746 | 0.9422336328626444 | 0.9470967741935484 | 0.9446589446589446 | 0.02574370709382151 | True |
| dom_only | 2523 | 0.9647245342845818 | 0.9309045226130653 | 0.9561290322580646 | 0.9433481858688734 | 0.031464530892448515 | True |
| model_only | 2523 | 0.9603646452635751 | 0.9234629861982434 | 0.9496774193548387 | 0.9363867684478372 | 0.03489702517162471 | True |
| rule_only | 2523 | 0.9068569163694015 | 0.9054054054054054 | 0.7780645161290323 | 0.8369188063844553 | 0.036041189931350116 | False |
| url_only | 2523 | 0.5790725326991677 | 0.4149377593360996 | 0.9032258064516129 | 0.5686433793663689 | 0.5646453089244852 | False |

## Camouflage robustness

Variants are generated in memory from the frozen grouped final-test rows;
positive-class variants also support train-only augmentation, and no
camouflage dataset is persisted.

| Variant | Samples | Accuracy | Precision | Recall | F1 | FPR | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| case_variation | 2523 | 0.9667063020214031 | 0.942381562099872 | 0.9496774193548387 | 0.9460154241645244 | 0.02574370709382151 | true |
| character_substitution | 2523 | 0.9678953626634959 | 0.9494818652849741 | 0.9458064516129032 | 0.9476405946994183 | 0.02231121281464531 | true |
| separator_insertion | 2523 | 0.9667063020214031 | 0.942381562099872 | 0.9496774193548387 | 0.9460154241645244 | 0.02574370709382151 | true |
| unicode_confusable | 2523 | 0.9667063020214031 | 0.942381562099872 | 0.9496774193548387 | 0.9460154241645244 | 0.02574370709382151 | true |

## Threshold sensitivity

| Threshold | Precision | Recall | F1 | FPR | Selected |
|---:|---:|---:|---:|---:|---|
| 0.35 | 0.9463722397476341 | 0.9493670886075949 | 0.947867298578199 | 0.024285714285714285 | true |
| 0.4 | 0.9521531100478469 | 0.944620253164557 | 0.948371723590151 | 0.02142857142857143 | false |
| 0.45 | 0.9549114331723028 | 0.9382911392405063 | 0.9465283320031922 | 0.02 | false |
| 0.5 | 0.9594813614262561 | 0.9367088607594937 | 0.9479583666933548 | 0.017857142857142856 | false |
| 0.55 | 0.9702479338842975 | 0.9287974683544303 | 0.9490703314470493 | 0.012857142857142857 | false |
| 0.6 | 0.9732888146911519 | 0.9224683544303798 | 0.9471974004874087 | 0.011428571428571429 | false |

## Calibration

| Status | Samples | Brier score | Expected calibration error |
|---|---:|---:|---:|
| reported | 2523 | 0.027799898669269924 | 0.014206238187247425 |

## Repeated grouped validation

| Status | Folds per repetition | Repetitions | Evaluations | Gate pass rate | Mean accuracy | Mean precision | Mean recall | Mean F1 | Mean FPR |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| passed | 5 | 3 | 15 | 1.0 | 0.9660525276326922 | 0.9405867009174724 | 0.9503938141048432 | 0.9454337262715835 | 0.02693314299310017 |

## Duplicate and leakage audit

| Field | Duplicate groups | Duplicate rows | Cross-split groups |
|---|---:|---:|---:|
| clean_text | 386 | 1018 | 0 |
| combined_text | 385 | 1016 | 0 |
| model_text | 487 | 1320 | 0 |
| normalized_url | 0 | 0 | 0 |
| site_group | 169 | 362 | 0 |
Overall audit passed: **true**.

## Split integrity audit

| Status | Clean rows | Train rows | Test rows | Excluded rows | Failed checks |
|---|---:|---:|---:|---:|---|
| passed | 12960 | 10143 | 2523 | 294 | none |

## Offline inference speed

| Status | Samples/run | Runs | Mean ms | P50 ms | P95 ms | Max ms | Mean ms/sample |
|---|---:|---:|---:|---:|---:|---:|---:|
| reported | 2523 | 5 | 3059.585567800241 | 2518.8210609994712 | 3933.8321070026723 | 3933.8321070026723 | 1.2126775932620852 |

Scope: offline prediction on the evaluation host; browser, UI, and device latency are excluded.

## Visual artifacts

| Artifact | Status | Size (bytes) | SHA-256 recorded |
|---|---|---:|---|
| ablation_metrics | created | 60155 | true |
| calibration | created | 76545 | true |
| confusion_matrix | created | 44214 | true |
| threshold_sensitivity | created | 60740 | true |

## Scope exclusions

- runtime_device_evaluation: out_of_scope for this model progress report
- time_shifted_evaluation: out_of_scope for this model progress report

## Text-and-domain grouped slices

| Slice | Samples | Status | Accuracy | Precision | Recall | F1 | FPR |
|---|---:|---|---:|---:|---:|---:|---:|
| dom_text_length_high | 682 | failed | 0.969208211143695 | 0.8969072164948454 | 0.8877551020408163 | 0.8923076923076922 | 0.017123287671232876 |
| dom_text_length_low | 594 | failed | 0.9511784511784511 | 0.9401993355481728 | 0.9625850340136054 | 0.9512605042016807 | 0.06 |
| url_digit_count_high | 2523 | passed | 0.9659135949266746 | 0.9422336328626444 | 0.9470967741935484 | 0.9446589446589446 | 0.02574370709382151 |
| url_digit_count_low | 2133 | passed | 0.9732770745428974 | 0.9485815602836879 | 0.9502664298401421 | 0.9494232475598935 | 0.018471337579617834 |
| url_length_high | 617 | failed | 0.9594813614262561 | 0.8971428571428571 | 0.9573170731707317 | 0.9262536873156343 | 0.039735099337748346 |
| url_length_low | 664 | passed | 0.9728915662650602 | 0.9398496240601504 | 0.9259259259259259 | 0.9328358208955223 | 0.015122873345935728 |

## Text-and-domain grouped limitations

- government_education_domain_churn: pending: no authoritative slice labels in local data
- repeated_grouped_cv: fixed-candidate stability evaluation; not a nested estimate of hyperparameter-selection generalization
## Component checks

| Check | Status |
|---|---|
| model_tooling_unit | passed |

## Interpretation limits

Offline replay is not physical browser, Android, or Windows runtime proof.
A missing matrix cell remains pending. This report contains aggregate-safe
results and validated scenario detail where applicable; source code and
component unit tests remain in their owners.
