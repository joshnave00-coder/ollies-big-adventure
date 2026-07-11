"""
Programmatic sound generation for Ollie's Big Adventure.
All sounds are synthesised at runtime using Python's built-in `array` module —
no external audio files required.

To swap in a real audio file later, replace the corresponding _build(...) call
in SoundManager._build_all() with:
    s['key'] = pygame.mixer.Sound("assets/sounds/myfile.wav")

Mixer must already be initialised (main.py does this) before SoundManager().
"""

import pygame
import math
import array
import random

# Must match main.py: pygame.mixer.init(frequency=44100, size=-16, channels=2)
_SR = 44100


# ─────────────────────────────────────────────────────────────────────────────
# Low-level helpers
# ─────────────────────────────────────────────────────────────────────────────

def _env(i, n, atk=0.08, rel=0.25):
    """Attack-release amplitude envelope — returns scalar in [0.0, 1.0]."""
    if n <= 1:
        return 1.0
    t = i / (n - 1)
    if t < atk:
        return t / atk
    if t > 1.0 - rel:
        return (1.0 - t) / rel
    return 1.0


def _build(samples_iter, vol=0.30):
    """
    Convert an iterable of float samples (≈ ±1.0) into a stereo pygame.Sound.
    `vol` scales the peak amplitude (0.0–1.0).  A real .wav could replace this
    entire call — see module docstring.
    """
    samples = list(samples_iter)
    n = len(samples)
    # Interleaved stereo 16-bit signed PCM
    buf = array.array('h', [0] * (n * 2))
    for i, s in enumerate(samples):
        val = int(max(-1.0, min(1.0, s * vol)) * 32767)
        buf[i * 2]     = val   # left
        buf[i * 2 + 1] = val   # right
    return pygame.mixer.Sound(buffer=buf)


# ─────────────────────────────────────────────────────────────────────────────
# Waveform generators  (all yield float samples)
# ─────────────────────────────────────────────────────────────────────────────

def _sine(freq, dur, atk=0.08, rel=0.25):
    n = int(_SR * dur)
    for i in range(n):
        t = i / _SR
        yield math.sin(2 * math.pi * freq * t) * _env(i, n, atk, rel)


def _sine_sweep(f0, f1, dur, atk=0.05, rel=0.30):
    """Linear frequency sweep from f0 to f1."""
    n = int(_SR * dur)
    for i in range(n):
        t  = i / _SR
        fq = f0 + (f1 - f0) * (i / n)
        yield math.sin(2 * math.pi * fq * t) * _env(i, n, atk, rel)


def _buzz(freq, dur):
    """Odd-harmonic square-wave approximation — low, grating buzzer."""
    n    = int(_SR * dur)
    amps = [1.0, 1 / 3, 1 / 5, 1 / 7]
    norm = sum(amps)
    for i in range(n):
        t = i / _SR
        s = sum(a * math.sin(2 * math.pi * freq * (2 * k + 1) * t)
                for k, a in enumerate(amps)) / norm
        yield s * _env(i, n, atk=0.01, rel=0.35)


def _tremolo_sine(freq, dur, trem_rate=22):
    """Sine wave whose amplitude oscillates — gives a bubbly, watery feel."""
    n = int(_SR * dur)
    for i in range(n):
        t    = i / _SR
        trem = 0.55 + 0.45 * math.sin(2 * math.pi * trem_rate * t)
        yield math.sin(2 * math.pi * freq * t) * trem * _env(i, n)


def _flutter(dur):
    """Rapid wobbling pitch — bird-wing flutter, accelerating slightly."""
    n = int(_SR * dur)
    for i in range(n):
        t          = i / _SR
        wobble_hz  = 32 + 20 * (i / n)   # speeds up as bird is caught
        fq         = 700 + 320 * math.sin(2 * math.pi * wobble_hz * t)
        yield math.sin(2 * math.pi * fq * t) * _env(i, n, atk=0.02, rel=0.28)


def _click(dur=0.045):
    """Short white-noise burst — percussive pop."""
    n = int(_SR * dur)
    for i in range(n):
        yield random.uniform(-1.0, 1.0) * _env(i, n, atk=0.01, rel=0.70)


def _whoosh(dur):
    """Descending sine + noise mix — hot-slide whoosh."""
    n = int(_SR * dur)
    for i in range(n):
        t     = i / _SR
        fq    = 780 - 560 * (i / n)
        sine  = math.sin(2 * math.pi * fq * t)
        noise = random.uniform(-0.4, 0.4)
        yield (sine * 0.62 + noise * 0.38) * _env(i, n, atk=0.04, rel=0.38)


def _hum_sweep(f0, f1, dur):
    """Rising sine with a soft second harmonic — engine-like hum."""
    n = int(_SR * dur)
    for i in range(n):
        t  = i / _SR
        fq = f0 + (f1 - f0) * ((i / n) ** 1.6)   # accelerating rise
        s  = (math.sin(2 * math.pi * fq * t)
              + 0.28 * math.sin(4 * math.pi * fq * t))
        yield s * _env(i, n, atk=0.12, rel=0.15) / 1.28


