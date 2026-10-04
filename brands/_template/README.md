# Onboarding a new brand

1. `cp -R brands/_template brands/<client-slug>` and set `"name": "<client-slug>"` in `tokens.json`.
2. Capture the client's brand guide / website / Figma. Record every source in `assets/MANIFEST.md`.
3. If the client has reference videos or an existing channel look, run the **Reference → style guide**
   procedure in `standards/core/pipeline.md` and map its findings onto the palette roles below.
4. Map their colours onto the palette roles (`ground`, `surface`, `text`, `accent`, `accentScript`,
   `status`). Rename `palettes/base.json` and add more palettes if the brand has distinct moods. Set each palette's `mode` (`dark` or `light`) — the ground look follows it.
5. Fill `fonts`, choose a variant for each `kit` component, and list the `marks` the brand uses.
6. Fill `brand.md` (constant visual language) and `narrative.md`.
7. Validate: `python3 tools/brandcheck.py brands/<client-slug>`.
8. Build and render the brand proof sheet — full-screen title, subtitle, lower third and side screen
   text in every palette, one scene per palette:
   `python3 tools/proof_sheet.py <client-slug>` (writes `videos/proof-<client-slug>/`), then
   `python3 tools/qa.py videos/proof-<client-slug>` (every check passes except 3 while the brand is still
   `draft`), then render the stills the tool prints
   (`npx hyperframes snapshot videos/proof-<client-slug> --at … --no-end -o videos/proof-<client-slug>/renders/proof-stills`)
   and the video (`npx hyperframes render videos/proof-<client-slug> -o videos/proof-<client-slug>/renders/proof.mp4`).
9. Tymek reviews the proof sheet. On approval set `"status": "approved"`. Only approved brands pass
   the QA gate.
