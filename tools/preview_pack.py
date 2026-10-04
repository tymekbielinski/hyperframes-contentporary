"""Generate the preview pack for human sign-off (standards/core/qa.md §3) into renders/preview/.

Contents (index.html links everything): the final critique scores (any graphic still below 8 first),
a contact sheet of every graphic (one settled frame each), a draft of the hook plus one body scene
(long-form; a Short links its whole render), the density timeline, the exceptions list, and the
automated gate's result when renders/qa-report.json exists. renders/ is never committed.

Usage: python3 tools/preview_pack.py videos/<slug> [--render renders/qa-draft.mp4] [--overlays renders/overlays]
"""
import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

import cadence_scan
import media
import project as pj

DIMENSIONS = ["smooth", "on-brand", "readable", "synced", "purposeful", "craft"]
PASS_SCORE = 8
SETTLED_LEAD = 0.35   # the settled frame: 0.35 s before a scene's cut (inside the 0.3–1 s hold)
SHORTS_EXIT = 0.36


def parse_critique(text: str) -> dict:
    """The last '## Round N' table of critique.md → {"round": N | None, "rows": [...]}, low scorers first."""
    rounds = list(re.finditer(r"^## Round (\d+)\s*$", text, re.M))
    if not rounds:
        return {"round": None, "rows": []}
    last = rounds[-1]
    rows = []
    for line in text[last.end():].splitlines():
        if line.startswith("## "):
            break
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8 or cells[0] in ("graphic", "") or set(cells[0]) <= {"-", ":"}:
            continue
        scores = {}
        for dim, cell in zip(DIMENSIONS, cells[1:7]):
            scores[dim] = int(cell) if re.fullmatch(r"\d{1,2}", cell) else None
        low = [d for d, s in scores.items() if s is None or s < PASS_SCORE]
        rows.append({"graphic": cells[0], "scores": scores, "notes": cells[7], "low": low})
    rows.sort(key=lambda r: (not r["low"], ))
    return {"round": int(last.group(1)), "rows": rows}


def graphics(project, fmt, rows) -> list:
    """Every graphic in the render: {"label", "timeline" (s on the edit), "start", "end" (s in the render)}."""
    full = [r for r in rows if r["placement"] == "full-frame"]
    if fmt == "shorts":
        return [{"label": f"{r['type']} {r['t_in']:g}–{r['t_out']:g} s", "timeline": r["t_in"], "start": r["t_in"],
                 "end": r["t_out"] - SHORTS_EXIT} for r in full]
    slots = pj.composition_slots(project)
    out = []
    for i, s in enumerate(slots):
        row = full[i] if len(full) == len(slots) else None
        out.append({"label": s["id"] + (f" · {row['type']}" if row else ""), "timeline": row["t_in"] if row else None,
                    "start": s["start"], "end": s["start"] + s["dur"]})
    return out


def density_svg(report, width=960) -> str:
    dur, h = report["duration"], 46
    x = lambda t: round(t / dur * width, 1)
    bars = [f'<rect x="0" y="12" width="{width}" height="22" fill="#2a2a2a"/>']
    for a, b in report.get("screen_share", []):
        bars.append(f'<rect x="{x(a)}" y="12" width="{x(b) - x(a)}" height="22" fill="#555"><title>screen share {a:g}–{b:g} s</title></rect>')
    for a, b in report["over_footage"]:
        bars.append(f'<rect x="{x(a)}" y="24" width="{max(1, x(b) - x(a))}" height="10" fill="#8fb3ff"><title>over-footage {a:g}–{b:g} s</title></rect>')
    for a, b in report["full_frame"]:
        bars.append(f'<rect x="{x(a)}" y="12" width="{max(1, x(b) - x(a))}" height="22" fill="#f26666"><title>full-frame {a:g}–{b:g} s</title></rect>')
    if report["format"] == "long-form":
        he = min(report["hook_end"], dur)
        bars.append(f'<line x1="{x(he)}" y1="4" x2="{x(he)}" y2="42" stroke="#fff" stroke-dasharray="3 3"/>'
                    f'<text x="{x(he) + 4}" y="10" fill="#ccc" font-size="10">hook_end {he:g} s</text>')
    return f'<svg viewBox="0 0 {width} {h}" width="100%" role="img" aria-label="density timeline">{"".join(bars)}</svg>'


def _cut(src, start, end, out):
    media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-ss", f"{start:.3f}", "-i", str(src),
               "-t", f"{max(0.04, end - start):.3f}", "-an", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)])


def _frame(src, t, out_png, g, fmt, background=None):
    """Extract one tile; past the clip end (or any MediaError) write a solid placeholder tile and mark the
    graphic `missing` so the pack names it instead of silently dropping it."""
    try:
        media.extract_frame(src, t, out_png, background=background)
    except media.MediaError as e:
        size = "480x854" if fmt == "shorts" else "480x270"
        media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-f", "lavfi", "-i", f"color=c=0x802020:s={size}",
                   "-frames:v", "1", "-pix_fmt", "rgb24", str(out_png)])
        g["missing"] = str(e)


