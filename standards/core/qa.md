# QA Gate

Two stages: an automated gate that blocks the render, then a human sign-off before delivery.
Automated checks are implemented by `tools/qa` (Plan 3). Until it exists, run each check by hand.

## 1. Automated gate (blocks render)

| # | Check | Method |
|---|---|---|
| 1 | HyperFrames validity | `npx hyperframes check` |
| 2 | No lib fork | the project's `lib.lock` hashes equal root `lib/` |
| 3 | BRIEF complete | `format`, `brand` (status `approved`), `palette`, `font`, `captions` (Shorts) present; `python3 tools/brandcheck.py` passes and the palette/font/overrides choice is valid (`brandcheck.validate_choice`) |
| 4 | Seek-safety | static scan: no `Math.random`, `Date.now`, `repeat: -1`, CSS `infinite` animations |
| 5 | Blur law | every `feGaussianBlur` / `blur()` carries `data-blur-reason` = `focus`, `glow` or `wipe` (`wipe` only in Shorts); camera and whip blur only via `HFMotionBlur` |
| 6 | Easing vocabulary | no raw curves outside the named `ease.*` tokens |
| 7 | Captions | long-form: no caption layer except `kit.lower-third`; Shorts: matches the `captions` flag |
| 8 | Density | long-form: hook ≥ 60 % graphics, no face gap > 6 s, body gaps ≤ 30 s (BRIEF `screen_share` ranges exempt); Shorts ≈ 45 % |
| 9 | Settle before cut | the last 0.3 s of each full-frame scene is still (frame difference) |
| 10 | Render traps | text verified in rendered frames, not only snapshots (`standards/formats/shorts.md` §9b traps apply to every format); seek-flicker scan |

**Exceptions:** declared in the BRIEF under `exceptions:`, each with a reason (e.g. a recreated UI
that has no real screenshot). The gate passes declared exceptions and lists them in the preview pack.

## 2. Human review

1. **Preview pack** (generated): a contact sheet of every graphic, a draft render of the hook plus
   one body scene, the density timeline, and the exceptions list.
2. **Sign-off by whoever ran the build**, using these five questions. Tymek sees the final. Each
   question must be answerable by someone other than Tymek:
   1. **Smooth?** Moves ease in and settle; nothing snaps, jitters or overshoots; scenes hold still
      before they cut.
   2. **On-brand?** Ground, surfaces, headline treatment and marks match `brands/<brand>/brand.md`;
      colours come from the chosen palette.
   3. **Readable?** Every word on screen can be read at normal speed; nothing is cropped, ghosted or
      too small at phone size.
   4. **Synced?** Each graphic lands on the words it illustrates (see the transcript times).
   5. **Earns its place?** Each graphic explains, proves or emphasises something; roughly 80 %
      familiar (screenshot + highlight, whiteboard-style marks), 20 % custom brand moments.
3. Final render and delivery. Client videos then go to the client as V1 via `client-ops`.

**Promotion rule:** a review finding that changes how future videos should be made is written into
`standards/` or `brands/<brand>/` in the same session. Never only into a BRIEF or agent memory.
