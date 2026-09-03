# Next.js / website testing

This folder defines the testing scope for the Next.js website. Website source,
fixtures, and production unit tests remain in `../gamblock-ai-website/` in the
umbrella workspace; they are not copied here.

The cross-system runner invokes the complete website unit-test suite and the
Playwright browser E2E suite. It records only aggregate status, duration, and
an output hash in the canonical summary:

```sh
python3 docs/tools/run_evaluation.py --workspace-root .. --run-code-tests --component website
```

The checks are reported separately as `website_unit` (`npm test`) and
`website_e2e` (`npm run e2e`). The website repository owns the Playwright
configuration, server startup, and test fixtures.

Do not publish URLs, account data, credentials, screenshots, traces, or raw
browser output. The canonical report contains aggregate check status only.