def _read_qa(path):
    """The gate's report: None (absent = qa not run or crashed, never a pass), a dict, or {"error": ...}."""
    if not path.is_file():
        return None
    try:
        qa = json.loads(path.read_text())
        if not isinstance(qa, dict) or not isinstance(qa.get("checks"), list):
            raise ValueError("no checks list")
        return qa
    except ValueError as e:
        return {"error": f"renders/qa-report.json is unreadable ({e}) — re-run python3 tools/qa.py"}


def build(project, render, overlays=None, out_dir=None) -> Path:
    project = Path(project)
    if not Path(render).is_file():
        raise media.MediaError(f"{render} not found — run python3 tools/qa.py (it renders qa-draft.mp4) or pass --render")
    brief = pj.read_brief(project)
    fmt = brief.get("format")
    if fmt not in pj.FORMATS:
        raise pj.ProjectError(f"BRIEF format must be long-form or shorts, got {fmt!r}")
    rows = pj.read_storyboard(project)
    out = Path(out_dir) if out_dir else project / "renders" / "preview"
    if out.exists():
        shutil.rmtree(out)
    (out / "frames").mkdir(parents=True)

    items = graphics(project, fmt, rows)
    for i, g in enumerate(items, 1):
        g["frame"] = f"frames/{i:03d}.png"
        _frame(render, max(g["start"], g["end"] - SETTLED_LEAD), out / g["frame"], g, fmt)
    for j, mov in enumerate(sorted(Path(overlays).glob("*.mov")) if overlays else [], len(items) + 1):
        info = media.video_info(mov)
        g = {"label": f"over-footage · {mov.stem}", "timeline": None, "frame": f"frames/{j:03d}.png"}
        _frame(mov, max(0.0, info["duration"] - SETTLED_LEAD), out / g["frame"], g, fmt, background="0x3a3a3a")
        items.append(g)
    if items:
        cols = 4
        media.run([media.tool("ffmpeg"), "-v", "error", "-nostdin", "-y", "-framerate", "1", "-i", str(out / "frames" / "%03d.png"),
                   "-vf", f"scale=480:-2,tile={cols}x{-(-len(items) // cols)}:padding=8:margin=8:color=0x202020",
                   "-frames:v", "1", str(out / "contact-sheet.png")])

    drafts = []
    if fmt == "long-form" and items and items[0].get("start") is not None:
        hook_end = pj.hook_end(brief)
        scenes = [g for g in items if "start" in g]
        hook = [g for g in scenes if g["timeline"] is not None and g["timeline"] < hook_end] or scenes[:1]
        body = [g for g in scenes if g["timeline"] is not None and g["timeline"] >= hook_end][:1]
        _cut(render, hook[0]["start"], hook[-1]["end"], out / "hook.mp4")
        drafts.append(("hook.mp4", f"hook: {len(hook)} scene(s)"))
        if body:
            _cut(render, body[0]["start"], body[0]["end"], out / "body.mp4")
            drafts.append(("body.mp4", f"body: {body[0]['label']}"))
    elif fmt == "shorts":
        shutil.copyfile(render, out / "short.mp4")
        drafts.append(("short.mp4", "the whole Short"))

    try:
        density = cadence_scan.report(project)
    except (pj.ProjectError, ValueError) as e:
        density = {"error": str(e)}
    crit_path = project / "critique.md"
    critique = parse_critique(crit_path.read_text()) if crit_path.is_file() else {"round": None, "rows": []}
    qa_path = project / "renders" / "qa-report.json"
    qa = _read_qa(qa_path)
    (out / "index.html").write_text(render_html(project.name, fmt, items, drafts, density, critique, qa,
                                                brief.get("exceptions") or []))
    return out / "index.html"


