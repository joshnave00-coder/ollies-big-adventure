"""
art.py — shared rendering toolkit (added in the 0.3 graphics overhaul).

Pure presentation only: anti-aliased drawing primitives, CC0 image loading/caching,
gradients, soft shadows, recolouring and tiling helpers.  NO gameplay logic lives
here, and nothing here imports game/level/player — it is a leaf module like
constants.py so any drawing code can use it freely.

Two things this module gives the rest of the project:

1.  `aadraw` — a drop-in replacement for `pygame.draw` whose circle/ellipse/polygon/
    line calls are anti-aliased (via pygame.gfxdraw).  Swapping `pygame.draw` →
    `aadraw` in the character/furniture draw code removes the jagged edges that made
    the hand-drawn art look rough, without changing any shapes or coordinates.

2.  Stock-art helpers (`image`, `scaled`, `scaled_h`, `tinted`, …) that load the
    curated CC0 Kenney art under assets/img/ once and cache the scaled results, plus
    `vgradient` / `soft_shadow` for cheap depth and grounding.
"""

import os
import math
import functools

import pygame
import pygame.gfxdraw as gfx

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "img")


# --------------------------------------------------------------------------- #
# Colour sanitising — gfxdraw needs integer 0..255 components
# --------------------------------------------------------------------------- #
def _col(color):
    return tuple(max(0, min(255, int(c))) for c in color)


def shade(color, factor):
    """Multiply an RGB(A) colour by `factor` (e.g. 0.8 = darker, 1.2 = lighter)."""
    out = [max(0, min(255, int(c * factor))) for c in color[:3]]
    if len(color) == 4:
        out.append(color[3])
    return tuple(out)


def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# --------------------------------------------------------------------------- #
# Anti-aliased drawing — same call signatures as pygame.draw
# --------------------------------------------------------------------------- #
class _AADraw:
    """Drop-in for pygame.draw with anti-aliased fills/outlines.

    Supports the subset the project uses: circle, ellipse, polygon, line, rect,
    arc.  `width=0` (the default) means a filled shape; `width>0` an outline.
    """

    def circle(self, surf, color, center, radius, width=0):
        x, y, r = int(center[0]), int(center[1]), int(radius)
        if r < 1:
            return
        c = _col(color)
        if width <= 0:
            gfx.filled_circle(surf, x, y, r, c)
            gfx.aacircle(surf, x, y, r, c)
        else:
            for rr in range(r, max(0, r - width), -1):
                gfx.aacircle(surf, x, y, rr, c)

    def ellipse(self, surf, color, rect, width=0):
        x, y, w, h = rect
        cx, cy = int(x + w / 2), int(y + h / 2)
        rx, ry = max(1, int(w / 2)), max(1, int(h / 2))
        c = _col(color)
        if width <= 0:
            gfx.filled_ellipse(surf, cx, cy, rx, ry, c)
            gfx.aaellipse(surf, cx, cy, rx, ry, c)
        else:
            gfx.aaellipse(surf, cx, cy, rx, ry, c)

    def polygon(self, surf, color, points, width=0):
        pts = [(int(px), int(py)) for px, py in points]
        c = _col(color)
        if len(pts) < 3:
            if len(pts) == 2:
                self.line(surf, color, pts[0], pts[1], max(1, width))
            return
        if width <= 0:
            gfx.filled_polygon(surf, pts, c)
            gfx.aapolygon(surf, pts, c)
        else:
            gfx.aapolygon(surf, pts, c)

    def line(self, surf, color, p1, p2, width=1):
        c = _col(color)
        x1, y1, x2, y2 = int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1])
        if width <= 1:
            gfx.line(surf, x1, y1, x2, y2, c)
            return
        # Thick line as an anti-aliased quad
        dx, dy = x2 - x1, y2 - y1
        ln = math.hypot(dx, dy)
        if ln == 0:
            self.circle(surf, color, p1, width / 2)
            return
        nx, ny = -dy / ln * width / 2, dx / ln * width / 2
        self.polygon(surf, color,
                     [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny),
                      (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)])

    def lines(self, surf, color, closed, points, width=1):
        pts = [(int(p[0]), int(p[1])) for p in points]
        for i in range(len(pts) - 1):
            self.line(surf, color, pts[i], pts[i + 1], width)
        if closed and len(pts) > 2:
            self.line(surf, color, pts[-1], pts[0], width)

    def aaline(self, surf, color, p1, p2, blend=1):
        gfx.line(surf, int(p1[0]), int(p1[1]), int(p2[0]), int(p2[1]), _col(color))

    def rect(self, surf, color, rect, width=0, border_radius=0):
        pygame.draw.rect(surf, color, rect, width, border_radius=border_radius)

    def arc(self, surf, color, rect, a0, a1, width=1):
        pygame.draw.arc(surf, color, rect, a0, a1, width)


aadraw = _AADraw()


# --------------------------------------------------------------------------- #
# Image loading / scaling (CC0 Kenney art under assets/img/)
# --------------------------------------------------------------------------- #
def _convert(surf):
    if pygame.display.get_surface() is not None:
        return surf.convert_alpha()
    return surf


@functools.lru_cache(maxsize=None)
def image(rel):
    """Load assets/img/<rel> once (rel uses forward slashes)."""
    path = os.path.join(ASSET_DIR, *rel.split("/"))
    return _convert(pygame.image.load(path))


@functools.lru_cache(maxsize=None)
def scaled(rel, w, h):
    return pygame.transform.smoothscale(image(rel), (int(w), int(h)))


