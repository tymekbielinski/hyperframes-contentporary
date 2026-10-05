# Animation Reference Library — design

**Date:** 2026-10-05 · **Status:** approved by Tymek in chat (scope, stackability, stills in Git)

## Problem

The first long-form test build (`videos/startup-youtube-lessons-intro`, 2026-10-05) passed the automated
gate and still looked basic: flat frames, tiny type and no depth compared with Tymek's editor's
After Effects work. The build agent only had text descriptions of the reference grammar
(`standards/formats/long-form.md`, `docs/research/2026-10-03-custom-animation-catalogue.md`). The frames
behind that research were left in a session scratchpad and are gone, so no agent can *see* what
"good" looks like, and the critique loop scores against an imagined bar.

## Goal

A universal, brand-agnostic reference library committed to Git. It has three parts:

1. **Per-video breakdowns.** Every reference video becomes a timed shot log with stills, and each
   graphic shot is tagged with a catalogue pattern ID plus measured layout and motion values.
2. **Pattern cards.** There is one card per catalogue pattern. It holds a hand-written quality bar and
   a generated evidence block: exemplar stills from every video that uses the pattern, plus measured
   ranges.
3. **Pipeline hooks.** The storyboard cites pattern IDs, the critique loop compares rendered frames side
   by side with reference stills, and the QA gate checks the citations.

**Stackable.** Adding a video means running one ingest command, doing the analyst review and running
one index command. Nothing is hand-maintained per video beyond the analysis, and evidence regenerates
from all videos.

## Decisions

- **Corpus now:** the 7 After Effects videos already analysed in the research doc, all in `~/Downloads`
  (media stays out of Git; `source.json` records the file name only).
- **Stills in Git:** Tymek approved about 20–40 MB in total. They are JPEG at 960 px wide (the
  installed ffmpeg has no WebP encoder) and only graphic and section shots keep stills after review.
  Per-video budget: 10 MB, enforced by `tools/ref_index.py --check`.
- **Rules stay in `standards/`.** `standards/formats/long-form.md` remains the rule (catalogue IDs, kit
  table). `references/` is evidence plus quality bars, so precedence `core → formats → brands → BRIEF`
  is unchanged. Pattern IDs are read from long-form.md, so a new catalogue row automatically gets a card.
- **New patterns:** an analyst may tag a shot `new:<slug>`. The index lists these as candidates, and
  promoting one means adding a catalogue row to long-form.md (the promotion rule).
- **Section formats get IDs** E1 (board walkthrough + face PiP) and E2 (slide deck + round face-cam) in
  long-form.md, matching the research doc.
- **Shorts:** the schema has `format`, so Shorts references can be ingested later. QA check 11 passes
  Shorts with a note until a Shorts catalogue with IDs exists.

## Layout

```
references/
  README.md                       how to add a video; the analyst brief; schema
  index.json                      generated: per-video stats, per-pattern exemplars, candidates
  patterns/<id>.md                one card per registry ID (A1…E2, title, subtitle, lower-third, …)
  videos/<slug>/source.json       title, url, format, ground, made_by, brand, duration, fps, size, file
  videos/<slug>/shots.json        contiguous shots covering 0…duration, draft → reviewed
  videos/<slug>/stills/*.jpg      stills of graphic / section shots
  videos/<slug>/work/             gitignored: contact sheets and analysis scratch
```

## Tools

| Tool | Does |
|---|---|
| `tools/refs.py` | Library module: pattern registry from long-form.md, load + validate videos, exemplar lookup, storyboard `type` → IDs |
| `tools/ref_ingest.py` | Video → draft shot log (ffmpeg hard cuts), stills and contact sheets |
| `tools/ref_index.py` | Validate everything; write `index.json`; regenerate card evidence blocks; create stub cards; `--prune` stills of face shots; `--check` for CI |
| `tools/ref_board.py` | Critique boards: candidate frames (mid, settled) above reference stills of the row's pattern |
| `tools/qa.py` check 11 | Long-form: every storyboard row cites a known kit name or catalogue ID; unknown IDs fail; patterns without exemplars warn |

## Analyst review (agent work, per video)

The analyst looks at the stills (and the source video around transitions) and fills in every shot:

- `kind`: face, graphic, section or other
- `pattern` and `placement`
- `layout`: largest text height in px at 1080, fill, layers
- `motion`: entrance, camera, word rate, hold
- `colours`, `marks` and `notes`
- `quality`: one or two sentences on why the shot looks expensive

Shots may be merged or split, and an `exemplar: true` flag pins the best shot of a pattern. The
analyst then writes or updates the quality bar of every pattern card the video touched.

## Out of scope

- Rebuilding `videos/startup-youtube-lessons-intro` (done after the library exists).
- Kit improvements found during analysis; these are promoted separately.
- Shorts catalogue IDs.
