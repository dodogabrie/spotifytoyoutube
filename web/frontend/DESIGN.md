# Frontend design system

This file documents the visual language used by the Vue 3 SPA in
`web/frontend/`. It's intentionally explicit so design-aware tools
(e.g. Anthropic's Claude Design) can read it and reproduce or extend
the UI without having to infer everything from inline Tailwind classes.

If you change the look of the app, update this file in the same PR.

---

## Product context

- One-page-per-step flow: Home → Login → Playlists → Transfer → Report.
- Two **provider brands** appear side-by-side throughout the app:
  Spotify and YouTube Music.
- Calm, document-style UI: light surfaces, restrained accent colors,
  no large hero imagery. The visual focus is the progress log, not
  marketing.

---

## Tokens

Colors come from Tailwind's default palette (no custom config). The
project uses three "roles":

| Role | Tailwind family | Notes |
| --- | --- | --- |
| Background | `slate-50` | Page background (`body`). |
| Surface | `white` | Cards, list rows, header bar. |
| Border / divider | `slate-200` | Card borders and `divide-slate-200` on lists. |
| Text primary | `slate-900` | Headings and body. |
| Text secondary | `slate-500` | Labels, metadata, descriptions. |
| Text muted | `slate-400` | "Inactive" status dots, "no playlists" empty state. |
| Spotify brand | `emerald-500/600/700` | Spotify connect button, "matched" progress fill, hover ring on the Spotify direction card. |
| YouTube Music brand | `rose-500/600/700` | YT Music connect button, hover ring on the YT Music direction card. |
| Action / CTA | `slate-900` (bg) / `white` (text) | Primary buttons, e.g. "Continue", "Transfer N playlist(s)". |
| Info | `sky-500` (progress) / `blue-600` (links, "started"/"done" log lines) | Per-playlist progress bar and informational log entries. |
| Success | `green-600/700` | Connected status dot, "matched" log entries. |
| Warning | `yellow-700` / `amber-600` | "Unmatched" log entries and the unmatched counter. |
| Danger | `red-600/700` | Error messages and error log entries. |

Typography: Tailwind defaults (system stack). Sizes in use:
- `text-3xl font-bold` — landing headline.
- `text-2xl font-bold` — step page headlines.
- `text-lg font-semibold` — header brand mark and card titles.
- Body — default size, `text-slate-900`.
- `text-sm` — secondary labels, log entries.
- `text-xs uppercase tracking-wide` — small section labels inside cards.

Radii & elevation:
- Cards: `rounded-xl border border-slate-200 bg-white` (no shadow at
  rest, optional `hover:shadow` on click-targets).
- Buttons: `rounded` (Tailwind default) for most, full-width buttons
  in cards use `rounded px-4 py-2`.
- Form inputs (`<input>`, `<select>`): `border border-slate-300 rounded
  px-3 py-2`.

Spacing:
- Page container: `max-w-5xl mx-auto px-6 py-8`.
- Card inner padding: `p-4`, `p-6`, or `p-8` depending on density
  (denser for the playlist list, looser for the landing/direction
  cards).
- Vertical rhythm between sections: `space-y-6` on the page root,
  `space-y-4` inside cards.

States:
- Disabled buttons: `disabled:opacity-40`.
- Hover on click-target cards: `hover:border-<brand>-500 hover:shadow`.
- Status dot pattern: `text-green-600` if connected, `text-slate-400`
  otherwise. Always a leading `●` glyph.

---

## Component patterns

These are the recurring patterns extracted from the existing views.
They are not (yet) Vue components — they live as inline class strings
— but treat them as the canonical implementations.

### Page shell

```html
<section class="space-y-6">
  <header>
    <h1 class="text-2xl font-bold">…</h1>
    <p class="text-slate-500 text-sm mt-1">…</p>
  </header>
  …
</section>
```

The top-level `<App>` wraps everything in
`max-w-5xl mx-auto px-6 py-8`, so views never set their own
horizontal width.

### Card

```html
<div class="rounded-xl border border-slate-200 bg-white p-6">…</div>
```

### Clickable card (direction picker)

```html
<button class="rounded-xl border border-slate-200 bg-white p-8 text-left
               hover:border-emerald-500 hover:shadow">
  <div class="text-sm uppercase tracking-wide text-slate-400">Direction</div>
  <div class="text-xl font-semibold mt-1">Spotify → YouTube Music</div>
  <p class="mt-3 text-slate-500">…</p>
</button>
```

The Spotify card uses `hover:border-emerald-500`, the YT Music card
uses `hover:border-rose-500`.

### Primary action

```html
<button class="bg-slate-900 text-white px-5 py-2 rounded
               disabled:opacity-40">
  Continue
</button>
```

### Brand action (per provider)

```html
<!-- Spotify -->
<button class="bg-emerald-600 text-white px-4 py-2 rounded
               hover:bg-emerald-700">Connect Spotify</button>

<!-- YouTube Music -->
<button class="bg-rose-600 text-white px-4 py-2 rounded
               hover:bg-rose-700">Connect YouTube Music</button>
```

### Status dot (in the header)

```html
<span :class="connected ? 'text-green-600' : 'text-slate-400'">● Spotify</span>
```

### Form row inside a card

```html
<div class="rounded-xl border border-slate-200 bg-white p-4
            grid grid-cols-1 md:grid-cols-3 gap-3 items-center">
  <input class="border border-slate-300 rounded px-3 py-2 col-span-2" />
  <select class="border border-slate-300 rounded px-3 py-2">…</select>
</div>
```

### Selectable list (playlists)

```html
<div class="rounded-xl border border-slate-200 bg-white">
  <div class="px-4 py-2 border-b border-slate-200 …">Select all</div>
  <ul class="divide-y divide-slate-200">
    <li class="px-4 py-3 flex items-center gap-3">
      <input type="checkbox" />
      <div class="flex-1">
        <div class="font-medium">Playlist name</div>
        <div class="text-xs text-slate-500">N tracks</div>
      </div>
    </li>
  </ul>
</div>
```

### Progress bar

```html
<div>
  <div class="flex justify-between text-sm">
    <span>Overall</span><span>3/10 (30%)</span>
  </div>
  <div class="h-2 rounded bg-slate-100 mt-1 overflow-hidden">
    <div class="h-full bg-emerald-500 transition-all" style="width: 30%" />
  </div>
</div>
```

The overall (cross-playlist) bar uses `bg-emerald-500`; the
per-playlist bar uses `bg-sky-500`. Both ride on a
`bg-slate-100` track.

### Live log row

```html
<li class="px-4 py-1 border-b border-slate-100 last:border-0 font-mono text-sm">
  <span class="text-green-700">[track_matched]</span> Playlist - Song title
</li>
```

Color by event type:
- `track_matched` → `text-green-700`
- `track_unmatched` → `text-yellow-700`
- `playlist_started` / `playlist_done` → `text-blue-700`
- `error` → `text-red-700`

### Big-number tile (Report view)

```html
<div class="rounded-xl border border-slate-200 bg-white p-4">
  <div class="text-xs text-slate-500 uppercase">Matched</div>
  <div class="text-3xl font-bold text-emerald-600 mt-1">42</div>
</div>
```

Color of the big number by tile: matched=`emerald-600`,
unmatched=`amber-600`, skipped=`slate-600`.

---

## When extending the UI

- Keep both providers symmetric. If a feature is added for Spotify,
  add the YT Music counterpart in the matching shade
  (emerald ↔ rose).
- Prefer one of the patterns above before inventing a new one. If a
  pattern repeats three times, lift it into a Vue component under
  `web/frontend/src/components/` and update this doc.
- Don't introduce a new color family without adding the role to the
  "Tokens" table. Two ad-hoc accent colors will collapse the visual
  hierarchy fast.
- Animations: only `transition-all` on progress bar widths is in use
  today. Match that restraint — no entrance animations on cards.
- Don't deepen the elevation language. Cards stay flat at rest;
  hover may add `shadow`, never anything heavier.
