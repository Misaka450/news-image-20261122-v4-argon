import os
import sys
import math
import hashlib
import subprocess
from PIL import Image, ImageFont

# Exact system font files matched by fontconfig (used by rsvg-convert)
FONT_PATHS = {
    "serif_reg": "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-regular.otf",
    "serif_bold": "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-bold.otf",
    "serif_italic": "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-italic.otf",
    "sans_reg": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "sans_bold": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "cond_bold": "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf",
}

_FONT_CACHE = {}

def get_font(key: str, size_px: float) -> ImageFont.FreeTypeFont:
    cache_key = (key, round(size_px * 10))
    if cache_key not in _FONT_CACHE:
        _FONT_CACHE[cache_key] = ImageFont.truetype(FONT_PATHS[key], int(round(size_px * 2)))
    return _FONT_CACHE[cache_key]

def measure_px(text: str, key: str, size_px: float) -> float:
    f = get_font(key, size_px)
    return f.getlength(text) / 2.0

def wrap_lines(text: str, key: str, size_px: float, max_width: float, max_lines: int) -> list[str]:
    words = text.split()
    lines = []
    cur = []
    for w in words:
        candidate = " ".join(cur + [w])
        if not cur or measure_px(candidate, key, size_px) <= max_width:
            cur.append(w)
        else:
            lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    if len(lines) > max_lines:
        raise ValueError(
            f"Text overflow ({len(lines)} > {max_lines} lines at {size_px}px, max_w={max_width}): {text!r} -> {lines}"
        )
    return lines

def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

BADGE_COLORS = {
    "CONFIRMED": ("#166534", "#FFFFFF"),
    "OFFICIAL": ("#1E40AF", "#FFFFFF"),
    "REPORTED": ("#334155", "#FFFFFF"),
    "CLAIM": ("#B45309", "#FFFFFF"),
}

REGION_COLORS = {
    "EUROPE": "#1B365D",
    "MIDDLE EAST": "#9E2A2B",
    "ASIA-PACIFIC": "#B45309",
    "AMERICAS": "#0F766E",
    "AFRICA": "#15803D",
    "OCEANIA": "#0369A1",
    "WORLD": "#4B5563",
}

