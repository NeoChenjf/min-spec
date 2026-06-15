---
gate_id: testC
version: 0.1.0
phase: verify
generated_at: 2026-06-15T03:34:18Z
decision: block
---

## Gate Result

| gate | status | exit_code | cmd |
|---|---|---|---|
| build | skipped | - | - |
| test | fail | 1 | node -e "console.log(\"ALL TESTS PASSED\"); process.exit(1)" |

## Output Contract
```json
{
  "decision": "block",
  "evidence_path": "docs/meta/gates/testC-gate.md",
  "blocking_reason": "test gate exited 1",
  "next_action": "修复 test 失败后重跑 scripts/gate.py"
}
```
