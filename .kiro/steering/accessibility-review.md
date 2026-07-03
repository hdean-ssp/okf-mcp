---
inclusion: manual
---

# Accessibility Review

Manually invoked via `/accessibility-review` for accessibility audits of UI code.

## Scope

Audit the UI code for WCAG 2.1 AA conformance.

## Semantic HTML

- Using `<button>` for buttons, `<a>` for links (not `<div onClick>`)
- Headings used hierarchically (`<h1>` → `<h2>` → `<h3>`, no skips)
- Lists as `<ul>`, `<ol>`, `<li>`
- Landmarks (`<header>`, `<main>`, `<nav>`, `<footer>`) on every page

## Keyboard

- Every interactive element reachable via Tab
- Focus visible (never `outline: none` without a replacement)
- Focus order logical (reflects visual order)
- Skip links for long navigation
- No keyboard traps

## Screen Reader

- All images have `alt` text (decorative images: `alt=""`)
- Icons that convey meaning have ARIA labels
- Form inputs have associated `<label>` elements
- Errors announced via ARIA live regions
- Modal focus management (focus moves to modal on open, returns on close)

## Colour and Contrast

- Text contrast ratio ≥ 4.5:1 (normal text) or 3:1 (large text)
- Don't rely on colour alone to convey information (use icons, text, patterns)
- Focus indicators have sufficient contrast

## Forms

- Every input has a `<label>`
- Required fields marked (both visually and to assistive tech)
- Error messages associated with inputs via `aria-describedby`
- Fieldsets group related inputs

## Dynamic Content

- Loading states announced
- Route changes announced
- Toast/notification messages have appropriate ARIA roles

## Report Format

1. **Summary** — conformance level, critical issues
2. **Findings by severity** — Critical (blocks use), Serious (major impairment), Moderate, Minor
3. **For each finding**: WCAG criterion, location, description, remediation
4. **Automated scan results** — if axe-core or similar was run
5. **Manual test notes** — keyboard-only and screen reader findings
