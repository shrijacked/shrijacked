"""Render dark_mode.svg and light_mode.svg (Andrew6rant-style neofetch card) from
portrait.txt + facts.json + stats.json. Pure stdlib. Run: python build_svg.py"""
import base64, json, os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
FS, LH, CW = 15, 20, 9.0
PFS, PLH, PCW = 7, 7.8, 4.2   # portrait font size, line height, advance          # font size, line height, monospace advance (0.6em)
PAD, GAP, RW = 20, 26, 62         # padding, column gap, readout width in chars

THEMES = {
    "dark":  dict(bg="#161b22", text="#c9d1d9", key="#ffa657", value="#a5d6ff", cc="#616e7f", ph="#8b949e", prompt="#3fb950", border="#30363d"),
    "light": dict(bg="#f6f8fa", text="#24292f", key="#953800", value="#0a3069", cc="#c2cfde", ph="#6e7781", prompt="#1a7f37", border="#d0d7de"),
}

def load(name, default=None):
    p = os.path.join(HERE, name)
    if not os.path.exists(p):
        return default
    with open(p, encoding="utf-8") as f:
        return json.load(f) if name.endswith(".json") else f.read()

def key_spans(parts):
    out = []
    for i, k in enumerate(parts):
        if i: out.append(".")
        out.append(f'<tspan class="key">{escape(k)}</tspan>')
    return "".join(out), len(".".join(parts))

def value_span(v, vid=None):
    cls = "ph" if v.startswith("[placeholder") else "value"
    idattr = f' id="{vid}"' if vid else ""
    return f'<tspan class="{cls}"{idattr}>{escape(v)}</tspan>'

def dots(n):
    return f'<tspan class="cc">{" " + "." * (n - 2) + " " if n > 2 else " " * n}</tspan>'

def row_line(parts, val, width):
    ks, kl = key_spans(parts)
    n = max(2, width - 2 - kl - 1 - len(val))
    return f'<tspan class="cc">. </tspan>{ks}:{dots(n)}{value_span(val)}', 2 + kl + 1 + n + len(val)

def build(theme, portrait, facts, stats):
    c = THEMES[theme]
    fill = lambda s: s.format(**stats) if "{" in s else s
    lines = []  # list of svg tspan bodies for the readout
    head = f'{facts["user"]}@{facts["host"]}'
    lines.append(f'<tspan class="key">{facts["user"]}</tspan>@<tspan class="key">{facts["host"]}</tspan> ' + "—" * (RW - len(head) - 1))
    for si, sec in enumerate(facts["sections"]):
        if sec["title"]:
            lines.append("")
            lines.append(f'- {escape(sec["title"])} ' + "—" * (RW - len(sec["title"]) - 3))
        for r in sec["rows"]:
            if r is None:
                lines.append('<tspan class="cc">. </tspan>')
            elif isinstance(r, dict):
                (k1, v1, _), (k2, v2, _) = r["pair"]
                half = 34
                a, _ = row_line(k1, fill(v1), half)
                b, _ = row_line(k2, fill(v2), RW - half - 1)  # 2 chars of ". " are dropped, " | " adds 3
                b = b.replace('<tspan class="cc">. </tspan>', "", 1)
                lines.append(a + '<tspan class="cc"> | </tspan>' + b)
            else:
                body, _ = row_line(r[0], fill(r[1]), RW)
                lines.append(body)
    lines.append("")
    lines.append(f'<tspan class="prompt">{head}:~$</tspan> <tspan class="cursor">█</tspan>')

    art = portrait.rstrip("\n").split("\n")
    pw = max(len(l) for l in art)
    nrows = max(len(lines), int(len(art) * PLH / LH + 0.999))
    ph_ = len(art) * PLH
    rx = PAD + pw * PCW + GAP
    W = int(rx + RW * CW + PAD)
    H = int(PAD + nrows * LH + PAD - 4)
    top = (nrows * LH - len(art) * PLH) / 2       # vertically centre the portrait
    font = base64.b64encode(open(os.path.join(HERE, "fonts/JetBrainsMono-subset.woff2"), "rb").read()).decode()
    o = [f'<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="JBM, Consolas, Menlo, monospace" font-size="{FS}px">',
         f'<title>{head} — Shrijak Kumar\'s GitHub profile</title>',
         "<style>",
         f"@font-face{{font-family:'JBM';src:url(data:font/woff2;base64,{font}) format('woff2');}}",
         f".key{{fill:{c['key']}}} .value{{fill:{c['value']}}} .cc{{fill:{c['cc']}}} .ph{{fill:{c['ph']};font-style:italic}} .prompt{{fill:{c['prompt']}}}",
         f".ascii{{fill:{c['text']}}} text,tspan{{white-space:pre}}",
         "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}} .cursor{fill:" + c['text'] + ";animation:blink 1.1s step-end infinite}",
         "@media (prefers-reduced-motion:reduce){.cursor{animation:none}}",
         "</style>",
         f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="15" fill="{c["bg"]}" stroke="{c["border"]}"/>',
         f'<text class="ascii" x="{PAD}" y="{PAD + 15}" font-size="{PFS}px">']
    for i, l in enumerate(art):
        o.append(f'<tspan x="{PAD}" y="{PAD + 6 + top + i * PLH:.1f}" textLength="{len(l) * PCW:.1f}">{escape(l)}</tspan>')
    o.append("</text>")
    o.append(f'<text x="{rx:.0f}" y="{PAD + 15}" fill="{c["text"]}">')
    for i, l in enumerate(lines):
        o.append(f'<tspan x="{rx:.0f}" y="{PAD + 15 + i * LH}">{l}</tspan>')
    o.append("</text></svg>")
    return "\n".join(o)

if __name__ == "__main__":
    facts, stats = load("facts.json"), load("stats.json", {})
    for t in THEMES:
        portrait = load(f"portrait_{t}.txt") or load("portrait.txt") or load("portrait_placeholder.txt")
        with open(os.path.join(HERE, f"{t}_mode.svg"), "w", encoding="utf-8") as f:
            f.write(build(t, portrait, facts, stats))
    print("wrote dark_mode.svg, light_mode.svg")