def _concat(*iters):
    """Chain multiple generators end-to-end."""
    for it in iters:
        yield from it


def _silence(dur):
    for _ in range(int(_SR * dur)):
        yield 0.0


# ─────────────────────────────────────────────────────────────────────────────
# SoundManager
# ─────────────────────────────────────────────────────────────────────────────

class SoundManager:
    """
    Builds all sounds at construction time and exposes named play_*() methods.
    Call toggle() or set .enabled to mute/unmute without reloading sounds.
    """

    def __init__(self):
        self.enabled = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        try:
            self._build_all()
        except Exception:
            # If synthesis fails (e.g. mixer not ready), run silently
            self.enabled = False

    def _build_all(self):
        s = self._sounds

        # ── short upward ding — generic score / pet ──────────────────────
        s['score'] = _build(_sine_sweep(440, 880, 0.18), vol=0.26)

        # ── two-tone happy chirp — treat collected ────────────────────────
        s['treat'] = _build(_concat(
            _sine(900, 0.10, atk=0.04, rel=0.20),
            _silence(0.022),
            _sine(1150, 0.13, atk=0.04, rel=0.30),
        ), vol=0.26)

        # ── flutter then pop — bird caught ────────────────────────────────
        s['bird'] = _build(_concat(
            _flutter(0.17),
            _silence(0.018),
            _click(0.048),
        ), vol=0.24)

        # ── low buzzer / thud — enemy damages Ollie ───────────────────────
        s['enemy_hit'] = _build(_buzz(130, 0.26), vol=0.28)

        # ── soft ascending 4-note chime — angel appears ───────────────────
        s['angel'] = _build(_concat(
            _sine(523,  0.12, rel=0.30),
            _sine(659,  0.12, rel=0.30),
            _sine(784,  0.12, rel=0.30),
            _sine(1047, 0.22, rel=0.40),
        ), vol=0.20)

        # ── bubbly blip — water bottle collected ──────────────────────────
        s['water'] = _build(_concat(
            _tremolo_sine(880, 0.10, trem_rate=28),
            _sine_sweep(900, 1250, 0.13, atk=0.04, rel=0.30),
        ), vol=0.25)

        # ── quick boing — jump ────────────────────────────────────────────
        s['jump'] = _build(_sine_sweep(260, 520, 0.14, atk=0.02, rel=0.45), vol=0.16)

        # ── descending whoosh — hot slide ─────────────────────────────────
        s['slide'] = _build(_whoosh(0.44), vol=0.21)

        # ── ascending hum — magic carpet liftoff ──────────────────────────
        s['carpet'] = _build(_hum_sweep(130, 430, 0.65), vol=0.24)

        # ── 4-tone triumphant fanfare — made it home! ─────────────────────
        # C5 → E5 → G5 → C6, last note is held longer
        s['fanfare'] = _build(_concat(
            _sine(523,  0.15, atk=0.04, rel=0.20),
            _sine(659,  0.15, atk=0.04, rel=0.20),
            _sine(784,  0.15, atk=0.04, rel=0.20),
            _sine(1047, 0.42, atk=0.04, rel=0.35),
        ), vol=0.30)

        # ── descending tone — game over ───────────────────────────────────
        s['game_over'] = _build(
            _sine_sweep(420, 105, 0.72, atk=0.04, rel=0.32), vol=0.29)

        # ── bright two-note ting — coin / money collected ─────────────────
        s['coin'] = _build(_concat(
            _sine(1318, 0.06, atk=0.02, rel=0.20),   # E6
            _sine(1976, 0.12, atk=0.02, rel=0.35),   # B6
        ), vol=0.22)

        # ── slow shimmering choir chord — heaven / touching God ───────────
        # A spread major chord (C-E-G-C) layered, long and gentle
        def _choir():
            n = int(_SR * 1.6)
            freqs = [261.6, 329.6, 392.0, 523.3]   # C4 E4 G4 C5
            for i in range(n):
                t = i / _SR
                vib = 1.0 + 0.004 * math.sin(2 * math.pi * 5.5 * t)   # soft vibrato
                s_ = sum(math.sin(2 * math.pi * f * vib * t) for f in freqs) / len(freqs)
                yield s_ * _env(i, n, atk=0.22, rel=0.45)
        s['heaven'] = _build(_choir(), vol=0.24)

    # ── public API ────────────────────────────────────────────────────────────

    def toggle(self):
        self.enabled = not self.enabled

    def _play(self, key):
        if self.enabled and key in self._sounds:
            self._sounds[key].play()

    def play_jump(self):      self._play('jump')
    def play_score(self):     self._play('score')
    def play_treat(self):     self._play('treat')
    def play_bird(self):      self._play('bird')
    def play_enemy_hit(self): self._play('enemy_hit')
    def play_angel(self):     self._play('angel')
    def play_water(self):     self._play('water')
    def play_slide(self):     self._play('slide')
    def play_carpet(self):    self._play('carpet')
    def play_fanfare(self):   self._play('fanfare')
    def play_game_over(self): self._play('game_over')
    def play_coin(self):      self._play('coin')
    def play_heaven(self):    self._play('heaven')
