# Animation Reference Library

Every brand and every video borrows its motion grammar from here. **Rules** live in
`standards/formats/<format>.md`. This folder holds the **evidence**: real reference videos broken down shot
by shot, and one card per pattern with a quality bar and the best stills. Agents look at these stills
before building and compare their renders against them in the critique loop (`standards/core/qa.md` §2).

```
references/
  index.json               generated — per-video stats, per-pattern exemplars, new-pattern candidates
  patterns/<id>.md         one card per pattern ID in standards/formats/long-form.md (A1…E2 + kit names)
  videos/<slug>/
    source.json            what the video is (file name only — the media stays on the shared drive)
    shots.json             contiguous shots covering 0…duration, each draft → reviewed
    stills/*.jpg           960 px stills of graphic and section shots (committed)
    work/                  contact sheets and scratch (gitignored)
```

## Add a reference video (stackable — repeat for every new video)

1. **Ingest:**
   ```bash
   python3 tools/ref_ingest.py "<video file>" --slug <kebab-slug> --title "<YouTube title>" \
     --brand "<whose channel>" --made-by "<who animated it>" --ground dark|light|mixed [--url <youtube url>]
   ```
   It writes a draft `shots.json`: one shot per hard cut, stills per shot and contact sheets in `work/`.
2. **Analyse** every shot (below). Draft shots block `ref_index.py --check`.
3. **Prune and index:** `python3 tools/ref_index.py --prune`. This deletes stills of face shots, regenerates
   `index.json` and every card's evidence block, and creates a card for any new catalogue ID.
4. **Quality bars:** update the bar of every pattern the video touched (below).
5. **Check and commit:** `python3 tools/ref_index.py --check` must print `OK`. Commit `references/`
   (stills included). Stay within the 10 MB stills budget per video.

## Analyse

Start from `work/timeline-NN.jpg` (2 fps, 10 per row = 5 s per row; `work/timeline.txt` lists the span of each
sheet). They show what the cut detector misses: scale or zoom transitions (the CTA dive), beats inside one
canvas, punch-ins. Then work through `work/contact-NN.jpg` (with `work/contact.txt` mapping tiles to shot ids)
and each shot's stills.

**Fix the shot list first** with `python3 tools/ref_shots.py <slug> split|merge|stills …` (it keeps shots
contiguous and re-extracts stills) before filling in fields. A long graphic shot that chains patterns: split it
at the beat where the pattern changes when that beat is ≥ 1.5 s; otherwise tag the dominant pattern and name the
other in `notes`. When motion matters (camera legs, word builds, holds), cut a 10 fps strip from the source video
into `work/`:

```bash
ffmpeg -ss <t_in> -to <t_out> -i "<video>" -vf fps=10,scale=480:-2 "references/videos/<slug>/work/<id>-%03d.jpg"
```

For a compact overview use a tiled strip, `fps=10,scale=320:-2,tile=10x<rows>`: one row per second (this ffmpeg
has no `drawtext`, so count tiles instead of reading timestamps). Measure `type_px` on a full-resolution frame,
not on the 960 px stills: `ffmpeg -ss <t> -i "<video>" -frames:v 1 -vf scale=1920:1080 work/<id>-full.png`.

For every shot, set `"status": "reviewed"` and fill in:

| Field | What to write |
|---|---|
| `kind` | `face` (talking head, punch-ins included), `graphic` (full-frame or over-footage animation), `section` (recorded board/deck), `other` (b-roll, screen recording without graphics) |
| `pattern` | graphic/section only: an ID from `standards/formats/long-form.md` (A1…E2, or a kit name such as `title`, `lower-third`, `roadmap`). Nothing fits → `new:<kebab-name>` (it shows up under `candidates` in `index.json`; promote it by adding a catalogue row). |
| `placement` | `full-frame` or `over-footage` |
| `layout` | `{"type_px": <cap height of the largest text, in px at 1080 p; 0 = no text>, "fill": "sparse"\|"balanced"\|"dense", "layers": <depth layers: ground, backdrop, cards, marks…>}` |
| `motion` | `{"entrance": "<how it arrives>", "camera": "<legs and stops, or none>", "word_rate_s": <s per word or null>, "hold_s": <still hold before the cut or null>}` |
| `colours` | the 1–4 dominant non-neutral colours as `#RRGGBB` |
| `marks` | hand-drawn marks used: `underline`, `scribble`, `arrow`, `circle`, `strike`, `highlight-block`, `check`, `cross`, `script-word` |
| `quality` | one or two sentences: **why this looks expensive** — the specific craft (depth, real UI, the micro-detail, timing), not a description of the content |
| `notes` | anything else: what is said, a variant, a bug |
| `exemplar` | `true` on the best 1–2 shots of a pattern in this video (pinned first on the card) |

Face shots: `kind` only, with `pattern`, `placement`, `layout` and `motion` all `null`. Other shots need only `kind` (pattern `null`). Shots must stay contiguous: each `t_in` equals the previous `t_out` (`ref_shots.py` keeps it so).

Take the grammar, never the content: logos, faces and copy in the stills are evidence, not assets.

## Quality bar

The top of each card (`patterns/<id>.md`, above the generated block) is hand-written and survives
regeneration. Write **4–8 checkable bullets** a reviewer can verify on a still or a 10 fps strip, drawn
from what the exemplars share. For example:

- Focus card ≥ 40 % of frame width; the backdrop is the same screenshot blurred and dimmed to ≈ 35 %.
- Headline cap height ≥ 70 px at 1080; never more than 2 lines.
- Highlight lands only after the card has settled (≥ 0.3 s), sweeping left → right in ≈ 0.3 s.

Where a bullet contradicts the rule row in `standards/formats/long-form.md`, change the rule in the same
commit (promotion rule) and say so in the commit message.

## Use it when building a video

- **Storyboard:** every row's `type` cites a pattern ID (QA check 11). Before building a pattern, open
  its card and look at the stills.
- **Critique loop:** `python3 tools/ref_board.py videos/<slug> --render <reel.mp4>` puts each full-frame
  graphic above reference stills of its pattern. For over-footage layouts, use
  `--pattern <ID> --still <frame.png> -o <board.jpg>`. Score Craft and On-brand against the card.
