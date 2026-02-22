# UX Design Brief: Big Apple Cinemas

## Objective

Design a modern, high-conversion, production-ready UX/UI for Big Apple Cinemas that is responsive across mobile, tablet, desktop, and large monitors.

## Product Goal

Deliver a polished, recruiter-impressive visual system and end-to-end booking experience that is realistic to implement in React + Tailwind.

## Design Direction

- Cinematic, premium visual language with strong brand character.
- Strong typography hierarchy and intentional spacing.
- Clear interaction states and fast decision UX.
- WCAG AA contrast and accessible components.
- Subtle motion to support flow, not distract.

## Breakpoints

- Mobile: 360 / 390
- Tablet: 768
- Desktop: 1440
- Large monitor: 1920+

## Core Flows and Screens

1. Home: featured, now playing, coming soon.
2. Movies: list, search, filters.
3. Movie detail: trailer, runtime, rating, cast, showtimes by theater/date.
4. Seat selection: interactive map, legend, sticky summary, mobile zoom support.
5. Hold countdown: 8-minute reservation timer with clear recovery path.
6. Checkout: summary, pricing breakdown, promo code, payment method selection.
7. Payment states: processing, success, failure, retry.
8. Order confirmation: ticket summary + QR tickets.
9. My Tickets: active and past tickets/orders.
10. Login/Register.
11. Loading, empty, and error states for all key pages.
12. Admin dashboard basics: movies, theaters, showtimes, occupancy, sales snapshots.

## Critical UX Behaviors

- Avoid user confusion during hold and expiry moments.
- Reflect seat status updates in near real-time without jarring UI shifts.
- Reinforce trust at checkout with security and refund cues.
- Keep mobile booking one-handed and low-friction.
- Handle edge cases clearly:
  - seat becomes unavailable during checkout,
  - payment fails and retry,
  - ticket already scanned.

## Required Design Deliverables

- Information architecture and sitemap.
- User flow diagrams (browse -> seat select -> pay -> ticket received).
- Design system:
  - color tokens,
  - typography scale,
  - spacing scale,
  - components and state variants.
- High-fidelity screen specs for each breakpoint.
- Motion and micro-interaction rules.
- Accessibility checklist.
- Developer handoff notes for component behavior and responsive rules.

## Suggested Design Token Baseline

- Semantic colors: `bg`, `surface`, `surface-muted`, `text-primary`, `text-secondary`, `accent`, `success`, `warning`, `danger`.
- Radius scale: `4, 8, 12, 16, 24`.
- Spacing scale: `4, 8, 12, 16, 20, 24, 32, 40, 48, 64`.
- Type scale: `12, 14, 16, 18, 20, 24, 32, 40, 52`.
- Motion durations: `120ms`, `180ms`, `240ms`, `320ms`.

## Handoff Requirements for Engineering

- Annotate every interactive component with idle/hover/focus/pressed/disabled/loading/error states.
- Define responsive behavior by breakpoint for each page section.
- Provide seat-map interaction rules for keyboard and touch.
- Include copy for empty/error states and expiration recovery dialogs.
- Include redlines for spacing, typography, and component sizing.
