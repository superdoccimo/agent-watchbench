# Agent Watchbench Repository Secret Scan

## Summary
- root: examples/secret-scan-root
- files checked: 3
- findings: 2
- value policy: secret values are not printed

## Findings
- .env.sample:1 [token] value redacted
- subdir/config.txt:1 [client-secret] value redacted
