# DESIGN.md — ParAlert

## Theme
Dark. The scene: a worried parent on their phone in the evening. Dark reduces glare and feels
calm/private, not clinical. Avoids the "security tool → navy" reflex by tinting toward a soft
indigo ink, not corporate blue, with a calm teal accent for guidance (never alarm).

## Color (OKLCH, color strategy: Restrained)
Tinted-neutral ink scale + one calm accent for guidance. Severity & angle hues used only on
their own signifiers, never as decoration.

```
--ink:        oklch(0.17 0.012 270)   /* app background */
--surface:    oklch(0.22 0.014 270)   /* cards, bars */
--surface-2:  oklch(0.27 0.016 270)   /* chips, insets */
--border:     oklch(0.32 0.015 270)
--text:       oklch(0.96 0.005 270)
--text-muted: oklch(0.72 0.012 270)
--text-faint: oklch(0.56 0.012 270)

--accent:     oklch(0.74 0.10 205)     /* calm teal — guidance/recommendation, ≤10% of surface */

/* severity — communicates, never screams */
--sev-high:   oklch(0.63 0.19 25)
--sev-medium: oklch(0.78 0.14 80)
--sev-low:    oklch(0.74 0.15 150)

/* the 3 angles */
--angle-victim:    oklch(0.70 0.13 15)
--angle-aggressor: oklch(0.78 0.13 70)
--angle-bystander: oklch(0.72 0.10 235)
```

Never `#000`/`#fff`. Severity color appears as a small dot/label/meter, not as a card side-stripe.

## Typography
System stack (renders Hebrew well, zero network dependency):
`-apple-system, "Segoe UI", system-ui, "Helvetica Neue", Arial, sans-serif`.
Scale ratio ≥1.25. Weight contrast for hierarchy (400 body / 600 headings / 700 page title).
Body measure ≤70ch. Tabular numerals for scores/counts.

## Elevation
Flat first. One soft shadow level for raised surfaces (alerts, settings cards):
`0 1px 2px oklch(0 0 0 / 0.3), 0 8px 24px oklch(0 0 0 / 0.18)`. No glassmorphism.

## Motion (ease-out, exponential; no bounce)
```
--ease: cubic-bezier(0.22, 1, 0.36, 1);   /* ease-out-quint-ish */
--dur-fast: 140ms;  --dur: 220ms;  --dur-slow: 360ms;
```
Animate transform/opacity only, never layout. New alert: fade+rise. Tab/filter: quick state
transition. Toxicity meter: width grows on mount. Chat messages: stagger in. Respect
`prefers-reduced-motion`.

## Component notes
- **Alert**: full 1px border + subtle surface tint + a leading severity dot and severity label.
  No side-stripe borders (banned). Recommendation block carries the calm teal accent.
- **3-angle summary**: not three identical KPI tiles. One row, each angle a labeled count with
  its hue as a small marker; de-emphasized when zero.
- **Tabs / filter chips**: pill toggles, animated active state.
- **Settings**: grouped sections (profile, sensitivity, notifications, groups), not nested cards.