def render_html(slug, fmt, items, drafts, density, critique, qa, exceptions) -> str:
    e = html.escape
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>Preview pack — {e(slug)}</title>",
             "<style>body{font:15px/1.5 system-ui,sans-serif;background:#111;color:#eee;margin:24px;max-width:1100px}"
             "h1,h2{font-weight:600}table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #333;padding:4px 8px;text-align:left}"
             ".low{color:#f88;font-weight:600}.pass{color:#8d8}.fail{color:#f88}figure{display:inline-block;margin:6px;width:250px;vertical-align:top}"
             "figure img{width:100%;border:1px solid #333}figcaption{font-size:12px;color:#aaa}a{color:#9cf}</style></head><body>",
             f"<h1>Preview pack — {e(slug)} <small>({e(fmt)})</small></h1>"]
    # 1. critique scores, low first
    parts.append("<h2>Critique scores" + (f" — round {critique['round']}" if critique["round"] else "") + "</h2>")
    if critique["rows"]:
        low = [r for r in critique["rows"] if r["low"]]
        parts.append(f"<p class='{'low' if low else 'pass'}'>{len(low)} graphic(s) below {PASS_SCORE} on some dimension.</p>")
        parts.append("<table><tr><th>graphic</th>" + "".join(f"<th>{d}</th>" for d in DIMENSIONS) + "<th>notes</th></tr>")
        for r in critique["rows"]:
            cells = "".join(f"<td class='{'low' if d in r['low'] else ''}'>{'—' if r['scores'][d] is None else r['scores'][d]}</td>" for d in DIMENSIONS)
            parts.append(f"<tr><td class='{'low' if r['low'] else ''}'>{e(r['graphic'])}</td>{cells}<td>{e(r['notes'])}</td></tr>")
        parts.append("</table>")
    else:
        parts.append("<p class='low'>No critique scores recorded yet — run the critique loop (standards/core/qa.md §2) into critique.md.</p>")
    # 2. automated gate
    if qa and "error" in qa:
        parts.append(f"<h2>Automated gate — <span class='fail'>UNKNOWN</span></h2><p class='fail'>{e(qa['error'])}</p>")
    elif qa:
        ok = bool(qa.get("ok"))
        parts.append(f"<h2>Automated gate — <span class='{'pass' if ok else 'fail'}'>{'PASS' if ok else 'FAIL'}</span></h2><table>")
        for c in qa["checks"]:
            parts.append(f"<tr><td>{c.get('n')}</td><td>{e(str(c.get('name')))}</td><td class='{'pass' if c.get('status') in ('PASS', 'WAIVED') else 'fail'}'>{e(str(c.get('status')))}</td>"
                         f"<td>{'<br>'.join(e(str(f)) for f in c.get('findings', [])[:5])}</td></tr>")
        parts.append("</table>")
        if qa.get("warnings"):
            parts.append("<p class='low'>Gate warnings:</p><ul>" + "".join(f"<li class='low'>{e(str(w))}</li>" for w in qa["warnings"]) + "</ul>")
    else:
        parts.append("<h2>Automated gate — <span class='fail'>NOT RUN</span></h2><p class='low'>No renders/qa-report.json — qa was not run or crashed; this is NOT a pass. Run python3 tools/qa.py first.</p>")
    # 3. drafts + contact sheet
    parts.append("<h2>Drafts</h2><ul>" + "".join(f"<li><a href='{f}'>{f}</a> — {e(d)}</li>" for f, d in drafts) + "</ul>")
    parts.append(f"<h2>Every graphic ({len(items)})</h2>")
    if items:
        parts.append("<p><a href='contact-sheet.png'>contact-sheet.png</a></p>")
    for g in items:
        when = f" · timeline {g['timeline']:.1f} s" if g.get("timeline") is not None else ""
        miss = f"<br><span class='fail'>FRAME MISSING: {e(g['missing'])}</span>" if g.get("missing") else ""
        parts.append(f"<figure><img src='{g['frame']}' alt=''><figcaption>{e(g['label'])}{when}{miss}</figcaption></figure>")
    # 4. density
    parts.append("<h2>Density</h2>")
    if "error" in density:
        parts.append(f"<p class='low'>{e(density['error'])}</p>")
    else:
        parts.append(density_svg(density))
        if density.get("reference"):
            parts.append(f"<p>face reference: {e(str(density['reference']))}</p>")
        parts.append("".join(f"<p class='low'>WARN — {e(str(w))}</p>" for w in density.get("warnings", [])))
        parts.append("<ul>" + "".join(f"<li class='{'pass' if r['ok'] else 'fail'}'>{'PASS' if r['ok'] else 'FAIL'} — {e(r['name'])}: {e(r['detail'])}</li>"
                                      for r in density["results"]) + "</ul>")
    # 5. exceptions
    parts.append("<h2>Exceptions</h2>" + ("<ul>" + "".join(f"<li>{e(str(x))}</li>" for x in exceptions) + "</ul>" if exceptions else "<p>None declared.</p>"))
    parts.append("</body></html>\n")
    return "\n".join(parts)


def main(argv) -> int:
    ap = argparse.ArgumentParser(prog="python3 tools/preview_pack.py")
    ap.add_argument("project")
    ap.add_argument("--render")
    ap.add_argument("--overlays")
    a = ap.parse_args(argv[1:])
    render = Path(a.render) if a.render else Path(a.project) / "renders" / "qa-draft.mp4"
    try:
        index = build(a.project, render, a.overlays)
    except (pj.ProjectError, media.MediaError) as e:
        print(e)
        return 1
    print(f"preview pack → {index}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
