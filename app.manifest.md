VoltsWorks Power Tools — companion diagrams for the oneshot-power-calc toolkit

Audience: builders, maintenance leads, and educator demos who want to see the power tools as a visual toolkit, not a single calculator.

Goals
- Show VoltsWorks internals (electrical calculator, funding sieve, videos/ideas ledger) as three explorable cells.
- Preserve showcase-grade archify geometry (dark, labelClear, 1200 baseline, clean routes, kiosk-native).
- Leave runtime gaps (video frame, auth, infra) intentionally blank and document them for a later build pass.

Non-goals
- Ship new calculator code, video frame, or infra.
- Represent incomplete backend as complete boxes.

Performance target
- One breadcrumb spot-aware render under 80ms on a modern laptop.
- Layout resolves before any document-visible paint.

Acceptance criteria
- Themeless emit; dark read with no color shift.
- All routes clear; no label collision; no edge through unrelated node.
- 3 core cells: electrical, sieve, ideas ledger.
- Video module is present but visibly incomplete/future.
- Test harness explicitly shown as a pulse along the electrical path.
