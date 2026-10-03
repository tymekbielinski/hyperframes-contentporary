# Onboarding a new brand

1. `cp -R brands/_template brands/<client-slug>` and set `"name": "<client-slug>"` in `tokens.json`.
2. Capture the client's brand guide / website / Figma. Record every source in `assets/MANIFEST.md`.
3. If the client has reference videos or an existing channel look, run the **Reference → style guide**
   procedure in `standards/core/pipeline.md` and map its findings onto the palette roles below.
4. Map their colours onto the palette roles (`ground`, `surface`, `text`, `accent`, `accentScript`,
   `status`). Rename `palettes/base.json` and add more palettes if the brand has distinct moods.
5. Fill `fonts`, choose a variant for each `kit` component, and list the `marks` the brand uses.
6. Fill `brand.md` (constant visual language) and `narrative.md`.
7. Validate: `python3 tools/brandcheck.py brands/<client-slug>`.
8. Render the brand proof sheet (Plan 4 tooling): full-screen title, subtitle, lower third and
   side screen text in every palette.
9. Tymek reviews the proof sheet. On approval set `"status": "approved"`. Only approved brands pass
   the QA gate.
