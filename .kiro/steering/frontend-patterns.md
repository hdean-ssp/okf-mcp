---
inclusion: fileMatch
fileMatchPattern: "**/ui/**,**/web/**,**/frontend/**,**/*.tsx,**/*.jsx,**/components/**"
---

# Frontend Patterns

Loaded when working on React / frontend code.

## Stack

- React 18+ with function components and hooks
- TypeScript strict mode — no `any` without explicit justification
- Vite for dev and build
- Tailwind for styling — avoid writing custom CSS
- TanStack Query for server state
- React Hook Form + Zod for forms
- React Router for routing
- Vitest + React Testing Library for tests

## Component Structure

- One component per file
- Components are functional; avoid class components
- Use custom hooks to extract logic from components
- Keep components under 200 lines; split when they grow

## State

- Server state → TanStack Query (never `useState` for data fetched from the API)
- Form state → React Hook Form
- Ephemeral UI state → `useState`
- Complex local state → `useReducer`
- Global UI state → Zustand (not Redux unless there's a specific reason)

## API Calls

- Centralised API client with interceptors for auth, errors, correlation IDs
- Every mutation shows optimistic UI where sensible
- Every mutation handles error states explicitly
- Retry transient failures automatically (via TanStack Query)

## Accessibility (Non-Negotiable)

- Semantic HTML — use the right element, not `<div>` for everything
- ARIA labels for icons, interactive non-text elements
- Keyboard navigation — every interactive element tab-reachable
- Focus management — especially for modals, dialogs, route changes
- Form labels associated with inputs
- Colour contrast meets WCAG 2.1 AA
- Test with keyboard only and with a screen reader before merging

## Authentication

- Token stored in memory or httpOnly cookie, never localStorage for sensitive tokens
- Auth state in a dedicated context
- Protected routes use a route guard component
- Automatic token refresh before expiry
- Logout clears all client state

## Performance

- Code-split routes with `lazy()` and `Suspense`
- Images optimised and lazy-loaded
- Bundle size budget enforced in CI (< 250KB gzipped for main bundle)
- Avoid unnecessary re-renders — use `useMemo`, `useCallback` where measurable
- Core Web Vitals tracked in production

## Testing

- Unit tests for hooks and utility functions
- Component tests for interactive components (not just snapshots)
- E2E tests for critical user flows (Playwright)
- Mock the API at the boundary; don't test the API in component tests
