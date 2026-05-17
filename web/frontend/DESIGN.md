# Frontend design system

This file is the source of truth for the visual language of the Vue 3
SPA. It's written so that design-aware tools (Anthropic's Claude
Design, in particular) can ingest the frontend, understand the
semantic tokens and reusable components, and produce a faithful
restyling pass without having to re-derive conventions from scattered
inline classes.

If you change the look of the app, update this file in the same PR.

---

## Inputs to feed a design tool

When asking Claude Design (or similar) to restyle this app, give it:

1. This file (`web/frontend/DESIGN.md`).
2. `tailwind.config.js` — the semantic token registry.
3. The `web/frontend/src/components/` folder — the building blocks.
4. The baseline screenshots in `docs/screenshots/` — the "before"
   state, at both desktop (1280×820) and mobile (390×844) viewports.
5. `CLAUDE.md` and `README.md` — product context (what the app does
   and the constraints).

**Restyling brief — what should change**:
- Move from a flat utilitarian look to a more polished, branded UI.
- Stronger visual identity for the dual-brand parity (Spotify
  ↔ YouTube Music). Today this is implied by one accent color per
  provider; the design pass can lean into it more.
- Microinteractions are welcome on hover/focus states, progress bar
  fills, and the live log row append. Today only the progress bar
  has a transition.
- Type hierarchy is functional but bland — tightening can help.
- Empty/error/loading states deserve dedicated illustration or
  iconography (the codebase currently uses plain text).

**Restyling brief — what should NOT change**:
- The structure of the 5 screens (Home → Login → Playlists →
  Transfer → Report) and the order of the flow. The product is
  state-driven and Vue Router-bound; changing the navigation breaks
  the engine wiring.
- The dual-brand assumption: both providers must remain visually
  symmetric. Don't favor one over the other.
- The progress event vocabulary in `TransferView.vue`
  (`track_matched`, `track_unmatched`, `playlist_started`,
  `playlist_done`, `job_started`, `job_done`, `error`). Visual
  treatment of each is welcome; renaming or merging is not.
- The Tailwind-first stack. Generated styles should be Tailwind
  utilities (custom CSS only when a token can't express it).
- Accessibility floor: keyboard focus rings, 4.5:1 contrast on text,
  44×44 tap targets on mobile.

---

## Semantic tokens (`tailwind.config.js`)

The Tailwind config exposes named color roles, not raw shades. A
restyling pass should usually retune the *values* in the config
without touching call sites.

| Token | Default mapping | Role |
| --- | --- | --- |
| `bg-page` | `slate-50` | Page background. |
| `bg-surface` | `white` | Cards, header, list rows. |
| `bg-surface-muted` | `slate-100` | Subtle insets, code-like blocks. |
| `border-border` / `border-divider` | `slate-200` | Card borders and list separators. |
| `text-fg-primary` | `slate-900` | Headings and body. |
| `text-fg-secondary` | `slate-500` | Labels, metadata. |
| `text-fg-muted` | `slate-400` | "Inactive" elements. |
| `*-spotify-{50..900}` | emerald scale | Spotify brand. |
| `*-ytmusic-{50..900}` | rose scale | YouTube Music brand. |
| `*-success-{…}` | emerald | "Matched", "connected". |
| `*-warning-{…}` | amber | "Unmatched". |
| `*-danger-{…}` | red | Errors. |
| `*-info-{…}` | sky | Per-playlist progress bar, links, focus rings. |
| `*-accent-{…}` | slate | Primary CTA (the neutral "Continue" / "Transfer" buttons). |

Other tokens:

| Token | Default | Role |
| --- | --- | --- |
| `rounded-card` | `0.875rem` | All cards. |
| `rounded-control` | `0.5rem` | Buttons, inputs, selects. |
| `shadow-card` | very soft 2-layer | Resting elevation for cards & buttons. |
| `shadow-card-hover` | deeper shadow | Hover on interactive cards. |
| `max-w-shell` | `64rem` | Page container width. |
| `font-sans` | system stack | Default text. |
| `font-mono` | system mono | Live log entries. |

---

## Reusable components

These live in `web/frontend/src/components/` and are the canonical
building blocks. Restyling them cascades to all five views.

### `AppCard.vue`
Card surface with optional `variant="interactive"` (hover lifts +
deeper shadow). Padding presets: `sm | md | lg`.

### `AppButton.vue`
The single button primitive. Tones:
- `primary` — neutral CTA (`bg-accent-900 text-white`).
- `spotify` / `ytmusic` — provider-branded actions.
- `ghost` — secondary action with a border.
- `danger` — destructive.

Sizes: `sm | md | lg`. Optional `block`. Always renders a focus ring
keyed off `info-500`.

### `StatusDot.vue`
Compact `● Label` indicator used in the header. Active state shows a
glowing halo (`shadow-[0_0_0_4px_rgba(16,185,129,0.15)]`).

### `ProgressBar.vue`
Label + counter + animated fill. Tone `spotify | info | accent`. Used
twice in `TransferView`: overall (`spotify`) and per-playlist (`info`).

### `StatTile.vue`
Big-number tile on the Report view. Tone `success | warning | muted`.

### `PageHeader.vue`
Title + subtitle. Mobile-first sizing
(`text-2xl sm:text-3xl font-bold tracking-tight`).

---

## Layout

- Page container: `max-w-shell mx-auto px-4 sm:px-6 py-6 sm:py-10`.
- Sticky header with `backdrop-blur` over the surface color at 80%
  opacity.
- Footer is purely informational (copyright/credits).
- Vertical rhythm inside views: `space-y-6 sm:space-y-8`.
- Mobile-first: every grid starts at `grid-cols-1`; expand at `sm:`
  (3-up tiles, 2-col form rows) or `md:` (paired cards).

---

## Tone of voice

- Headings: imperative present ("Transfer your playlists", "Connect
  both accounts", "Pick source playlists").
- Helper text: one sentence, second-person, no exclamation marks.
- Buttons: verb + noun ("Connect Spotify", "Transfer 3 playlists").
- Error messages: lowercase, no emoji ("YT Music auth expired").

---

## Accessibility notes (must hold after restyling)

- All interactive elements must keep the `focus-visible:outline-info-500`
  treatment (`AppButton` already does).
- Contrast: don't lower `fg-secondary` below the slate-500 equivalent
  without re-checking.
- Tap targets ≥ 44×44 on mobile (`size="md"` button is 40px tall —
  acceptable on desktop; restyling for mobile should bump to
  `size="lg"` where needed).
- Live log uses `font-mono` — keep it, it helps scanning event types.