def draw_hero_illustration(idx: int, x: float, y: float, w: float, h: float) -> str:
    out = []
    clip_id = f"hero_clip_{idx}"
    out.append(f'<defs><clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" ry="4"/></clipPath></defs>')
    out.append(f'<g clip-path="url(#{clip_id})">')

    if idx == 1:
        # COP31 Antalya collapse: daylight-dusk conference teal-gold palette, globe grid, document, red NO DEAL stamp, 44h overtime plaque
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#143D52"/>')
        out.append(f'<rect x="{x}" y="{y+h-22}" width="{w}" height="22" fill="#0C2636"/>')
        # Sunburst/plenary arcs
        cx, cy = x + 62, y + 54
        for r in (40, 30, 20):
            out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#266485" stroke-width="1"/>')
        out.append(f'<line x1="{cx-42}" y1="{cy}" x2="{cx+42}" y2="{cy}" stroke="#266485" stroke-width="1"/>')
        out.append(f'<line x1="{cx}" y1="{cy-42}" x2="{cx}" y2="{cy+42}" stroke="#266485" stroke-width="1"/>')
        # Earth globe + warming curve
        out.append(f'<circle cx="{cx}" cy="{cy}" r="18" fill="#1B5572" stroke="#38BDF8" stroke-width="1.3"/>')
        out.append(f'<path d="M{cx-12},{cy+6} Q{cx-4},{cy-10} {cx+10},{cy-4} T{cx+14},{cy+8}" fill="none" stroke="#34D399" stroke-width="2.2"/>')
        # Treaty document in center
        dx, dy = x + 112, y + 23
        out.append(f'<rect x="{dx}" y="{dy}" width="84" height="60" rx="3" fill="#FFFFFF" stroke="#94A3B8" stroke-width="1"/>')
        out.append(f'<text x="{dx+42}" y="{dy+11}" font-family="Liberation Sans" font-size="6.8" font-weight="bold" fill="#0F172A" text-anchor="middle">ANTALYA DRAFT</text>')
        out.append(f'<line x1="{dx+8}" y1="{dy+16}" x2="{dx+76}" y2="{dy+16}" stroke="#CBD5E1" stroke-width="1.5"/>')
        out.append(f'<text x="{dx+42}" y="{dy+26}" font-family="Liberation Sans" font-size="6.5" font-weight="bold" fill="#64748B" text-anchor="middle">FOSSIL FUELS</text>')
        out.append(f'<line x1="{dx+6}" y1="{dy+24}" x2="{dx+78}" y2="{dy+24}" stroke="#DC2626" stroke-width="2"/>')
        out.append(f'<text x="{dx+42}" y="{dy+36}" font-family="Liberation Sans" font-size="6.2" fill="#64748B" text-anchor="middle">$120B ADAPTATION</text>')
        out.append(f'<line x1="{dx+6}" y1="{dy+34}" x2="{dx+78}" y2="{dy+34}" stroke="#DC2626" stroke-width="1.8"/>')
        # Angled NO DEAL stamp
        out.append(f'<g transform="translate({dx+42},{dy+46}) rotate(-8)">')
        out.append('<rect x="-36" y="-9" width="72" height="16.5" rx="2" fill="#991B1B" stroke="#FCA5A5" stroke-width="1.2"/>')
        out.append('<text x="0" y="2.8" font-family="Liberation Sans" font-size="9.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">NO DEAL</text>')
        out.append('</g>')
        # Right metric callout: +44h overtime
        out.append(f'<rect x="{x+206}" y="{y+24}" width="108" height="56" rx="4" fill="#0E2C3D" stroke="#38BDF8" stroke-width="1"/>')
        out.append(f'<text x="{x+260}" y="{y+46}" font-family="TeX Gyre Heros Cn" font-size="22" font-weight="bold" fill="#FBBF24" text-anchor="middle">+44 HRS</text>')
        out.append(f'<text x="{x+260}" y="{y+59}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#FFFFFF" text-anchor="middle">OVERTIME DEADLOCK</text>')
        out.append(f'<text x="{x+260}" y="{y+71}" font-family="Liberation Sans" font-size="6.5" fill="#7DD3FC" text-anchor="middle">~200 NATIONS · 1.5°C GAP</text>')

    elif idx == 2:
        # Ukraine 186 drones & Dymer 5-storey collapse
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#0F172A"/>')
        out.append(f'<rect x="{x}" y="{y+h-18}" width="{w}" height="18" fill="#1E293B"/>')
        # Drone swarm trajectories from left to right
        for dy_off, dx_off in [(28, 22), (42, 45), (56, 18), (34, 78), (50, 92), (64, 58)]:
            px, py = x + dx_off, y + dy_off
            out.append(f'<polygon points="{px},{py} {px-11},{py-4} {px-8},{py} {px-11},{py+4}" fill="#F97316"/>')
            out.append(f'<line x1="{px-24}" y1="{py-2}" x2="{px-12}" y2="{py}" stroke="#FDBA74" stroke-width="0.9" stroke-dasharray="2,2"/>')
        # Air defence interceptor dome & burst
        out.append(f'<path d="M{x+115},{y+78} Q{x+145},{y+22} {x+185},{y+44}" fill="none" stroke="#38BDF8" stroke-width="1.6" stroke-dasharray="3,2"/>')
        out.append(f'<circle cx="{x+138}" cy="{y+42}" r="7.5" fill="#38BDF8" fill-opacity="0.28" stroke="#38BDF8" stroke-width="1.2"/>')
        out.append(f'<circle cx="{x+138}" cy="{y+42}" r="2.8" fill="#E0F2FE"/>')
        # 5-storey Dymer apartment block on center-right
        bx, by = x + 186, y + 25
        out.append(f'<rect x="{bx}" y="{by}" width="56" height="55" fill="#334155" stroke="#94A3B8" stroke-width="1"/>')
        # Collapsed V-notch in middle of block
        out.append(f'<polygon points="{bx+16},{by} {bx+40},{by} {bx+32},{by+35} {bx+22},{by+35}" fill="#0F172A"/>')
        out.append(f'<circle cx="{bx+28}" cy="{by+28}" r="9.5" fill="#EF4444" fill-opacity="0.8"/>')
        out.append(f'<circle cx="{bx+28}" cy="{by+26}" r="5.5" fill="#FBBF24"/>')
        # Windows on remaining sides
        for row in range(5):
            for col in (4, 10, 42, 48):
                wx, wy = bx + col, by + 5 + row * 9.5
                out.append(f'<rect x="{wx}" y="{wy}" width="4" height="5.5" fill="#FDE047" fill-opacity="0.85"/>')
        # Big stat counter box on right
        out.append(f'<rect x="{x+248}" y="{y+24}" width="66" height="56" rx="4" fill="#1E293B" stroke="#F97316" stroke-width="1"/>')
        out.append(f'<text x="{x+281}" y="{y+46}" font-family="TeX Gyre Heros Cn" font-size="22" font-weight="bold" fill="#FB923C" text-anchor="middle">186</text>')
        out.append(f'<text x="{x+281}" y="{y+58}" font-family="Liberation Sans" font-size="6.8" font-weight="bold" fill="#38BDF8" text-anchor="middle">161 DOWNED</text>')
        out.append(f'<text x="{x+281}" y="{y+70}" font-family="Liberation Sans" font-size="6.2" fill="#E2E8F0" text-anchor="middle">DYMER: 4 DEAD</text>')

    elif idx == 3:
        # Bahrain radar claim vs denial: warm desert crimson-amber left vs Gulf slate-teal right
        out.append(f'<rect x="{x}" y="{y}" width="{w/2}" height="{h}" fill="#3B1A1E"/>')
        out.append(f'<rect x="{x+w/2}" y="{y}" width="{w/2}" height="{h}" fill="#132D42"/>')
        out.append(f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#FBBF24" stroke-width="1.5" stroke-dasharray="3,2"/>')
        # Left side: IRGC Claim — Patriot phased-array radar dish + crosshair
        rx, ry = x + 44, y + 68
        out.append(f'<rect x="{rx-14}" y="{ry}" width="28" height="10" fill="#94A3B8"/>')
        out.append(f'<polygon points="{rx-18},{ry-4} {rx+6},{ry-32} {rx+16},{ry-24} {rx-8},{ry+2}" fill="#CBD5E1" stroke="#FFFFFF" stroke-width="1"/>')
        out.append(f'<circle cx="{rx+4}" cy="{ry-16}" r="15" fill="none" stroke="#FBBF24" stroke-width="1.4" stroke-dasharray="2,2"/>')
        out.append(f'<line x1="{rx-14}" y1="{ry-16}" x2="{rx+22}" y2="{ry-16}" stroke="#FBBF24" stroke-width="1"/>')
        out.append(f'<line x1="{rx+4}" y1="{ry-34}" x2="{rx+4}" y2="{ry+2}" stroke="#FBBF24" stroke-width="1"/>')
        out.append(f'<text x="{x+114}" y="{y+42}" font-family="Liberation Sans" font-size="8.2" font-weight="bold" fill="#FBBF24" text-anchor="middle">IRGC CLAIM</text>')
        out.append(f'<text x="{x+114}" y="{y+55}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#FEF3C7" text-anchor="middle">2 Patriot Radars</text>')
        out.append(f'<text x="{x+114}" y="{y+67}" font-family="Liberation Sans" font-size="6.6" fill="#FCA5A5" text-anchor="middle">Al-Riffa &amp; Awali</text>')
        # Right side: Bahrain Denial — Sitra industrial tanks + interception arc
        tx, ty = x + 186, y + 54
        out.append(f'<rect x="{tx}" y="{ty}" width="20" height="22" rx="2" fill="#64748B" stroke="#CBD5E1" stroke-width="1"/>')
        out.append(f'<rect x="{tx+24}" y="{ty+4}" width="20" height="18" rx="2" fill="#64748B" stroke="#CBD5E1" stroke-width="1"/>')
        out.append(f'<circle cx="{tx+34}" cy="{ty-2}" r="7.5" fill="#F97316" fill-opacity="0.9"/>')
        out.append(f'<circle cx="{tx+34}" cy="{ty-4}" r="4.2" fill="#FDE047"/>')
        out.append(f'<path d="M{tx-8},{ty-8} Q{tx+18},{ty-30} {tx+48},{ty-10}" fill="none" stroke="#38BDF8" stroke-width="2"/>')
        out.append(f'<text x="{x+276}" y="{y+42}" font-family="Liberation Sans" font-size="8.2" font-weight="bold" fill="#38BDF8" text-anchor="middle">MANAMA DENIAL</text>')
        out.append(f'<text x="{x+276}" y="{y+55}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#E0F2FE" text-anchor="middle">Radars Intact</text>')
        out.append(f'<text x="{x+276}" y="{y+67}" font-family="Liberation Sans" font-size="6.6" fill="#93C5FD" text-anchor="middle">Sitra Site Fire</text>')

    # Top corner callout pills for Hero cards
    pills = {
        1: ("COP31 · ANTALYA OVERTIME", "NO FOSSIL-FUEL DEAL"),
        2: ("186 DRONES OVERNIGHT", "161 DOWNED · DYMER HIT"),
        3: ("CLAIM VS DENIAL · BAHRAIN", "2 RADARS? · SITRA FIRE"),
    }
    p_left, p_right = pills[idx]
    lw = measure_px(p_left, "sans_bold", 7.2) + 12
    rw = measure_px(p_right, "sans_bold", 7.2) + 12
    out.append(f'<rect x="{x+6}" y="{y+5}" width="{lw:.1f}" height="14" rx="3" fill="#9E2A2B"/>')
    out.append(f'<text x="{x+6+lw/2:.1f}" y="{y+14.5}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{esc(p_left)}</text>')
    out.append(f'<rect x="{x+w-rw-6:.1f}" y="{y+5}" width="{rw:.1f}" height="14" rx="3" fill="#F8FAFC" fill-opacity="0.94"/>')
    out.append(f'<text x="{x+w-6-rw/2:.1f}" y="{y+14.5}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#0F172A" text-anchor="middle">{esc(p_right)}</text>')

    out.append("</g>")
    return "\n".join(out)

def draw_secondary_illustration(idx: int, x: float, y: float, w: float, h: float, tag_left: str, tag_right: str) -> str:
    out = []
    clip_id = f"sec_clip_{idx}"
    out.append(f'<defs><clipPath id="{clip_id}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3.5" ry="3.5"/></clipPath></defs>')
    out.append(f'<g clip-path="url(#{clip_id})">')

    if idx == 4:
        # US House 258 seats hemicycle on rich Capitol slate-blue
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#173254"/>')
        cx, cy = x + 96, y + 56
        out.append(f'<path d="M{cx-46},{cy} A46,46 0 0,1 {cx+15},{cy-43.5}" fill="none" stroke="#3B82F6" stroke-width="12"/>')
        out.append(f'<path d="M{cx+15},{cy-43.5} A46,46 0 0,1 {cx+46},{cy}" fill="none" stroke="#EF4444" stroke-width="12"/>')
        out.append(f'<text x="{cx}" y="{cy-8}" font-family="TeX Gyre Heros Cn" font-size="19" font-weight="bold" fill="#FFFFFF" text-anchor="middle">258</text>')
        out.append(f'<text x="{cx}" y="{cy+0.5}" font-family="Liberation Sans" font-size="6.2" font-weight="bold" fill="#BFDBFE" text-anchor="middle">DEM HOUSE SEATS</text>')

    elif idx == 5:
        # Benghazi corvette Merkury sunk: Mediterranean teal sky + lighter sea waves + large tilted warship & explosion
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#134E6F"/>')
        out.append(f'<rect x="{x}" y="{y+42}" width="{w}" height="{h-42}" fill="#0284C7"/>')
        # Listing warship silhouette (-16 deg) with superstructure, mast & radar
        out.append(f'<g transform="translate({x+88},{y+41}) rotate(15)">')
        out.append('<polygon points="-54,2 50,2 40,12 -44,12" fill="#94A3B8" stroke="#F8FAFC" stroke-width="1"/>')
        out.append('<polygon points="-24,2 -14,-11 16,-11 24,2" fill="#64748B" stroke="#E2E8F0" stroke-width="0.8"/>')
        out.append('<line x1="0" y1="-11" x2="0" y2="-20" stroke="#F8FAFC" stroke-width="1.4"/>')
        out.append('<line x1="-6" y1="-16" x2="6" y2="-16" stroke="#F8FAFC" stroke-width="1.1"/>')
        out.append('</g>')
        # Explosion plume & wave crest
        out.append(f'<circle cx="{x+112}" cy="{y+39}" r="11" fill="#EF4444" fill-opacity="0.9"/>')
        out.append(f'<circle cx="{x+112}" cy="{y+38}" r="6" fill="#FDE047"/>')
        out.append(f'<path d="M{x+8},{y+48} Q{x+40},{y+44} {x+72},{y+48} T{x+136},{y+48} T{x+180},{y+48}" fill="none" stroke="#BAE6FD" stroke-width="1.3"/>')
        out.append(f'<text x="{x+156}" y="{y+55}" font-family="TeX Gyre Heros Cn" font-size="11.5" font-weight="bold" fill="#FEF08A" text-anchor="middle">SUNK</text>')

    elif idx == 6:
        # Iran 2-hour rolling blackouts: dusk purple-amber sky + half-darkened skyline + bright steel pylon + 2H OFF dial
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#2E1A47"/>')
        # City skyline silhouette at bottom
        out.append(f'<rect x="{x+8}" y="{y+42}" width="16" height="20" fill="#1E293B"/>')
        out.append(f'<rect x="{x+26}" y="{y+36}" width="18" height="26" fill="#1E293B"/>')
        for wx in (11, 17, 29, 36):
            for wy in (45, 51):
                out.append(f'<rect x="{x+wx}" y="{y+wy}" width="3" height="3.5" fill="#FDE047"/>')
        # Bright steel pylon in center-left
        px, py = x + 74, y + 58
        out.append(f'<polygon points="{px-11},{py} {px-3},{py-34} {px+3},{py-34} {px+11},{py}" fill="none" stroke="#E2E8F0" stroke-width="1.5"/>')
        out.append(f'<line x1="{px-15}" y1="{py-23}" x2="{px+15}" y2="{py-23}" stroke="#E2E8F0" stroke-width="1.5"/>')
        out.append(f'<line x1="{px-12}" y1="{py-13}" x2="{px+12}" y2="{py-13}" stroke="#E2E8F0" stroke-width="1.5"/>')
        # Clock dial with 2h red cut sector
        cx, cy = x + 140, y + 39
        out.append(f'<circle cx="{cx}" cy="{cy}" r="16.5" fill="#111827" stroke="#FBBF24" stroke-width="1.6"/>')
        out.append(f'<path d="M{cx},{cy} L{cx},{cy-15.5} A15.5,15.5 0 0,1 {cx+13.5},{cy-7.5} Z" fill="#EF4444"/>')
        out.append(f'<text x="{cx}" y="{cy+4}" font-family="TeX Gyre Heros Cn" font-size="10.5" font-weight="bold" fill="#FEF08A" text-anchor="middle">2H OFF</text>')

    elif idx == 7:
        # Hong Kong Election Committee 98.79% turnout: civic blue with HK skyline towers + ballot box
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#1D3E5E"/>')
        # HK skyline silhouette on left background
        for tx_off, th in [(10, 26), (20, 34), (31, 22), (41, 30)]:
            out.append(f'<rect x="{x+tx_off}" y="{y+h-th}" width="8" height="{th}" fill="#2E5A82"/>')
        bx, by = x + 52, y + 27
        out.append(f'<rect x="{bx}" y="{by+10}" width="34" height="22" rx="2" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1"/>')
        out.append(f'<rect x="{bx+4}" y="{by+14}" width="26" height="4" fill="#DC2626"/>')
        out.append(f'<rect x="{bx+8}" y="{by+1}" width="18" height="12" fill="#FFFFFF" stroke="#475569" stroke-width="0.9"/>')
        out.append(f'<polyline points="{bx+12},{by+7} {bx+15},{by+10} {bx+22},{by+3}" fill="none" stroke="#16A34A" stroke-width="1.8"/>')
        out.append(f'<text x="{x+136}" y="{y+42}" font-family="TeX Gyre Heros Cn" font-size="20" font-weight="bold" fill="#4ADE80" text-anchor="middle">98.79%</text>')
        out.append(f'<text x="{x+136}" y="{y+53.5}" font-family="Liberation Sans" font-size="6.3" font-weight="bold" fill="#FFFFFF" text-anchor="middle">5,640 / 5,709 VOTERS</text>')

    elif idx == 8:
        # India 720/9 declared in Wellington: vivid daylight emerald cricket oval + tan pitch + stumps + scoreboard
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#15803D"/>')
        out.append(f'<ellipse cx="{x+96}" cy="{y+52}" rx="86" ry="20" fill="#16A34A" stroke="#86EFAC" stroke-width="0.9"/>')
        # Scoreboard plaque on left
        out.append(f'<rect x="{x+14}" y="{y+22}" width="96" height="34" rx="3" fill="#062E1E" stroke="#FBBF24" stroke-width="1.2"/>')
        out.append(f'<text x="{x+62}" y="{y+41}" font-family="TeX Gyre Heros Cn" font-size="18.5" font-weight="bold" fill="#FDE047" text-anchor="middle">720/9d</text>')
        out.append(f'<text x="{x+62}" y="{y+51}" font-family="Liberation Sans" font-size="6.2" font-weight="bold" fill="#A7F3D0" text-anchor="middle">INDIA RECORD IN NZ</text>')
        # Stumps & ball on right
        sx = x + 132
        for s_off in (0, 7, 14):
            out.append(f'<line x1="{sx+s_off}" y1="{y+25}" x2="{sx+s_off}" y2="{y+54}" stroke="#FEF08A" stroke-width="2.3"/>')
        out.append(f'<line x1="{sx-1}" y1="{y+25}" x2="{sx+15}" y2="{y+25}" stroke="#FEF08A" stroke-width="2"/>')
        out.append(f'<circle cx="{sx+30}" cy="{y+43}" r="7.5" fill="#DC2626" stroke="#FFFFFF" stroke-width="1"/>')
        out.append(f'<path d="M{sx+25},{y+39} Q{sx+30},{y+43} {sx+35},{y+47}" fill="none" stroke="#FFFFFF" stroke-width="0.9" stroke-dasharray="1.5,1.5"/>')

    elif idx == 9:
        # Verstappen wins Las Vegas GP: non-overlapping layout (gantry left, F1 car center, 75TH WIN plaque right)
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#18182B"/>')
        # Track asphalt & red/white kerbs on left-center
        out.append(f'<polygon points="{x+6},{y+56} {x+124},{y+34} {x+124},{y+54} {x+6},{y+62}" fill="#334155"/>')
        out.append(f'<line x1="{x+6}" y1="{y+56}" x2="{x+124}" y2="{y+34}" stroke="#EF4444" stroke-width="2.2" stroke-dasharray="5,5"/>')
        # Checkered gantry on far left
        out.append(f'<rect x="{x+14}" y="{y+24}" width="10" height="32" fill="#E2E8F0"/>')
        out.append(f'<rect x="{x+14}" y="{y+24}" width="5" height="8" fill="#0F172A"/>')
        out.append(f'<rect x="{x+19}" y="{y+32}" width="5" height="8" fill="#0F172A"/>')
        # F1 car cleanly centered at x+68, y+45
        cx, cy = x + 68, y + 45
        out.append(f'<polygon points="{cx-24},{cy+4} {cx+18},{cy-2} {cx+26},{cy+3} {cx-22},{cy+9}" fill="#2563EB" stroke="#60A5FA" stroke-width="0.8"/>')
        out.append(f'<polygon points="{cx-6},{cy+1} {cx+6},{cy-4} {cx+10},{cy+1}" fill="#EF4444"/>')
        out.append(f'<circle cx="{cx-14}" cy="{cy+7}" r="5" fill="#0F172A" stroke="#FBBF24" stroke-width="1.5"/>')
        out.append(f'<circle cx="{cx+15}" cy="{cy+3}" r="5" fill="#0F172A" stroke="#FBBF24" stroke-width="1.5"/>')
        # Right podium callout box below the top-right pill (zero overlap!)
        out.append(f'<rect x="{x+128}" y="{y+24}" width="54" height="33" rx="3" fill="#27203A" stroke="#FBBF24" stroke-width="1"/>')
        out.append(f'<text x="{x+155}" y="{y+40}" font-family="TeX Gyre Heros Cn" font-size="12.5" font-weight="bold" fill="#FDE047" text-anchor="middle">75TH WIN</text>')
        out.append(f'<text x="{x+155}" y="{y+51}" font-family="Liberation Sans" font-size="6.3" font-weight="bold" fill="#E2E8F0" text-anchor="middle">POLE TO FLAG</text>')

    elif idx == 10:
        # Seoul AI exam cheating resignation & emergency market review: warm slate-burgundy with clean 3-zone separation
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#2D2338"/>')
        # Scantron card on left (x+12..x+58)
        sx, sy = x + 12, y + 22
        out.append(f'<rect x="{sx}" y="{sy}" width="46" height="35" rx="2" fill="#FFFFFF" stroke="#CBD5E1" stroke-width="1"/>')
        for r_i in range(3):
            for c_i in range(4):
                fill_c = "#DC2626" if (r_i + c_i) % 2 == 0 else "#94A3B8"
                out.append(f'<circle cx="{sx+8.5+c_i*9.5}" cy="{sy+9+r_i*8.5}" r="2.7" fill="{fill_c}"/>')
        # Center market stabilization mini bars (x+66..x+92)
        for bi, bh_bar in enumerate((12, 18, 25)):
            bx_bar = x + 67 + bi * 8.5
            out.append(f'<rect x="{bx_bar}" y="{y+56-bh_bar}" width="6" height="{bh_bar}" rx="1" fill="#34D399"/>')
        # Right framed callout box (x+98..x+181, completely clear of chart & scantron)
        out.append(f'<rect x="{x+98}" y="{y+23}" width="83" height="34" rx="3" fill="#1F162B" stroke="#F87171" stroke-width="0.9"/>')
        out.append(f'<text x="{x+139.5}" y="{y+40}" font-family="TeX Gyre Heros Cn" font-size="15.5" font-weight="bold" fill="#FCA5A5" text-anchor="middle">111 CASES</text>')
        out.append(f'<text x="{x+139.5}" y="{y+51}" font-family="Liberation Sans" font-size="5.8" font-weight="bold" fill="#A7F3D0" text-anchor="middle">AI EXAM · MARKET FUND</text>')

    elif idx == 11:
        # DR Congo Ebola clinic trapped + Sudan Khartoum drones: warm savannah olive-ochre + hospital tent + drones
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#2F3624"/>')
        # White medical tent silhouette on left-center
        tx, ty = x + 44, y + 40
        out.append(f'<polygon points="{tx-26},{ty+16} {tx-20},{ty-4} {tx},{ty-14} {tx+20},{ty-4} {tx+26},{ty+16}" fill="#F8FAFC" stroke="#86EFAC" stroke-width="1"/>')
        out.append(f'<rect x="{tx-2.5}" y="{ty-6}" width="5" height="14" fill="#DC2626"/>')
        out.append(f'<rect x="{tx-7}" y="{ty-1.5}" width="14" height="5" fill="#DC2626"/>')
        # Incoming drone icon & numbers on right
        out.append(f'<polygon points="{x+102},{y+30} {x+92},{y+26} {x+95},{y+30} {x+92},{y+34}" fill="#F97316"/>')
        out.append(f'<text x="{x+136}" y="{y+41}" font-family="TeX Gyre Heros Cn" font-size="16" font-weight="bold" fill="#FDE047" text-anchor="middle">11,613</text>')
        out.append(f'<text x="{x+136}" y="{y+52.5}" font-family="Liberation Sans" font-size="6.0" font-weight="bold" fill="#FFFFFF" text-anchor="middle">DRC EBOLA · 4 DEAD SUDAN</text>')

    elif idx == 12:
        # Liverpool 4-0 Man Utd (Anfield pitch green + goalpost/ball) & Alcaraz ATP Finals (Turin blue court + net/trophy)
        out.append(f'<rect x="{x}" y="{y}" width="{w/2}" height="{h}" fill="#14532D"/>')
        out.append(f'<rect x="{x+w/2}" y="{y}" width="{w/2}" height="{h}" fill="#1E3A8A"/>')
        # Left: Soccer goalpost, penalty box & red card icon
        out.append(f'<rect x="{x+8}" y="{y+24}" width="26" height="18" fill="none" stroke="#86EFAC" stroke-width="1.2"/>')
        out.append(f'<circle cx="{x+21}" cy="{y+35}" r="4.5" fill="#FFFFFF" stroke="#0F172A" stroke-width="0.8"/>')
        out.append(f'<rect x="{x+74}" y="{y+24}" width="8" height="12" rx="1" fill="#EF4444" stroke="#FFFFFF" stroke-width="0.7"/>')
        out.append(f'<text x="{x+52}" y="{y+44}" font-family="TeX Gyre Heros Cn" font-size="17" font-weight="bold" fill="#FFFFFF" text-anchor="middle">4 – 0</text>')
        out.append(f'<text x="{x+48}" y="{y+55}" font-family="Liberation Sans" font-size="6.2" font-weight="bold" fill="#BBF7D0" text-anchor="middle">LIV v 10-MAN MUN</text>')
        # Right: Tennis court lines, net, yellow ball & trophy cup
        out.append(f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#F8FAFC" stroke-width="1.2"/>')
        out.append(f'<rect x="{x+102}" y="{y+24}" width="78" height="32" fill="none" stroke="#93C5FD" stroke-width="0.8"/>')
        out.append(f'<circle cx="{x+112}" cy="{y+34}" r="4" fill="#FACC15" stroke="#FFFFFF" stroke-width="0.7"/>')
        out.append(f'<text x="{x+146}" y="{y+42}" font-family="TeX Gyre Heros Cn" font-size="13.5" font-weight="bold" fill="#FDE047" text-anchor="middle">6-2 7-6</text>')
        out.append(f'<text x="{x+144}" y="{y+54}" font-family="Liberation Sans" font-size="6.2" font-weight="bold" fill="#E0F2FE" text-anchor="middle">ALCARAZ ATP TITLE</text>')

    elif idx == 13:
        # Pope Leo XIV 1,300 poor guests (warm Vatican gold/terracotta + dome) & Wembanyama 50 pts (arena wood + hoop/ball)
        out.append(f'<rect x="{x}" y="{y}" width="{w/2}" height="{h}" fill="#6B2E1A"/>')
        out.append(f'<rect x="{x+w/2}" y="{y}" width="{w/2}" height="{h}" fill="#3B1D11"/>')
        out.append(f'<line x1="{x+w/2}" y1="{y}" x2="{x+w/2}" y2="{y+h}" stroke="#FDE68A" stroke-width="1.2"/>')
        # Left: St. Peter's dome silhouette & table
        out.append(f'<path d="M{x+12},{y+44} A10,10 0 0,1 {x+32},{y+44} Z" fill="#FDE68A" fill-opacity="0.85"/>')
        out.append(f'<line x1="{x+22}" y1="{y+29}" x2="{x+22}" y2="{y+34}" stroke="#FDE68A" stroke-width="1.3"/>')
        out.append(f'<line x1="{x+10}" y1="{y+46}" x2="{x+34}" y2="{y+46}" stroke="#FFFFFF" stroke-width="1.5"/>')
        out.append(f'<text x="{x+60}" y="{y+43}" font-family="TeX Gyre Heros Cn" font-size="16.5" font-weight="bold" fill="#FDE047" text-anchor="middle">1,300</text>')
        out.append(f'<text x="{x+48}" y="{y+54.5}" font-family="Liberation Sans" font-size="6.0" font-weight="bold" fill="#FEF3C7" text-anchor="middle">VATICAN POOR LUNCH</text>')
        # Right: Basketball backboard, rim, net & orange ball
        bx_h, by_h = x + 112, y + 34
        out.append(f'<rect x="{bx_h-8}" y="{by_h-9}" width="16" height="11" fill="none" stroke="#E2E8F0" stroke-width="1.1"/>')
        out.append(f'<line x1="{bx_h-5}" y1="{by_h+2}" x2="{bx_h+5}" y2="{by_h+2}" stroke="#F97316" stroke-width="1.8"/>')
        out.append(f'<polygon points="{bx_h-4},{by_h+2} {bx_h+4},{by_h+2} {bx_h+2.5},{by_h+9} {bx_h-2.5},{by_h+9}" fill="none" stroke="#FFFFFF" stroke-width="0.8"/>')
        out.append(f'<circle cx="{bx_h+12}" cy="{by_h-2}" r="4.5" fill="#F97316" stroke="#FDE047" stroke-width="0.7"/>')
        out.append(f'<text x="{x+156}" y="{y+43}" font-family="TeX Gyre Heros Cn" font-size="16" font-weight="bold" fill="#FB923C" text-anchor="middle">50 PTS</text>')
        out.append(f'<text x="{x+144}" y="{y+54.5}" font-family="Liberation Sans" font-size="6.0" font-weight="bold" fill="#FED7AA" text-anchor="middle">WEMBY · 19 REB · 5 BLK</text>')

    # Top corner callout pills for Secondary cards
    lw = measure_px(tag_left, "sans_bold", 6.3) + 9
    rw = measure_px(tag_right, "sans_bold", 6.3) + 9
    out.append(f'<rect x="{x+4}" y="{y+4}" width="{lw:.1f}" height="12.5" rx="2.5" fill="#9E2A2B"/>')
    out.append(f'<text x="{x+4+lw/2:.1f}" y="{y+12.5}" font-family="Liberation Sans" font-size="6.3" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{esc(tag_left)}</text>')
    out.append(f'<rect x="{x+w-rw-4:.1f}" y="{y+4}" width="{rw:.1f}" height="12.5" rx="2.5" fill="#F8FAFC" fill-opacity="0.95"/>')
    out.append(f'<text x="{x+w-4-rw/2:.1f}" y="{y+12.5}" font-family="Liberation Sans" font-size="6.3" font-weight="bold" fill="#0F172A" text-anchor="middle">{esc(tag_right)}</text>')

    out.append("</g>")
    return "\n".join(out)

def draw_world_map(x: float, y: float, w: float, h: float) -> str:
    out = []
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#0B1D33" stroke="#1E3A5F" stroke-width="1.2"/>')
    # Header bar
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="18" rx="4" fill="#162E4A"/>')
    out.append(f'<text x="{x+8}" y="{y+12.5}" font-family="Liberation Sans" font-size="7.8" font-weight="bold" fill="#F8FAFC" letter-spacing="0.5">WHERE IT HAPPENED — PINNED TO STORIES #1–#13</text>')

    mx, my, mw, mh = x + 6, y + 21, w - 12, h - 46
    # Subtle graticule lines
    for gx in range(1, 6):
        lx = mx + mw * gx / 6.0
        out.append(f'<line x1="{lx:.1f}" y1="{my}" x2="{lx:.1f}" y2="{my+mh}" stroke="#19395A" stroke-width="0.6" stroke-dasharray="2,2"/>')
    for gy in range(1, 4):
        ly = my + mh * gy / 4.0
        out.append(f'<line x1="{mx}" y1="{ly:.1f}" x2="{mx+mw}" y2="{ly:.1f}" stroke="#19395A" stroke-width="0.6" stroke-dasharray="2,2"/>')

    # High-contrast continent polygons (bright slate-teal fill + cyan coastline stroke so continents pop at 300px)
    continents = [
        # North America
        [(0.04, 0.16), (0.17, 0.11), (0.28, 0.15), (0.31, 0.27), (0.24, 0.42), (0.18, 0.47), (0.12, 0.41), (0.07, 0.28)],
        # Greenland
        [(0.31, 0.07), (0.39, 0.06), (0.41, 0.15), (0.34, 0.17)],
        # South America
        [(0.24, 0.51), (0.33, 0.54), (0.37, 0.66), (0.32, 0.89), (0.27, 0.92), (0.23, 0.72)],
        # Europe
        [(0.43, 0.13), (0.56, 0.11), (0.61, 0.22), (0.58, 0.34), (0.45, 0.36), (0.42, 0.25)],
        # Africa
        [(0.43, 0.40), (0.56, 0.39), (0.63, 0.52), (0.59, 0.79), (0.52, 0.85), (0.46, 0.64), (0.42, 0.52)],
        # Asia
        [(0.59, 0.12), (0.87, 0.13), (0.93, 0.26), (0.87, 0.48), (0.76, 0.54), (0.68, 0.47), (0.61, 0.42), (0.58, 0.28)],
        # Maritime SE Asia
        [(0.77, 0.57), (0.86, 0.57), (0.89, 0.64), (0.79, 0.65)],
        # Australia
        [(0.79, 0.71), (0.90, 0.70), (0.92, 0.84), (0.81, 0.86)],
        # New Zealand
        [(0.94, 0.84), (0.97, 0.82), (0.98, 0.90), (0.95, 0.91)],
    ]
    for poly in continents:
        pts = " ".join(f"{mx + px * mw:.1f},{my + py * mh:.1f}" for px, py in poly)
        out.append(f'<polygon points="{pts}" fill="#2E5F85" stroke="#60A5FA" stroke-width="1.0"/>')

    # 13 well-separated numbered pins (no overlapping inline city labels; city index sits cleanly in the 2-line footer)
    pins = [
        (1, 0.57, 0.36, "#4B5563"),   # Antalya
        (2, 0.55, 0.21, "#1B365D"),   # Ukraine (Dymer)
        (3, 0.64, 0.46, "#9E2A2B"),   # Bahrain
        (4, 0.24, 0.33, "#0F766E"),   # Washington D.C.
        (5, 0.51, 0.43, "#15803D"),   # Benghazi
        (6, 0.67, 0.36, "#9E2A2B"),   # Tehran
        (7, 0.81, 0.45, "#B45309"),   # Hong Kong
        (8, 0.96, 0.87, "#0369A1"),   # Wellington NZ
        (9, 0.13, 0.34, "#0F766E"),   # Las Vegas
        (10, 0.86, 0.32, "#B45309"),  # Seoul
        (11, 0.56, 0.59, "#15803D"),  # DRC / Sudan
        (12, 0.44, 0.22, "#1B365D"),  # Anfield / Turin
        (13, 0.49, 0.31, "#4B5563"),  # Vatican
    ]
    for num, nx, ny, col in pins:
        px, py = mx + nx * mw, my + ny * mh
        out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="6.4" fill="{col}" stroke="#FFFFFF" stroke-width="1.2"/>')
        out.append(f'<text x="{px:.1f}" y="{py+2.3:.1f}" font-family="Liberation Sans" font-size="6.6" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{num}</text>')

    # Clean 2-line pin key at bottom of map box (zero collisions!)
    ly = y + h - 21
    out.append(f'<rect x="{x+4}" y="{ly}" width="{w-8}" height="18" rx="2" fill="#081424"/>')
    out.append(f'<text x="{x+w/2}" y="{ly+7.8}" font-family="Liberation Sans" font-size="5.9" font-weight="bold" fill="#E2E8F0" text-anchor="middle">1 Antalya · 2 Dymer · 3 Bahrain · 4 D.C. · 5 Benghazi · 6 Tehran · 7 HK</text>')
    out.append(f'<text x="{x+w/2}" y="{ly+15.5}" font-family="Liberation Sans" font-size="5.9" font-weight="bold" fill="#93C5FD" text-anchor="middle">8 Wellington · 9 Vegas · 10 Seoul · 11 DRC/Sudan · 12 UK/Turin · 13 Vatican</text>')
    return "\n".join(out)

def build_svg() -> str:
    W, H = 1024, 1024
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    # Warm editorial newsprint background
    svg.append(f'<rect width="{W}" height="{H}" fill="#F6F3EC"/>')

    # 1. Top Meta Banner (y=0..22)
    svg.append('<rect x="0" y="0" width="1024" height="22" fill="#0F1E36"/>')
    svg.append('<text x="14" y="14.5" font-family="Liberation Sans" font-size="8.2" font-weight="bold" fill="#F8FAFC" letter-spacing="0.8">THE WORLD IN ONE DAY · GLOBAL EDITION</text>')
    svg.append('<text x="512" y="14.5" font-family="Liberation Sans" font-size="8.2" font-weight="bold" fill="#FBBF24" text-anchor="middle" letter-spacing="0.6">SUNDAY 22 NOVEMBER 2026 (00:00–24:00 UTC)</text>')
    svg.append('<text x="1010" y="14.5" font-family="Liberation Sans" font-size="8.2" font-weight="bold" fill="#E2E8F0" text-anchor="end" letter-spacing="0.6">34 DATED STORIES · 7 REGIONS · 12 FIELDS</text>')

    # 2. Broadsheet Masthead (y=22..84)
    # Compact left & right ear boxes (134px wide) so giant masthead commands the page
    svg.append('<rect x="14" y="26" width="134" height="37" rx="2" fill="#EFECE4" stroke="#C8C0B0" stroke-width="0.8"/>')
    svg.append('<text x="81" y="37.5" font-family="Liberation Sans" font-size="6.9" font-weight="bold" fill="#8F1D1D" text-anchor="middle">SINGLE-DAY SCOPE</text>')
    svg.append('<text x="81" y="47.5" font-family="Liberation Sans" font-size="6.4" fill="#1F2937" text-anchor="middle">Happened or reported</text>')
    svg.append('<text x="81" y="56.5" font-family="Liberation Sans" font-size="6.6" font-weight="bold" fill="#1F2937" text-anchor="middle">Sun 22 Nov 2026 (UTC)</text>')

    svg.append('<rect x="876" y="26" width="134" height="37" rx="2" fill="#EFECE4" stroke="#C8C0B0" stroke-width="0.8"/>')
    svg.append('<text x="943" y="37.5" font-family="Liberation Sans" font-size="6.9" font-weight="bold" fill="#0F1E36" text-anchor="middle">CERTAINTY TIERS</text>')
    svg.append('<text x="943" y="47.5" font-family="Liberation Sans" font-size="6.4" fill="#166534" font-weight="bold" text-anchor="middle">CONFIRMED · OFFICIAL</text>')
    svg.append('<text x="943" y="56.5" font-family="Liberation Sans" font-size="6.4" fill="#B45309" font-weight="bold" text-anchor="middle">REPORTED · CLAIM (1-side)</text>')

    # Center Giant High-Contrast Serif Date Masthead (46px with subtle ink stroke for display weight)
    svg.append('<text x="512" y="57.5" font-family="TeX Gyre Pagella" font-size="46" font-weight="bold" fill="#0F172A" stroke="#0F172A" stroke-width="0.6" text-anchor="middle">Sunday 22 November 2026</text>')
    svg.append('<line x1="14" y1="67" x2="1010" y2="67" stroke="#8F1D1D" stroke-width="1.2"/>')
    svg.append('<text x="512" y="79.5" font-family="TeX Gyre Pagella" font-size="11.2" font-style="italic" font-weight="bold" fill="#8F1D1D" text-anchor="middle">COP31 collapses in Antalya with no fossil-fuel deal · Russia fires 186 drones as Dymer block collapses · Iran’s Bahrain radar claim meets denial · Democrats reach 258 House seats</text>')
    svg.append('<line x1="14" y1="84" x2="1010" y2="84" stroke="#111827" stroke-width="1.4"/>')

    # 3. 6-Column "THE DAY IN NUMBERS" KPI Strip (y=86..134)
    svg.append('<rect x="14" y="86" width="996" height="48" rx="3" fill="#EFECE4" stroke="#C8C0B0" stroke-width="0.9"/>')
    kpis = [
        ("186", "#2", "drones fired at Ukraine", "161 downed; Dymer block hit", "#9E2A2B"),
        ("44 h", "#1", "COP31 overtime talks", "ends in Antalya with no deal", "#1B365D"),
        ("258", "#4", "US House seats won", "Democrats' largest since 1992", "#0F766E"),
        ("98.79%", "#7", "Hong Kong poll turnout", "5,640 of 5,709 voters cast", "#B45309"),
        ("720/9", "#8", "India Test total in NZ", "record declared in Wellington", "#0369A1"),
        ("50 pts", "#13", "Victor Wembanyama", "19 reb, 5 blk as Spurs win", "#15803D"),
    ]
    col_w = 996.0 / 6.0
    for i, (num, ref, l1, l2, col) in enumerate(kpis):
        kx = 14 + i * col_w
        if i > 0:
            svg.append(f'<line x1="{kx:.1f}" y1="90" x2="{kx:.1f}" y2="130" stroke="#C8C0B0" stroke-width="0.8"/>')
        svg.append(f'<rect x="{kx+8:.1f}" y="91" width="20" height="11" rx="2" fill="{col}"/>')
        svg.append(f'<text x="{kx+18:.1f}" y="99" font-family="Liberation Sans" font-size="6.8" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{ref}</text>')
        svg.append(f'<text x="{kx+34:.1f}" y="106" font-family="TeX Gyre Heros Cn" font-size="20" font-weight="bold" fill="{col}">{esc(num)}</text>')
        svg.append(f'<text x="{kx+8:.1f}" y="118.5" font-family="Liberation Sans" font-size="7.6" font-weight="bold" fill="#111827">{esc(l1)}</text>')
        svg.append(f'<text x="{kx+8:.1f}" y="128.5" font-family="Liberation Sans" font-size="7.2" fill="#4B5563">{esc(l2)}</text>')

    # 4. Proportional 7-Region Bar (y=137..155, h=18)
    regions = [
        ("EUROPE · 8", 8, "#1B365D"),
        ("MIDDLE EAST · 5", 5, "#9E2A2B"),
        ("ASIA-PACIFIC · 8", 8, "#B45309"),
        ("AMERICAS · 5", 5, "#0F766E"),
        ("AFRICA · 3", 3, "#15803D"),
        ("OCEANIA · 3", 3, "#0369A1"),
        ("WORLD · 2", 2, "#4B5563"),
    ]
    total_r = sum(r[1] for r in regions)
    rx_cur = 14.0
    for r_label, r_count, r_col in regions:
        rw = 996.0 * (r_count / total_r)
        svg.append(f'<rect x="{rx_cur:.1f}" y="137" width="{rw:.1f}" height="18" fill="{r_col}"/>')
        svg.append(f'<text x="{rx_cur + rw/2:.1f}" y="148.8" font-family="Liberation Sans" font-size="7.3" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{esc(r_label)}</text>')
        rx_cur += rw

    # 5. Chronological UTC Timeline Bar (y=158..178, h=20)
    svg.append('<rect x="14" y="158" width="996" height="20" rx="2.5" fill="#14233C"/>')
    svg.append('<rect x="17" y="160.5" width="76" height="15" rx="2" fill="#9E2A2B"/>')
    svg.append('<text x="55" y="170.5" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="#FFFFFF" text-anchor="middle">THE DAY IN UTC</text>')
    utc_stops = [
        ("01:00", "HK polls (#7)"),
        ("05:30", "Vegas GP (#9)"),
        ("06:15", "186 drones (#2)"),
        ("12:15", "Seoul quits (#10)"),
        ("16:00", "COP31 no deal (#1)"),
        ("16:30", "LIV 4-0 MUN (#12)"),
        ("18:13", "US House 258 (#4)"),
        ("20:43", "Alcaraz ATP (#12)"),
    ]
    ux_start = 102.0
    ux_step = (1004.0 - ux_start) / len(utc_stops)
    for i, (utime, udesc) in enumerate(utc_stops):
        ux = ux_start + i * ux_step
        svg.append(f'<text x="{ux:.1f}" y="170.5" font-family="Liberation Sans" font-size="7.1" font-weight="bold" fill="#FBBF24">{esc(utime)}</text>')
        tw = measure_px(utime, "sans_bold", 7.1) + 3
        svg.append(f'<text x="{ux+tw:.1f}" y="170.5" font-family="Liberation Sans" font-size="7.0" fill="#E2E8F0">{esc(udesc)}</text>')

    # 6. Zone 1: 3 Hero Lead Cards (y=182..402, h=220)
    heroes = [
        {
            "num": 1,
            "kicker": "ANTALYA, TÜRKİYE · CLIMATE",
            "region": "WORLD",
            "status": "CONFIRMED",
            "headline": "COP31 collapses in Antalya with no deal after fossil-fuel deadlock",
            "body": "Nearly 200 nations end 44 hours of overtime without an accord after the EU and vulnerable states reject a draft that dropped the $120bn adaptation goal and omitted fossil-fuel phase-out.",
            "sources": "Reuters · BBC · AP · Al Jazeera (16:00 UTC)",
        },
        {
            "num": 2,
            "kicker": "KYIV REGION, UKRAINE · WAR",
            "region": "EUROPE",
            "status": "CONFIRMED",
            "headline": "Russia fires 186 drones overnight; five-storey Dymer block collapses",
            "body": "Ukraine's Air Force downs or jams 161 of 186 strike drones (72 jet-powered) across 18 sites. A hit collapses part of a five-storey apartment block in Dymer north of Kyiv, killing four.",
            "sources": "Ukrainian Air Force · Reuters · Kyiv Post (06:15 UTC)",
        },
        {
            "num": 3,
            "kicker": "RIFFA & SITRA, BAHRAIN · GULF",
            "region": "MIDDLE EAST",
            "status": "CLAIM",
            "headline": "Iran claims strikes on two US Patriot radars; Bahrain denies hits",
            "body": "Iran's IRGC claims via IRNA that missiles and drones struck two US Patriot radar arrays at Al-Riffa and Awali. Bahrain's Interior Ministry denies radar hits, reporting a Sitra site fire.",
            "sources": "IRNA (claim) · BNA / Reuters (denial)",
        },
    ]
    hero_w = 326.0
    hero_gap = 9.0
    hero_y = 182.0
    hero_h = 220.0
    for i, hcard in enumerate(heroes):
        hx = 14.0 + i * (hero_w + hero_gap)
        r_col = REGION_COLORS[hcard["region"]]
        b_bg, b_fg = BADGE_COLORS[hcard["status"]]
        svg.append(f'<rect x="{hx:.1f}" y="{hero_y}" width="{hero_w}" height="{hero_h}" rx="4" fill="#FFFFFF" stroke="#C8C0B0" stroke-width="1"/>')
        svg.append(draw_hero_illustration(hcard["num"], hx + 3, hero_y + 3, hero_w - 6, 94))

        # Kicker row (y = hero_y + 109)
        ky = hero_y + 111
        svg.append(f'<circle cx="{hx+13:.1f}" cy="{ky-3:.1f}" r="7.5" fill="{r_col}"/>')
        svg.append(f'<text x="{hx+13:.1f}" y="{ky-0.3:.1f}" font-family="Liberation Sans" font-size="8" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{hcard["num"]}</text>')
        svg.append(f'<text x="{hx+24:.1f}" y="{ky:.1f}" font-family="Liberation Sans" font-size="8" font-weight="bold" fill="{r_col}" letter-spacing="0.3">{esc(hcard["kicker"])}</text>')

        bw = measure_px(hcard["status"], "sans_bold", 7.2) + 10
        svg.append(f'<rect x="{hx+hero_w-bw-6:.1f}" y="{ky-9:.1f}" width="{bw:.1f}" height="12.5" rx="2.5" fill="{b_bg}"/>')
        svg.append(f'<text x="{hx+hero_w-6-bw/2:.1f}" y="{ky-0.2:.1f}" font-family="Liberation Sans" font-size="7.2" font-weight="bold" fill="{b_fg}" text-anchor="middle">{hcard["status"]}</text>')

        # 2-line Serif Headline
        h_lines = wrap_lines(hcard["headline"], "serif_bold", 12.8, hero_w - 16, 2)
        for li, line in enumerate(h_lines):
            svg.append(f'<text x="{hx+8:.1f}" y="{hero_y + 128 + li*14.5:.1f}" font-family="TeX Gyre Pagella" font-size="12.8" font-weight="bold" fill="#111827">{esc(line)}</text>')

        # 3-line Sans Summary
        b_lines = wrap_lines(hcard["body"], "sans_reg", 8.8, hero_w - 16, 3)
        for li, line in enumerate(b_lines):
            svg.append(f'<text x="{hx+8:.1f}" y="{hero_y + 160 + li*11.8:.1f}" font-family="Liberation Sans" font-size="8.8" fill="#27303F">{esc(line)}</text>')

        # Bottom source divider & text
        svg.append(f'<line x1="{hx+8:.1f}" y1="{hero_y+201:.1f}" x2="{hx+hero_w-8:.1f}" y2="{hero_y+201:.1f}" stroke="#E5E0D5" stroke-width="0.8"/>')
        svg.append(f'<text x="{hx+8:.1f}" y="{hero_y+213:.1f}" font-family="Liberation Sans" font-size="7.6" font-weight="bold" fill="#64748B">Sources: {esc(hcard["sources"])}</text>')

    # 7. Zone 2: 10 Secondary Illustrated Cards (#4–#13, 5x2 grid, y=407..751)
    secondaries = [
        {
            "num": 4, "region": "AMERICAS", "kicker": "WASHINGTON · US HOUSE", "status": "CONFIRMED",
            "tag_l": "US HOUSE · NC-5", "tag_r": "258 DEM SEATS",
            "headline": "Democrats reach 258 House seats after recount",
            "body": "AP projections after North Carolina's recount confirm Democrats won 258 of 435 House seats—their largest majority since 1992.",
            "sources": "AP · Washington Post",
        },
        {
            "num": 5, "region": "AFRICA", "kicker": "BENGHAZI · NAVAL WAR", "status": "CONFIRMED",
            "tag_l": "BENGHAZI PORT", "tag_r": "CORVETTE SUNK",
            "headline": "Russian corvette Merkury sinks in Libyan port",
            "body": "Satellite imagery and Libyan officials confirm Russia's Project 20380 corvette Merkury sank at Benghazi after sea-drone strikes.",
            "sources": "ISW · CBS News · Reuters",
        },
        {
            "num": 6, "region": "MIDDLE EAST", "kicker": "TEHRAN · ENERGY GRID", "status": "OFFICIAL",
            "tag_l": "TAVANIR UTILITY", "tag_r": "2-HR BLACKOUTS",
            "headline": "Iran begins scheduled two-hour daily power cuts",
            "body": "State utility Tavanir imposes rolling 2-hour blackouts across Tehran and major cities from 09:00–17:00 amid gas shortages.",
            "sources": "Tavanir · AFP · BBC",
        },
        {
            "num": 7, "region": "ASIA-PACIFIC", "kicker": "HONG KONG · ELECTIONS", "status": "OFFICIAL",
            "tag_l": "723 SEATS", "tag_r": "98.79% TURNOUT",
            "headline": "Hong Kong committee vote hits 98.79% turnout",
            "body": "Record 5,640 of 5,709 subsector voters cast ballots to choose 723 contested seats from 856 candidates on the 1,500-seat body.",
            "sources": "HK EAC · RTHK · Reuters",
        },
        {
            "num": 8, "region": "OCEANIA", "kicker": "WELLINGTON · CRICKET", "status": "OFFICIAL",
            "tag_l": "BASIN RESERVE", "tag_r": "INDIA 720/9d",
            "headline": "India declare on 720/9, their record total in NZ",
            "body": "Centuries by Rahul (136) and Pant (128) plus Gill's 98 lift India to 720/9 declared; New Zealand reach 119/2 at stumps.",
            "sources": "BCCI · ESPNcricinfo",
        },
        {
            "num": 9, "region": "AMERICAS", "kicker": "LAS VEGAS · FORMULA 1", "status": "OFFICIAL",
            "tag_l": "LAS VEGAS GP", "tag_r": "VERSTAPPEN +0.639S",
            "headline": "Verstappen edges Norris to win Las Vegas GP",
            "body": "Max Verstappen converts pole into his 75th F1 victory by 0.639s over Lando Norris under the Strip lights, with Piastri third.",
            "sources": "FIA · Formula 1 · Guardian",
        },
        {
            "num": 10, "region": "ASIA-PACIFIC", "kicker": "SEOUL · CABINET & MARKETS", "status": "CONFIRMED",
            "tag_l": "SEOUL CRISIS", "tag_r": "111 AI CASES",
            "headline": "Seoul minister quits over AI cheating; market fund set",
            "body": "Education Minister Choi Kyo-jin resigns over 111 AI exam cheating cases as Finance chiefs ready stock stabilization funds.",
            "sources": "Yonhap · MOFE · Korea.net",
        },
        {
            "num": 11, "region": "AFRICA", "kicker": "ITURI & KHARTOUM · CRISIS", "status": "CONFIRMED",
            "tag_l": "DRC & SUDAN", "tag_r": "EBOLA · 4 DEAD",
            "headline": "Clashes trap DRC Ebola medics; drones hit Khartoum",
            "body": "WHO pleads for truce as fighting traps staff at an Ituri Ebola hospital (11,613 cases); RSF drones kill four in Khartoum.",
            "sources": "WHO · Al Jazeera · AP",
        },
        {
            "num": 12, "region": "EUROPE", "kicker": "ANFIELD & TURIN · SPORT", "status": "OFFICIAL",
            "tag_l": "EPL & ATP FINALS", "tag_r": "LIV 4–0 · ALCARAZ",
            "headline": "Liverpool rout Man Utd 4–0; Alcaraz wins ATP Finals",
            "body": "Liverpool crush 10-man United 4–0 in Pochettino's debut after Yoro's red card; Carlos Alcaraz beats Zverev 6–2, 7–6(7) in Turin.",
            "sources": "Premier League · ATP · BBC",
        },
        {
            "num": 13, "region": "WORLD", "kicker": "VATICAN & SAN ANTONIO", "status": "CONFIRMED",
            "tag_l": "VATICAN & NBA", "tag_r": "1,300 · WEMBY 50",
            "headline": "Pope Leo XIV hosts 1,300 poor; Wembanyama scores 50",
            "body": "Pope Leo XIV hosts 1,300 guests for World Day of the Poor, while Victor Wembanyama posts 50 pts and 19 reb in a Spurs win.",
            "sources": "Vatican News · NBA · AP",
        },
    ]
    sec_w = 192.0
    sec_h = 168.0
    sec_gap_x = 9.0
    sec_gap_y = 7.0
    sec_y0 = 407.0
    for idx_s, scard in enumerate(secondaries):
        row = idx_s // 5
        col = idx_s % 5
        sx = 14.0 + col * (sec_w + sec_gap_x)
        sy = sec_y0 + row * (sec_h + sec_gap_y)
        r_col = REGION_COLORS[scard["region"]]
        b_bg, b_fg = BADGE_COLORS[scard["status"]]

        svg.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sec_w}" height="{sec_h}" rx="3.5" fill="#FFFFFF" stroke="#C8C0B0" stroke-width="0.9"/>')
        svg.append(draw_secondary_illustration(scard["num"], sx + 2.5, sy + 2.5, sec_w - 5, 62, scard["tag_l"], scard["tag_r"]))

        # Kicker & status row (sy + 76)
        ky = sy + 76
        svg.append(f'<circle cx="{sx+11:.1f}" cy="{ky-2.5:.1f}" r="6.2" fill="{r_col}"/>')
        svg.append(f'<text x="{sx+11:.1f}" y="{ky-0.2:.1f}" font-family="Liberation Sans" font-size="6.8" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{scard["num"]}</text>')
        svg.append(f'<text x="{sx+19.5:.1f}" y="{ky:.1f}" font-family="Liberation Sans" font-size="6.7" font-weight="bold" fill="{r_col}">{esc(scard["kicker"])}</text>')

        bw = measure_px(scard["status"], "sans_bold", 6.2) + 8
        svg.append(f'<rect x="{sx+sec_w-bw-4:.1f}" y="{ky-8:.1f}" width="{bw:.1f}" height="11" rx="2" fill="{b_bg}"/>')
        svg.append(f'<text x="{sx+sec_w-4-bw/2:.1f}" y="{ky-0.3:.1f}" font-family="Liberation Sans" font-size="6.2" font-weight="bold" fill="{b_fg}" text-anchor="middle">{scard["status"]}</text>')

        # 2-line Bold Serif Headline
        h_lines = wrap_lines(scard["headline"], "serif_bold", 10.2, sec_w - 12, 2)
        for li, line in enumerate(h_lines):
            svg.append(f'<text x="{sx+6:.1f}" y="{sy + 90 + li*11.8:.1f}" font-family="TeX Gyre Pagella" font-size="10.2" font-weight="bold" fill="#111827">{esc(line)}</text>')

        # 3-line Sans Summary
        b_lines = wrap_lines(scard["body"], "sans_reg", 7.8, sec_w - 12, 3)
        for li, line in enumerate(b_lines):
            svg.append(f'<text x="{sx+6:.1f}" y="{sy + 116 + li*10.2:.1f}" font-family="Liberation Sans" font-size="7.8" fill="#27303F">{esc(line)}</text>')

        # Bottom source line
        svg.append(f'<line x1="{sx+6:.1f}" y1="{sy+153:.1f}" x2="{sx+sec_w-6:.1f}" y2="{sy+153:.1f}" stroke="#E5E0D5" stroke-width="0.7"/>')
        svg.append(f'<text x="{sx+6:.1f}" y="{sy+163:.1f}" font-family="Liberation Sans" font-size="7.0" font-weight="bold" fill="#64748B">{esc(scard["sources"])}</text>')

    # 8. Zone 3: Bottom Split (y=756..948, h=192)
    # Left: Pin-Indexed World Map (x=14..324, w=310, h=192)
    svg.append(draw_world_map(14, 756, 310, 192))

    # Right: 21 Wire Briefs (#14–#34) in 3 columns (x=332..1010, w=678, h=192)
    bx, by, bw, bh = 332.0, 756.0, 678.0, 192.0
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="4" fill="#FFFFFF" stroke="#C8C0B0" stroke-width="1"/>')
    svg.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="18" rx="4" fill="#1B365D"/>')
    svg.append(f'<text x="{bx+8}" y="{by+12.5}" font-family="Liberation Sans" font-size="7.8" font-weight="bold" fill="#FFFFFF" letter-spacing="0.4">ALSO ON SUNDAY 22 NOVEMBER 2026 — 21 MORE DATED DISPATCHES (#14–#34)</text>')
    svg.append(f'<text x="{bx+bw-8}" y="{by+12.5}" font-family="Liberation Sans" font-size="6.8" font-weight="bold" fill="#FDE68A" text-anchor="end">Every item dated 22 Nov 2026 · Tagged by region, certainty &amp; wire</text>')

    briefs = [
        # Col 1 (14..20)
        (14, "EUROPE", "FI · Finland", "Ship Sparta II towed burning", "16 crew rescued off Loviisa after drone hit (Yle/Reuters)", "CONFIRMED"),
        (15, "MIDDLE EAST", "PS · Gaza City", "Strike hits aid truck; 4 dead", "Hamas seeks urgent mediator talks after blast (AP/AJ)", "REPORTED"),
        (16, "MIDDLE EAST", "SA · Rabigh", "Houthis claim refinery strike", "Drone attacks claimed on Petrol Rabigh & Riyadh (ISW)", "CLAIM"),
        (17, "MIDDLE EAST", "IL · Jerusalem", "Likud–Eisenkot talks stall", "Coalition bloc stuck at 48 seats, 13 short (AP/Haaretz)", "CONFIRMED"),
        (18, "EUROPE", "PT · Portimão", "Márquez wins 8th MotoGP title", "Ties Giacomo Agostini's all-time premier record (AFP)", "OFFICIAL"),
        (19, "ASIA-PACIFIC", "IN · New Delhi", "Nepal PM Balendra Shah visits", "Starts 2-day state visit for talks with PM Modi (Hindu)", "OFFICIAL"),
        (20, "EUROPE", "EE · Tallinn", "Estonia shuts 5 Russia posts", "Total closure begins 1 Dec after sabotage bid (ERR)", "OFFICIAL"),
        # Col 2 (21..27)
        (21, "ASIA-PACIFIC", "ID · Cikande", "Candy factory fire: 3 dead", "Sunday crews pull 24 body bags; 36 missing (Antara)", "CONFIRMED"),
        (22, "ASIA-PACIFIC", "IN · Manipur", "Toxic liquor toll hits 19 dead", "Around 600 hospitalized across state Sunday (PTI/BBC)", "CONFIRMED"),
        (23, "AMERICAS", "BR · Brasília", "Bolsonaro (71) remains in ICU", "Stable in intensive care for bowel obstruction (Reuters)", "REPORTED"),
        (24, "OCEANIA", "AU · Canberra", "Marles rejects AUKUS report", "Defence Minister defends nuclear sub timeline (ABC)", "OFFICIAL"),
        (25, "EUROPE", "BE · Brussels", "Air staff join Monday strike", "24-hour Belgian walkout grounds Brussels flights (Belga)", "CONFIRMED"),
        (26, "EUROPE", "UA · Zaporizhzhia", "Guided bombs injure child", "Zelensky urges US PURL Patriot transfer (Ukrinform)", "CONFIRMED"),
        (27, "ASIA-PACIFIC", "QA · Doha", "Pakistan A beat India A by 48", "Rising Stars Asia Cup win despite Varma 100 (Express)", "OFFICIAL"),
        # Col 3 (28..34)
        (28, "AMERICAS", "US · Nationwide", "Delta outage delays 1,000+", "Automation glitch disrupts holiday flights (AP/FAA)", "CONFIRMED"),
        (29, "AMERICAS", "US · Florida", "Trump hosts $TRUMP dinner", "Pitches crypto as US strategic edge over China (AJ/AP)", "REPORTED"),
        (30, "ASIA-PACIFIC", "ID · West Java", "7th Peparda Paralympics open", "Over 1,600 athletes compete in regional opener (Antara)", "OFFICIAL"),
        (31, "MIDDLE EAST", "KW · Kuwait", "Air defense downs stray drone", "Intercept reported near northern maritime zone (KUNA)", "REPORTED"),
        (32, "MIDDLE EAST", "PS · West Bank", "Eisenkot slams settler arson", "Calls West Bank arson wave 'Jewish terrorism' (AP)", "CONFIRMED"),
        (33, "OCEANIA", "ID · EU–Jakarta", "98.5% tariff-cut annex out", "Sunday schedule covers bilateral goods trade (EC/Reuters)", "OFFICIAL"),
        (34, "EUROPE", "RU · Kursk/Belgorod", "Moscow claims 42 drones shot", "Russian MoD reports overnight border intercepts (TASS)", "CLAIM"),
    ]

    b_col_w = bw / 3.0
    b_row_h = (bh - 22.0) / 7.0
    for idx_b, (bnum, breg, bloc, bhead, bsub, bstat) in enumerate(briefs):
        c_idx = idx_b // 7
        r_idx = idx_b % 7
        cx_b = bx + c_idx * b_col_w
        cy_b = by + 20.0 + r_idx * b_row_h
        if c_idx > 0 and r_idx == 0:
            svg.append(f'<line x1="{cx_b:.1f}" y1="{by+20}" x2="{cx_b:.1f}" y2="{by+bh-3}" stroke="#E5E0D5" stroke-width="0.8"/>')
        if r_idx > 0:
            svg.append(f'<line x1="{cx_b+4:.1f}" y1="{cy_b:.1f}" x2="{cx_b+b_col_w-4:.1f}" y2="{cy_b:.1f}" stroke="#F1EFEA" stroke-width="0.7"/>')

        r_col = REGION_COLORS[breg]
        s_bg, s_fg = BADGE_COLORS[bstat]
        # Number box
        svg.append(f'<rect x="{cx_b+5:.1f}" y="{cy_b+2.5:.1f}" width="14" height="10" rx="2" fill="{r_col}"/>')
        svg.append(f'<text x="{cx_b+12:.1f}" y="{cy_b+9.8:.1f}" font-family="Liberation Sans" font-size="6.4" font-weight="bold" fill="#FFFFFF" text-anchor="middle">{bnum}</text>')

        # Status badge on right
        sw = measure_px(bstat, "sans_bold", 5.5) + 6
        svg.append(f'<rect x="{cx_b+b_col_w-sw-5:.1f}" y="{cy_b+2.5:.1f}" width="{sw:.1f}" height="9.5" rx="1.8" fill="{s_bg}"/>')
        svg.append(f'<text x="{cx_b+b_col_w-5-sw/2:.1f}" y="{cy_b+9.2:.1f}" font-family="Liberation Sans" font-size="5.5" font-weight="bold" fill="{s_fg}" text-anchor="middle">{bstat}</text>')

        # Headline line (verify single-line fit!)
        full_head = f"{bloc}: {bhead}"
        avail_w = b_col_w - 23 - sw
        if measure_px(full_head, "sans_bold", 6.7) > avail_w:
            raise ValueError(f"Brief #{bnum} headline too wide ({measure_px(full_head, 'sans_bold', 6.7):.1f} > {avail_w:.1f}): {full_head}")
        svg.append(f'<text x="{cx_b+21:.1f}" y="{cy_b+10:.1f}" font-family="Liberation Sans" font-size="6.7" font-weight="bold" fill="#111827">{esc(full_head)}</text>')

        # Sub-line (verify single-line fit!)
        if measure_px(bsub, "sans_reg", 6.5) > b_col_w - 10:
            raise ValueError(f"Brief #{bnum} subline too wide ({measure_px(bsub, 'sans_reg', 6.5):.1f} > {b_col_w-10:.1f}): {bsub}")
        svg.append(f'<text x="{cx_b+6:.1f}" y="{cy_b+20:.1f}" font-family="Liberation Sans" font-size="6.5" fill="#4B5563">{esc(bsub)}</text>')

    # 9. Zone 4: Red-Bordered DATE CHECK Audit Box (y=952..1001, h=49)
    svg.append('<rect x="14" y="952" width="996" height="49" rx="3.5" fill="#FEF2F2" stroke="#9E2A2B" stroke-width="1.3"/>')
    svg.append('<rect x="18" y="956" width="84" height="41" rx="2.5" fill="#9E2A2B"/>')
    svg.append('<text x="60" y="974" font-family="Liberation Sans" font-size="8.5" font-weight="bold" fill="#FFFFFF" text-anchor="middle">DATE CHECK</text>')
    svg.append('<text x="60" y="984.5" font-family="Liberation Sans" font-size="6.5" font-weight="bold" fill="#FDE68A" text-anchor="middle">22 NOV 2026 UTC</text>')
    svg.append('<text x="60" y="993" font-family="Liberation Sans" font-size="6.0" fill="#FEE2E2" text-anchor="middle">STRICT 24H GATE</text>')

    dc1 = "INCLUDED (SUN 22 NOV 2026 ONLY): All 34 stories happened or were first reported on 22 Nov 2026 (UTC) — including tonight's 186-drone barrage on Ukraine (161 downed, Dymer block), COP31's collapse, US House 258th seat, and India's 720/9."
    dc2 = "EXCLUDED AS OTHER DAYS' NEWS: 400-drone / 110-missile Ukraine barrage (Thu 19–Fri 20 Nov) · 148-drone Kryvyi Rih strike (Fri 20–Sat 21 Nov) · 'El Chapo Isidro' Sinaloa capture (Fri 20 Nov) · Bayelsa boat capsizing, 24 dead (Fri 20 Nov) · Peru M6.7 quake (Fri 20 Nov)."
    dc3 = "ALSO EXCLUDED (PRE-22 NOV): Nvidia SEC probe (Fri 20 Nov) · BepiColombo Mercury orbit burn (Sat 21 Nov) · FBI $400m N. Korea crypto hack attribution (2022 / Feb 2025). Single-party military assertions (#3 Bahrain radars, #16 Rabigh, #34 Kursk) are tagged CLAIM."
    for d_str in (dc1, dc2, dc3):
        if measure_px(d_str, "sans_bold", 6.6) > 896:
            raise ValueError(f"Date check line too wide ({measure_px(d_str, 'sans_bold', 6.6):.1f} > 896): {d_str}")

    svg.append(f'<text x="108" y="965.5" font-family="Liberation Sans" font-size="6.6" font-weight="bold" fill="#7F1D1D">{esc(dc1)}</text>')
    svg.append(f'<text x="108" y="979.5" font-family="Liberation Sans" font-size="6.6" fill="#1F2937">{esc(dc2)}</text>')
    svg.append(f'<text x="108" y="993.5" font-family="Liberation Sans" font-size="6.6" fill="#1F2937">{esc(dc3)}</text>')

    # 10. Bottom Colophon Strip (y=1004..1024, h=20)
    svg.append('<rect x="0" y="1004" width="1024" height="20" fill="#0F1E36"/>')
    svg.append('<text x="14" y="1016.5" font-family="Liberation Sans" font-size="7.0" font-weight="bold" fill="#CBD5E1">WIRE SOURCES: Reuters · AP · BBC · AFP · Al Jazeera · Ukrinform · IRNA · BNA · WHO · FIA · BCCI · ATP · HK EAC</text>')
    svg.append('<text x="1010" y="1016.5" font-family="Liberation Sans" font-size="7.0" font-weight="bold" fill="#FBBF24" text-anchor="end">CERTAINTY: CONFIRMED (2+ wires) · OFFICIAL (record) · REPORTED (wire) · CLAIM (1 side)</text>')

    svg.append("</svg>")
    return "\n".join(svg)

def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(out_dir, "master.svg")
    png_path = os.path.join(out_dir, "entry.png")

    svg_content = build_svg()
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    # Render at 2048x2048 via rsvg-convert for 2x supersampled anti-aliasing, then downsample to 1024x1024
    raw_2x = subprocess.check_output(
        ["rsvg-convert", "-w", "2048", "-h", "2048"],
        input=svg_content.encode("utf-8"),
    )
    from io import BytesIO
    im_2x = Image.open(BytesIO(raw_2x)).convert("RGB")
    im_1x = im_2x.resize((1024, 1024), Image.Resampling.LANCZOS)

    # Save deterministic PNG (check if full RGB fits <= 1,048,576 bytes)
    buf = BytesIO()
    im_1x.save(buf, format="PNG", optimize=True, compress_level=9)
    png_bytes = buf.getvalue()
    if len(png_bytes) > 1048576:
        # Quantize deterministically to 256 colors if needed
        im_q = im_1x.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        buf = BytesIO()
        im_q.save(buf, format="PNG", optimize=True, compress_level=9)
        png_bytes = buf.getvalue()

    with open(png_path, "wb") as f:
        f.write(png_bytes)

    md5_hex = hashlib.md5(png_bytes).hexdigest()
    sha256_hex = hashlib.sha256(png_bytes).hexdigest()
    print(f"Built {png_path}: 1024x1024, {len(png_bytes)} bytes ({len(png_bytes)/1024:.1f} KiB), md5={md5_hex}, sha256={sha256_hex[:16]}")

if __name__ == "__main__":
    main()
