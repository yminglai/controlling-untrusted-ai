#!/usr/bin/env python3
"""Contrast regression test named in design/DESIGN.md section 9.

Reads site/assets/css/tokens.css, resolves the custom properties of the light (:root)
and dark ([data-theme="dark"]) themes, including var() references and
color-mix(in srgb, ...), and recomputes the role pairs. Fails under 4.5:1 for text
and 3:1 for marks, control borders and focus rings. Pure standard library.

    python3 pipeline/tests/test_contrast.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOKENS = ROOT / "site" / "assets" / "css" / "tokens.css"

HUES = ["coral", "terracotta", "blue", "amber", "teal", "periwinkle", "forest", "purple", "gold", "sky", "pink", "sand", "slate", "gray"]
MARK_HUES = ["coral", "terracotta", "blue", "amber", "teal", "periwinkle", "forest", "purple", "gold", "sand", "slate", "gray"]


def parse_blocks(css: str) -> tuple[dict, dict]:
    def block(selector: str) -> dict:
        m = re.search(re.escape(selector) + r"\s*\{(.*?)\n\}", css, re.S)
        assert m, f"block {selector!r} not found"
        body = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S)
        out = {}
        for decl in re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", body):
            out[decl[0]] = decl[1].strip()
        return out
    return block(":root"), block('[data-theme="dark"]')


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


NAMED = {"white": (255, 255, 255), "black": (0, 0, 0)}


def resolve(value: str, vars_: dict, depth: int = 0) -> tuple[float, float, float]:
    """Resolve a colour expression to an sRGB triple (0-255 floats)."""
    assert depth < 20, f"cyclic value {value!r}"
    v = value.strip()
    m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)
    if m:
        return resolve(vars_[m.group(1)], vars_, depth + 1)
    if v in NAMED:
        return NAMED[v]
    if v.startswith("#"):
        return hex_to_rgb(v)
    m = re.fullmatch(r"rgb\(\s*(\d+)\s+(\d+)\s+(\d+)\s*(?:/\s*[\d.]+)?\)", v)
    if m:
        return tuple(int(x) for x in m.groups())  # type: ignore[return-value]
    m = re.fullmatch(r"color-mix\(in srgb,\s*(.+?)\s+([\d.]+%|var\(--[a-z0-9-]+\)),\s*(.+?)(?:\s+([\d.]+%))?\)", v)
    if m:
        a, pa, b, pb = m.groups()
        pa_v = pa if pa.endswith("%") else resolve_pct(vars_[pa[4:-1]], vars_)
        p = float(pa_v.rstrip("%")) / 100
        q = float(pb.rstrip("%")) / 100 if pb else 1 - p
        ca, cb = resolve(a, vars_, depth + 1), resolve(b, vars_, depth + 1)
        return tuple(ca[i] * p + cb[i] * q for i in range(3))  # type: ignore[return-value]
    raise ValueError(f"cannot resolve {value!r}")


def resolve_pct(value: str, vars_: dict) -> str:
    v = value.strip()
    m = re.fullmatch(r"var\((--[a-z0-9-]+)\)", v)
    return resolve_pct(vars_[m.group(1)], vars_) if m else v


def luminance(rgb) -> float:
    def ch(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(x) for x in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def theme_vars(root: dict, dark: dict | None) -> dict:
    v = dict(root)
    if dark:
        v.update(dark)
    return v


def main() -> int:
    css = TOKENS.read_text(encoding="utf-8")
    root, dark = parse_blocks(css)
    failures: list[str] = []
    rows: list[str] = []

    def check(name: str, fg, bg, minimum: float, theme: str):
        r = ratio(fg, bg)
        rows.append(f"{theme:5} {name:58} {r:5.2f}  (min {minimum})")
        if r < minimum - 1e-9:
            failures.append(f"{theme}: {name} = {r:.2f} < {minimum}")

    for theme, vars_ in (("light", theme_vars(root, None)), ("dark", theme_vars(root, dark))):
        R = lambda expr: resolve(expr, vars_)  # noqa: E731
        bg, panel, fg, muted = R("var(--bg)"), R("var(--bg-panel)"), R("var(--fg)"), R("var(--fg-muted)")
        focus, control, rule_strong = R("var(--focus)"), R("var(--control-border)"), R("var(--rule-strong)")
        tint = float(resolve_pct(vars_["--tint"], vars_).rstrip("%")) / 100

        check("--fg on --bg", fg, bg, 4.5, theme)
        check("--fg on --bg-panel", fg, panel, 4.5, theme)
        check("--fg-muted on --bg (13 px meta, zero-count chips)", muted, bg, 4.5, theme)
        check("--fg-muted on --bg-panel", muted, panel, 4.5, theme)
        check("--bg text on --fg fill (Cited badge, active chip)", bg, fg, 4.5, theme)
        check("--control-border on --bg (inputs, buttons, plain chips)", control, bg, 3.0, theme)
        check("--control-border on --bg-panel", control, panel, 3.0, theme)
        check("--focus ring on --bg", focus, bg, 3.0, theme)
        check("--bg ring on --fg fill (checked segment, focused)", bg, fg, 3.0, theme)
        check("--rule-strong hairline on --bg", rule_strong, bg, 1.0, theme)  # decorative, reported only
        for hue in HUES:
            c = R(f"var(--{hue})")
            tinted = tuple(c[i] * tint + bg[i] * (1 - tint) for i in range(3))
            check(f"--fg on --c-tint ({hue})", fg, tinted, 4.5, theme)
        ink = R("var(--ink)")
        for hue in MARK_HUES:
            c = R(f"var(--{hue})")
            if theme == "light":
                outline = tuple(c[i] * 0.7 + ink[i] * 0.3 for i in range(3))
                check(f"mark outline (--c 70% ink) on --bg ({hue})", outline, bg, 3.0, theme)
                check(f"--c-border (--c 70% ink) on --bg ({hue})", outline, bg, 3.0, theme)
            else:
                check(f"raw hue mark on --bg ({hue})", c, bg, 3.0, theme)
                lifted = tuple(c[i] * 0.55 + 255 * 0.45 for i in range(3))
                check(f"panel outline (--c 55% white) on --bg-panel ({hue})", lifted, panel, 3.0, theme)
        # live indicator labels: --c-text on --bg only (forest 60 %, gold 50 %, coral 60 %)
        for hue, mix in (("forest", 0.6), ("gold", 0.5), ("coral", 0.6)):
            c = R(f"var(--{hue})")
            text = (tuple(c[i] * mix + ink[i] * (1 - mix) for i in range(3)) if theme == "light"
                    else tuple(c[i] * 0.65 + 255 * 0.35 for i in range(3)))
            check(f"--c-text live label ({hue}) on --bg", text, bg, 4.5, theme)

    for r in rows:
        print(r)
    if failures:
        print("\nFAILED:")
        for f in failures:
            print(" ", f)
        return 1
    print(f"\nOK: {len(rows)} pairs checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
