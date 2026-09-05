# Gamblock-AI Golang Report

This is the canonical aggregate report for this technology. It is
generated from validated public evidence and aggregate command results.
Raw URL, domain, DOM, browsing history, screenshot, serial, credential,
participant, and raw log data are never included.

This report covers the Go backend component checks.

## Component checks

| Check | Status |
|---|---|
| backend_unit | passed |
| backend_integration | passed |

## Supplemental explicit verification

These checks were executed explicitly on 2026-09-05 and are recorded as
aggregate results only:

| Check | Status | Aggregate result |
|---|---|---|
| backend_build | passed | `go build ./...` completed via `make verify` |
| backend_vet | passed | `go vet ./...` completed via `make verify` |
| backend_race | passed | `go test -race ./...` completed via `make verify`; no race report |
| backend_coverage | passed | `internal/*`: 75.2% (9,997/13,289 statements) |

Coverage is measured against application-owned `internal/*` packages, which is
the 75% target scope. The unfiltered `./...` profile is 13.1% because it also
includes generated `ent/` code and command entrypoints without test files; that
figure is retained as a limitation and is not used for the application target.

## Interpretation limits

Offline evaluation is not physical browser, Android, or Windows runtime proof.
A missing matrix cell remains pending. This report contains aggregate-safe
results and validated scenario detail where applicable; source code and
component unit tests remain in their owners.
