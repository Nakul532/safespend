"""WCAG 2.x contrast ratios for the GAME_DESIGN.md palette. Writes contrast.json next to the design files."""
import json
from pathlib import Path


def lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


L = {"paper": "#F4F1EA", "surface": "#FFFFFF", "hairline": "#E3DED3", "ink": "#151A22", "ink-2": "#5B6270",
     "indigo": "#3D4FC9", "indigo-hover": "#2F3FAE", "approved": "#0E7C5A", "held": "#B7791F", "blocked": "#B33A2E"}
D = {"night": "#12161F", "surface": "#1B2130", "hairline": "#2A3243", "text": "#ECEEF2", "text-2": "#A4ACBA",
     "accent": "#8B98F5", "approved": "#3FBF8F", "held": "#E0A84A", "blocked": "#E06A5C"}
pairs = []
for fg in ("ink", "ink-2", "indigo", "indigo-hover", "approved", "held", "blocked"):
    for bg in ("paper", "surface"):
        pairs.append(("light", f"{fg} text on {bg}", L[fg], L[bg]))
for fill in ("indigo", "indigo-hover", "approved", "held", "blocked"):
    pairs.append(("light", f"white text on {fill} fill", "#FFFFFF", L[fill]))
pairs.append(("light", "hairline on surface (decorative border)", L["hairline"], L["surface"]))
for fg in ("text", "text-2", "accent", "approved", "held", "blocked"):
    for bg in ("night", "surface"):
        pairs.append(("dark", f"{fg} text on {bg}", D[fg], D[bg]))
pairs.append(("dark", "night text on accent fill", D["night"], D["accent"]))
out = [{"theme": t, "pair": n, "fg": f, "bg": b, "ratio": ratio(f, b),
        "body_AA": ratio(f, b) >= 4.5, "large_AA": ratio(f, b) >= 3.0} for t, n, f, b in pairs]
Path(__file__).with_name("contrast.json").write_text(json.dumps(out, indent=1))
for o in out:
    print(f"{o['theme']:5} {o['pair']:42} {o['ratio']:5}  body {'PASS' if o['body_AA'] else 'FAIL'}  large {'PASS' if o['large_AA'] else 'FAIL'}")
