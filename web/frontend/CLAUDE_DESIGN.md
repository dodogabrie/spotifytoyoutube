# Driving Claude Design for this project

Operator runbook: exactly what to upload to Claude Design and what
prompt to paste to get a useful restyling pass. Keep this file in
sync with `DESIGN.md`.

---

## 1. Inputs to feed it

### If Claude Design can point at the Git repo
Point it at `dodogabrie/spotifytoyoutube` and tell it to scope its
reading to `web/frontend/` and `docs/screenshots/`. Then proceed to
section 3.

### If you need to upload files manually
Upload these, in this order — order matters because the first files
anchor the context:

1. **`web/frontend/DESIGN.md`** — the brief. Single most important
   file. Tells it what the design system is, what it may change,
   what it must not change, and the accessibility floor.
2. **`web/frontend/tailwind.config.js`** — the semantic token
   registry. Restyling = retune the values, not the names.
3. **`web/frontend/src/components/`** — every `.vue` file. These are
   the canonical building blocks (`AppCard`, `AppButton`,
   `StatusDot`, `ProgressBar`, `StatTile`, `PageHeader`).
4. **`web/frontend/src/views/`** — the 5 screens, in order: Home,
   Login, Playlists, Transfer, Report. Internal markup can be
   refined, the routes can't.
5. **`docs/screenshots/`** — all 10 PNGs (desktop + mobile of each
   route). Visual baseline.
6. **`CLAUDE.md`** + **`README.md`** — product context. What the
   app does, what the engine event vocabulary is, what the dual-brand
   constraint is.

Skip (these aren't relevant to design and only add noise):
- The Python `core/`, `cli/`, `web/backend/` folders.
- `tests/`.
- `node_modules/`, `dist/`, `reports/`, `secrets/`.

---

## 2. What NOT to upload

- The current `web/frontend/src/views/*.vue` if you want a bolder
  redesign. They constrain its imagination toward the existing
  layout. Trade-off: skipping them means you'll re-wire the result
  into the views by hand. For a polish pass, keep them. For a fresh
  look, drop them and rely on `DESIGN.md` + screenshots.
- Anything from `secrets/` or `.env`. Obvious but stated.

---

## 3. Prompt to paste

Copy this verbatim into the chat panel as the first message:

```
Restyle the existing Vue 3 SPA in web/frontend/. Read DESIGN.md
first — it has the brief, the semantic Tailwind tokens registry,
the reusable components, the do/don't rules and the accessibility
floor. Use the screenshots in docs/screenshots/ as the visual
"before" baseline.

Goal: turn the current utilitarian look into a polished, branded
product UI. Lean into the dual-brand identity (Spotify ↔ YouTube
Music) — keep parity, never favor one. Tighten the type hierarchy.
Add restrained microinteractions on hover, focus, and progress.
Design real empty / error / loading states (today they are plain
text).

Hard constraints (do not violate):
- Do not restructure the 5 screens or the Vue Router flow
  (Home → Login → Playlists → Transfer → Report).
- Do not rename or merge the progress event types used in
  TransferView.vue (track_matched, track_unmatched,
  playlist_started, playlist_done, job_started, job_done, error).
- Keep both providers visually symmetric — no asymmetric emphasis.
- Output Tailwind utilities only. Custom CSS only when a token
  cannot express it.
- Preserve keyboard focus rings, 4.5:1 text contrast and 44×44
  tap targets on mobile.
- Components in src/components/ may change their internal markup
  freely, but their props and slots must stay backward-compatible.

Deliverables, in this order:
1. Mobile + desktop mockups for each of the 5 screens. Pause for
   my review before generating code.
2. Updated tailwind.config.js (token values only — same names).
3. Updated src/components/*.vue.
4. (Optional) new components for empty / error / loading states.
5. A short changelog summarizing what changed and why.
```

---

## 4. Iteration tips

- After the first mockup pass, ask Claude Design to **diff** its
  proposal against the screenshots before generating code. This
  catches drift early.
- If a screen feels off, ask for **three variants side by side**
  rather than one revision — comparison is cheaper than blind
  refinement.
- For the Transfer view (live log + progress), ask explicitly for
  a "running" state mockup and a "completed" state mockup. They
  read very differently and the current screenshot only shows the
  empty waiting state.
- When the result looks good, ask it to **export the updated files
  as a patch** (the tool can produce raw file contents). Then apply
  with `git apply` locally and run `npm run build` before
  committing.
- If it proposes a new dependency (icon library, animation lib),
  push back: this project intentionally has no design deps beyond
  Tailwind. Suggest inline SVGs and CSS transitions instead.

---

## 5. After the pass

- Run `npm run build` in `web/frontend/` (must pass with no
  TypeScript errors).
- Run `.venv/bin/python -m pytest -q` (sanity check that the
  Python side is untouched).
- Re-shoot the screenshots with `node /tmp/screenshot.mjs` (or
  any equivalent Playwright script) so `docs/screenshots/`
  reflects the new baseline for the **next** restyling pass.
- Update `DESIGN.md` if any token names, components or rules
  changed.