@functools.lru_cache(maxsize=None)
def scaled_h(rel, h):
    img = image(rel)
    w0, h0 = img.get_size()
    w = max(1, int(round(w0 * h / h0)))
    return pygame.transform.smoothscale(img, (w, int(h)))


@functools.lru_cache(maxsize=None)
def scaled_w(rel, w):
    img = image(rel)
    w0, h0 = img.get_size()
    h = max(1, int(round(h0 * w / w0)))
    return pygame.transform.smoothscale(img, (int(w), h))


@functools.lru_cache(maxsize=None)
def tinted(rel, color, h=None):
    """Recolour an image by multiplying with `color`.  Great for turning the
    pale CC0 hill/pattern silhouettes into palette-matched layers.  Optionally
    scale to height `h` first."""
    img = scaled_h(rel, h) if h else image(rel)
    t = img.copy()
    mult = color if len(color) == 4 else (color[0], color[1], color[2], 255)
    t.fill(mult, special_flags=pygame.BLEND_RGBA_MULT)
    return t


@functools.lru_cache(maxsize=None)
def sprite(rel, h, flip=False):
    """A character/prop sprite scaled to pixel height `h`, optionally flipped
    horizontally for facing.  Cached by (rel, h, flip)."""
    img = scaled_h(rel, int(h))
    if flip:
        img = pygame.transform.flip(img, True, False)
    return img


def blit_sprite(surf, rel, cx, feet_y, h, flip=False, shadow=True, shadow_alpha=70):
    """Blit a sprite centred at x=`cx` with its feet on `feet_y`, scaled to
    height `h`.  Adds a soft contact shadow first unless `shadow=False`."""
    img = sprite(rel, h, flip)
    if shadow:
        ground_shadow(surf, cx, feet_y, max(20, img.get_width() - 8), 12, shadow_alpha)
    surf.blit(img, (int(cx - img.get_width() / 2), int(feet_y - img.get_height())))
    return img


def exists(rel):
    return os.path.isfile(os.path.join(ASSET_DIR, *rel.split("/")))


# --------------------------------------------------------------------------- #
# Gradients & shadows
# --------------------------------------------------------------------------- #
@functools.lru_cache(maxsize=None)
def vgradient(width, height, top, bottom):
    """Cached vertical gradient surface from `top` colour to `bottom`."""
    s = pygame.Surface((width, height)).convert() if pygame.display.get_surface() else pygame.Surface((width, height))
    for y in range(height):
        t = y / max(1, height - 1)
        pygame.draw.line(s, lerp_color(top, bottom, t), (0, y), (width, y))
    return s


@functools.lru_cache(maxsize=None)
def soft_shadow(width, height, alpha=80):
    """Soft elliptical shadow (transparent), darkest in the middle."""
    s = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width / 2, height / 2
    layers = 7
    for i in range(layers, 0, -1):
        f = i / layers
        a = int(alpha * (1.0 - f) + alpha * 0.18)
        rx, ry = max(1, int(width / 2 * f)), max(1, int(height / 2 * f))
        gfx.filled_ellipse(s, int(cx), int(cy), rx, ry, (0, 0, 0, a))
    return s


def ground_shadow(surf, cx, cy, w, h=None, alpha=80):
    """Blit a soft contact shadow centred at (cx, cy) — call before drawing a sprite."""
    if h is None:
        h = max(6, w // 3)
    sh = soft_shadow(int(w), int(h), alpha)
    surf.blit(sh, (int(cx - w / 2), int(cy - h / 2)))


@functools.lru_cache(maxsize=2048)
def _panel_overlay(w, h, radius):
    """Cached rounded shading overlay: light at the top, dark at the bottom,
    clipped to a rounded rectangle.  Turns a flat fill into a moulded surface."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        if t < 0.5:
            s_col = (255, 255, 255, int(70 * (0.5 - t) * 2))
        else:
            s_col = (0, 0, 0, int(55 * (t - 0.5) * 2))
        pygame.draw.line(s, s_col, (0, i), (w, i))
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def panel(surf, rect, color, radius=8, shadow=True, outline=None, gloss=True):
    """Draw a piece of furniture/UI as a rounded, gradient-shaded block with a
    soft drop shadow — the workhorse that makes flat shapes look illustrated."""
    x, y, w, h = (int(v) for v in rect)
    if w < 3 or h < 3:
        pygame.draw.rect(surf, color, rect, border_radius=max(0, radius))
        return
    if shadow:
        sh = soft_shadow(w + 12, max(8, int(h * 0.20)), 75)
        surf.blit(sh, (x - 6, y + h - int(h * 0.05)))
    pygame.draw.rect(surf, color, (x, y, w, h), border_radius=radius)
    surf.blit(_panel_overlay(w, h, radius), (x, y))
    if gloss:
        gh = max(2, h // 7)
        pygame.draw.rect(surf, shade(color, 1.18), (x + 3, y + 2, w - 6, gh),
                         border_radius=max(2, radius - 2))
        surf.blit(_panel_overlay(w - 6, gh, max(2, radius - 2)), (x + 3, y + 2))
    if outline:
        pygame.draw.rect(surf, outline, (x, y, w, h), 2, border_radius=radius)


@functools.lru_cache(maxsize=None)
def radial_glow(radius, color, max_alpha=90):
    """Soft circular glow surface (for lamps, hot hazards, magic, etc.)."""
    d = radius * 2
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        f = r / radius
        a = int(max_alpha * (1 - f) ** 1.4)
        gfx.filled_circle(s, radius, radius, r, (color[0], color[1], color[2], a))
    return s
