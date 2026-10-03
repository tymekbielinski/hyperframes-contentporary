# Onboarding a new brand

1. `cp -R brands/_template brands/<client-slug>` and set `"name": "<client-slug>"` in `tokens.json`.
2. Capture the client's brand guide / website / Figma. Record every source in `assets/MANIFEST.md`.
3. Map their colours onto the palette roles (`ground`, `surface`, `text`, `accent`, `accentScript`,
   `status`). Rename `palettes/base.json` and add more palettes if the brand has distinct moods.
4. Fill `fonts`, choose a variant for each `kit` component, and list the `marks` the brand uses.
5. Fill `brand.md` (constant visual language) and `narrative.md`.
6. Validate: `python3 tools/brandcheck.py brands/<client-slug>`.
7. Render the brand proof sheet (Plan 4 tooling): full-screen title, subtitle, lower third and
   side screen text in every palette.
8. Tymek reviews the proof sheet. On approval set `"status": "approved"`. Only approved brands pass
   the QA gate.
