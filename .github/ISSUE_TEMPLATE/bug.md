---
name: Bug Report
about: Report a bug with structured context so both humans and AI agents can act on it immediately
title: "[Bug] "
labels: bug
assignees: ''
---

# [Bug] <title>

<!-- Replace <title> above with a concise one-line description of the bug.
     Describe the symptom, not the fix. No period.
     Example: "Export CSV button produces empty file on Safari" -->

## Summary

<!-- 1-2 sentences. What is broken and what is the user-visible impact?
     No repro steps here, no speculation about cause. -->

## Environment

<!-- List as key: value pairs. Include only fields you can verify — omit unknowns rather than guessing. -->

- **Service/Product:**
- **Environment:** (dev / test / prod)
- **OS + version:**
- **App/package version:**
- **Branch or commit SHA:**
- **Cloud:** (AWS ECS Fargate / Azure AKS / local Docker)

## Reproducibility

<!-- One of: "Always", "Intermittent", "Once", "Not verified".
     If intermittent, add frequency (e.g. "roughly 1 in 5 attempts"). -->

## Steps to Reproduce

<!-- Numbered list. Start from a clean, known state. Each step is one observable action.
     A stranger with no context should be able to follow this and hit the bug. -->

1.
2.
3.

## Expected vs Actual

<!-- Two short paragraphs. Be concrete — no "it breaks". -->

**Expected:**

**Actual:**

## Logs / Error Output

<!-- Fenced code block. Include the stack trace, error message, or relevant log lines.
     Trim aggressively to the frames that matter. If none, write "None captured." -->

```
```

## Workaround

<!-- Any temporary way a user can avoid or work around the bug? If none, write "None known." -->

## Suspected Root Cause & Affected Files

<!-- Your hypothesis about the cause, followed by a bulleted list of relevant files as
     `path/to/file.ext:line`. Mark as "Unconfirmed" unless verified.
     If you have no hypothesis, write "Unknown" — do not fabricate one. -->

## Acceptance Criteria

<!-- Checklist defining "fixed". Each item is independently verifiable.
     Include both the positive case (bug no longer reproduces) and regression guards. -->

- [ ]
- [ ]

## Agent Notes

<!-- FOR KIRO AGENTS ONLY — leave blank when filing manually.
     When the developer or support-engineer agent triages this, they fill:
     - Related services / data flows touched
     - Upstream/downstream dependencies affected
     - Relevant steering files or architecture constraints
     - Suggested investigation approach -->
