"""Parchment background: warm base, soft mottling, fine grain, gentle vignette (JPEG bytes)."""
import io

import numpy as np
from PIL import Image

from . import tokens as T


def _noise(rng, w, h, cell):
    """Smooth value noise: random grid of size (w/cell, h/cell) upsampled bicubically."""
    gw, gh = max(2, int(w / cell) + 2), max(2, int(h / cell) + 2)
    g = rng.standard_normal((gh, gw)).astype(np.float32)
    im = Image.fromarray(g, mode='F').resize((w, h), Image.BICUBIC)
    a = np.asarray(im, dtype=np.float32)
    return (a - a.mean()) / (a.std() + 1e-6)


def parchment(w=2560, h=1440, seed=7, base=None, strength=1.0, vignette=1.0):
    rng = np.random.default_rng(seed)
    base = np.frombuffer(bytes.fromhex(base or T.PAPER), dtype=np.uint8).astype(np.float32)
    lum = (1.5 * _noise(rng, w, h, 420) + 1.0 * _noise(rng, w, h, 130) + 0.55 * _noise(rng, w, h, 32)
           + 0.35 * _noise(rng, w, h, 7)) * strength
    grain = rng.standard_normal((h, w)).astype(np.float32) * 0.9 * strength
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2) / np.sqrt(2)
    vig = -(r ** 2.6) * 10.0 * vignette
    v = lum + grain + vig                        # levels, negative = darker
    warm = np.array([1.0, 0.93, 0.80], dtype=np.float32)   # darker paper turns ochre, not grey
    img = base[None, None, :] + v[..., None] * warm[None, None, :]
    img = np.clip(img, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(img, 'RGB').save(buf, 'JPEG', quality=90, subsampling=0, optimize=True)
    return buf.getvalue()
