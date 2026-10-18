# Generated automation tests

Review generated selectors, paths, expected values, and credentials before use.

## Run API tests
`TARGET_API_URL=https://your-api.example pytest -m "not ui" -v`

## Run browser tests
Install browsers with `playwright install chromium`, then run:
`TARGET_WEB_URL=https://your-app.example pytest -m ui -v`

Generated tests are a reviewed starting point, not a replacement for QA judgment.
