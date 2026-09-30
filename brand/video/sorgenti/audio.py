import json
import sys
import wave
from pathlib import Path

import numpy as np

# usage: python3 audio.py [plan.json out.wav] — the plan comes from video.html (render.mjs writes it)
SR = 44100
# the scene plan, as in video.html: (id, choreography, transition, slow-down, hold)
PLAN_FULL = [
	("s-hook", 7.6, "cut", 1, 0.3),
	("j1", 3.2, "dive", 1, 0),
	("s-mkt", 4.4, "blinds", 1.3, 1.0),
	("s-tel", 3.8, "cloud", 1.25, 0.9),
	("j2", 3.2, "dive", 1, 0),
	("s-chat", 4.0, "zoom", 1.3, 1.0),
	("s-agenda", 5.0, "push", 1.3, 1.0),
	("s-serv", 3.6, "cloud", 1.2, 0.9),
	("j3", 3.2, "dive", 1, 0),
	("s-clin", 5.2, "wipeD", 1.25, 1.0),
	("s-ai", 4.8, "cloud", 1.25, 1.0),
	("j4", 3.2, "dive", 1, 0),
	("s-fatt", 4.0, "blinds", 1.3, 1.0),
	("s-auto", 3.4, "cloud", 1.3, 1.0),
	("j5", 3.2, "dive", 1, 0),
	("s-acc", 4.8, "push", 1.25, 1.0),
	("s-diet", 4.8, "zoom", 1.3, 1.0),
	("s-ex", 5.0, "cloud", 1.3, 1.0),
	("j6", 3.2, "dive", 1, 0),
	("s-liv", 5.0, "wipeV", 1.3, 1.0),
	("s-unl", 3.4, "zoom", 1, 0.8),
	("s-app", 4.6, "circle", 1.2, 1.0),
	("s-gdpr", 4.2, "cloud", 1.2, 1.0),
	("s-out", 4.8, None, 1, 1.5),
]
PLAN = [tuple(p) for p in json.loads(Path(sys.argv[1]).read_text())] if len(sys.argv) > 1 else PLAN_FULL
OUTWAV = sys.argv[2] if len(sys.argv) > 2 else "audio.wav"
AT = {}
SL = {}
LEN = {}
_a = 0.0
for _id, _d, _t, _s, _h in PLAN:
	AT[_id] = _a
	SL[_id] = _s
	LEN[_id] = _d * _s + _h
	_a += LEN[_id]
TOTAL = _a
DUR = TOTAL
N = int(SR * DUR)
rng = np.random.default_rng(7)


def midi(m):
	return 440 * 2 ** ((m - 69) / 12)


def env(n, a, d, s=0.0, r=None):
	t = np.arange(n) / SR
	e = np.minimum(1, t / max(a, 1e-4))
	return e * ((1 - s) * np.exp(-t / max(d, 1e-4)) + s)


music = np.zeros((N, 2))
sfx = np.zeros((N, 2))


def add(buf, t0, sig, pan=0.0, g=1.0):
	if t0 is None:
		return
	i = int(t0 * SR)
	if i >= N:
		return
	sig = sig[: N - i]
	l = np.cos((pan + 1) * np.pi / 4)
	r = np.sin((pan + 1) * np.pi / 4)
	buf[i : i + len(sig), 0] += sig * l * g * 1.414 / 2 * 1.414
	buf[i : i + len(sig), 1] += sig * r * g * 1.414 / 2 * 1.414


def lp(x, fc):
	a = np.exp(-2 * np.pi * fc / SR)
	# one-pole via cumulative filtering (vectorized using lfilter-like loop in chunks)
	from itertools import accumulate

	return np.array(list(accumulate(x, lambda p, v: a * p + (1 - a) * v)))


HOOK = "s-hook" in AT
AT_OUT = AT.get("s-out", AT.get("x-end", TOTAL))
GROOVE = 7.6 if HOOK else AT[PLAN[1][0]]  # drums and bass come in here
ARP = 3.5 if HOOK else 0.2
# ---------- music: F, Dm, Bb, C at 120 bpm ----------
CH = [[53, 57, 60, 64], [50, 57, 60, 65], [46, 57, 62, 65], [48, 55, 60, 64]]
BASS = [41, 38, 34, 36]


def pad(freqs, n):
	t = np.arange(n) / SR
	s = np.zeros(n)
	for f in freqs:
		for det in (-0.12, 0.0, 0.12):
			ff = f * 2 ** (det / 12)
			s += (
				np.sin(2 * np.pi * ff * t + rng.random() * 6)
				+ 0.25 * np.sin(2 * np.pi * 2 * ff * t)
				+ 0.08 * np.sin(2 * np.pi * 3 * ff * t)
			)
	return s / (len(freqs) * 3)


bar = 2.0
END = AT_OUT
SOFT = [(AT[s], AT[s] + LEN[s]) for s in ("s-ai", "s-gdpr") if s in AT]


def soft(t):
	return any(a <= t < b for a, b in SOFT)


k = 0
while k * bar < END:
	t0 = k * bar
	c = CH[k % 4]
	n = int(SR * (bar + 0.6))
	e = env(n, 0.35, 10, 0.9)
	e[int(SR * bar) :] *= np.linspace(1, 0, n - int(SR * bar))
	add(music, t0, pad([midi(m) for m in c], n) * e, 0, 0.16 if (t0 < GROOVE or soft(t0)) else 0.12)
	k += 1
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2]
t0 = ARP
k = 0
while t0 < END:
	c = CH[int(t0 // bar) % 4]
	m = c[arp_pat[k % 8]] + 12
	n = int(SR * 0.5)
	t = np.arange(n) / SR
	f = midi(m)
	s_ = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 20)) * env(
		n, 0.004, 0.16
	)
	add(music, t0, s_, 0.35 if k % 2 else -0.35, 0.05 if t0 < GROOVE else 0.07)
	t0 += 0.25
	k += 1


def kick():
	n = int(SR * 0.4)
	t = np.arange(n) / SR
	f = 50 + 90 * np.exp(-t * 30)
	return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat():
	n = int(SR * 0.08)
	x = rng.standard_normal(n)
	x = x - lp(x, 6000)
	return x * np.exp(-np.arange(n) / SR * 60)


HAT = hat()
KICK = kick()
t0 = GROOVE
k = 0
while t0 < END:
	full = not soft(t0)
	b = BASS[int(t0 // bar) % 4]
	n = int(SR * 0.48)
	t = np.arange(n) / SR
	f = midi(b)
	s_ = np.sin(2 * np.pi * f * t) + 0.15 * np.sin(2 * np.pi * 2 * f * t)
	e = env(n, 0.01, 0.3, 0.4)
	e[-800:] *= np.linspace(1, 0, 800)
	add(music, t0, s_ * e, 0, 0.16 if full else 0.08)
	if full and k % 2 == 0:
		add(music, t0, KICK, 0, 0.30)
	add(music, t0 + 0.25, HAT, 0.2, 0.05 if full else 0.025)
	if full and k % 2 == 1:
		n = int(SR * 0.2)
		x = rng.standard_normal(n)
		x = lp(x, 3000) - lp(x, 700)
		add(music, t0, x * np.exp(-np.arange(n) / SR * 18), -0.1, 0.10)
	t0 += 0.5
	k += 1
n = int(SR * (DUR - END))
e = env(n, 0.02, 2.2, 0.55) * np.linspace(1, 0, n) ** 1.1
add(music, END, pad([midi(m) for m in [41, 53, 57, 60, 67, 72]], n) * e, 0, 0.22)
add(music, END, KICK, 0, 0.35)


# ---------- sfx ----------
def whoosh(dur=0.7, lo=300, hi=2500):
	n = int(SR * dur)
	x = rng.standard_normal(n)
	b = lp(x, hi) - lp(x, lo)
	t = np.linspace(0, 1, n)
	return b * np.sin(np.pi * t) ** 2


def riser(dur):
	n = int(SR * dur)
	x = rng.standard_normal(n)
	b = lp(x, 2500) - lp(x, 400)
	return b * np.linspace(0, 1, n) ** 2.5


def pluck(m, d=0.25):
	n = int(SR * 0.6)
	t = np.arange(n) / SR
	f = midi(m)
	return (np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t * 30)) * env(
		n, 0.002, d
	)


def click():
	n = int(SR * 0.05)
	t = np.arange(n) / SR
	return np.sin(2 * np.pi * midi(84) * t) * np.exp(-t * 120) + 0.3 * lp(
		rng.standard_normal(n), 5000
	) * np.exp(-t * 200)


def boom(g=0.35):
	n = int(SR * 1.2)
	t = np.arange(n) / SR
	return np.sin(2 * np.pi * (45 + 60 * np.exp(-t * 25)) * t) * np.exp(-t * 4) * g


pent = [65, 69, 72, 74, 77, 81]


def chime(ms, t0, g=0.08):
	if t0 is None:
		return
	for j, m in enumerate(ms):
		add(sfx, t0 + j * 0.07, pluck(m + 12, 0.5), (j - 1) * 0.3, g)


def ticks(t0, n, step, g=0.035, oct=12):
	for i in range(n):
		add(sfx, t0 + i * step, pluck(pent[i % 6] + oct, 0.07), (-1) ** i * 0.4, g)


def at(sc, t):
	return AT[sc] + t * SL[sc] if sc in AT else None


# ---------- transitions: few, and each kind with its own sound ----------
# Only the moves that open space get a sound: the chapter doors, the diagonal
# wipes that cross the frame, the way into the dark. Pushes stay silent.
def vlp(x, fc):
	"""One-pole low-pass whose cut-off follows the array fc, sample by sample."""
	y = np.empty_like(x)
	s = 0.0
	a = np.exp(-2 * np.pi * np.asarray(fc) / SR)
	for k in range(len(x)):
		s = a[k] * s + (1 - a[k]) * x[k]
		y[k] = s
	return y


def add_st(buf, t0, L, R, g=1.0):
	i = int(t0 * SR)
	if i < 0:
		L, R = L[-i:], R[-i:]
		i = 0
	n = min(len(L), N - i)
	buf[i : i + n, 0] += L[:n] * g
	buf[i : i + n, 1] += R[:n] * g


def doppler(t_mid, dur=0.9, lo=180, hi=3200, pan_from=-0.8, pan_to=0.8, g=0.30):
	"""Something passes in front of the camera: the band opens and closes, the
	sound crosses the stereo field, the tail is shorter than the approach."""
	n = int(SR * dur)
	u = np.linspace(0, 1, n)
	peak = 0.58
	shape = np.where(u < peak, (u / peak) ** 2.2, (1 - (u - peak) / (1 - peak)) ** 1.4)
	x = rng.standard_normal(n)
	b = vlp(x, lo + (hi - lo) * shape) - vlp(x, np.full(n, lo * 0.7))
	b *= shape
	p = pan_from + (pan_to - pan_from) * u
	add_st(sfx, t_mid - dur * peak, b * np.cos((p + 1) * np.pi / 4), b * np.sin((p + 1) * np.pi / 4), g)


def swell(t_end, dur=1.1, notes=(65, 72, 77), g=0.18):
	"""A reversed tail that grows into the next chapter: air plus the chord,
	fading in, cut exactly on the downbeat."""
	n = int(SR * dur)
	u = np.linspace(0, 1, n)
	e = u**3
	x = rng.standard_normal(n)
	air = (vlp(x, np.full(n, 2600)) - vlp(x, np.full(n, 500))) * 0.5
	t = np.arange(n) / SR
	tone = sum(np.sin(2 * np.pi * midi(m) * t + rng.random() * 6) for m in notes) / len(notes)
	s = (air + tone * 0.6) * e
	add_st(sfx, t_end - dur, s * 0.95, s * 1.0, g)


def air_rise(t_mid, dur=0.8, g=0.16, up=True):
	"""A thin sweep that climbs (or falls) with a vertical wipe."""
	n = int(SR * dur)
	u = np.linspace(0, 1, n)
	f = 400 + 5000 * (u if up else 1 - u) ** 1.6
	x = rng.standard_normal(n)
	b = vlp(x, f) - vlp(x, f * 0.35)
	e = np.sin(np.pi * u) ** 2
	add_st(sfx, t_mid - dur / 2, b * e, b * e * 0.9, g)


def sub_whoosh(t_mid, dur=1.4, g=0.22):
	"""Into the dark: low air and a falling sub, felt more than heard."""
	n = int(SR * dur)
	u = np.linspace(0, 1, n)
	x = rng.standard_normal(n)
	low = vlp(x, np.full(n, 450)) - vlp(x, np.full(n, 60))
	sub = np.sin(2 * np.pi * np.cumsum(95 - 55 * u) / SR)
	e = np.where(u < 0.45, (u / 0.45) ** 2, np.exp(-(u - 0.45) * 5))
	s = (low * 0.8 + sub * 0.7) * e
	add_st(sfx, t_mid - dur * 0.45, s, s, g)


def shimmer(t_mid, dur=1.0, g=0.15):
	"""A cloud opens: bright air and three high notes ringing out."""
	n = int(SR * dur)
	u = np.linspace(0, 1, n)
	x = rng.standard_normal(n)
	hi = x - vlp(x, np.full(n, 5000))
	e = np.sin(np.pi * u) ** 1.5
	add_st(sfx, t_mid - dur / 2, hi * e * 0.6, hi * e * 0.6, g)
	for j, m in enumerate((84, 89, 93)):
		add(sfx, t_mid - 0.1 + j * 0.08, pluck(m, 0.35), (j - 1) * 0.5, 0.035)


# ---------- transitions ----------
# Sound only where space opens: the chapter doors (a swell and a soft low hit),
# the passes that cross the frame, the way into the dark. Zooms, pushes and
# dives into a scene stay silent: the music carries them.
pans = [(-0.8, 0.8), (0.8, -0.8)]
nd = 0
chords = [(65, 72, 77), (62, 69, 74), (58, 65, 70), (60, 67, 72), (53, 60, 65), (57, 64, 69)]
for i, (sc, _d, ty, _sl, _h) in enumerate(PLAN):
	b = AT[sc] + LEN[sc]
	if ty in ("blinds", "wipeD"):
		pf, pt = pans[nd % 2]
		nd += 1
		doppler(
			b,
			pan_from=pf,
			pan_to=pt,
			lo=150 if ty == "wipeD" else 200,
			hi=2600 if ty == "wipeD" else 3400,
			g=0.22,
		)
	elif ty == "wipeV":
		air_rise(b, up=False, g=0.10)
	elif ty == "circle":
		sub_whoosh(b)
	elif ty == "cloud":
		nxt = PLAN[i + 1][0]
		if nxt.startswith("j"):
			swell(b, notes=chords[int(nxt[1]) - 1], g=0.16)
		elif nxt == "s-out":
			swell(b, dur=1.4, notes=(53, 60, 65, 69), g=0.18)
for k in range(2, 7):
	add(sfx, at("j%d" % k, 0.55), boom(0.2), 0, 1)  # the stop lights up: felt, not a bell


# ---------- the logo ----------
def snap(base):  # the logo's pieces click together
	if base is None:
		return
	add(sfx, base, pluck(53, 0.2), -0.3, 0.1)
	add(sfx, base + 0.15, pluck(60, 0.2), 0.3, 0.1)
	add(sfx, base + 0.3, pluck(65, 0.2), 0, 0.1)


snap(at("s-out", 0.3))
chime([65, 72, 77, 81], at("s-out", 2.1), 0.05)
add(music, 0.0, riser(1.2) * 0.05, 0, 1)
if HOOK:
	snap(0.15)
	chime([72, 77, 81], 0.85, 0.07)
	for i in range(7):
		add(
			sfx, 5.55 + i * 0.08, pluck(pent[i % 6] + 12, 0.1), (-1) ** i * 0.3, 0.035
		)  # channels absorbed, quietly
	add(sfx, 6.55, riser(1.05), 0, 0.22)
	add(sfx, 7.6, boom(0.45), 0, 1)
	chime([65, 72, 77], 7.62, 0.06)
# the ads: a low hit under the first words, the logo and a bell on the call to action
add(sfx, at("x-hook", 0.05), boom(0.3), 0, 1)
snap(at("x-end", 0.15))
chime([72, 77, 84], at("x-end", 1.35), 0.06)


# ---------- interfaces: clicks and taps for what the hand does, one bell per real event ----------
def tap(t0, g=0.08):
	add(sfx, t0, click() * 0.6, 0.1, g)


for sc, t in [
	("s-ai", 3.95),
	("s-tel", 2.3),
	("s-mkt", 1.45),
	("s-fatt", 1.6),
	("s-liv", 2.0),
	("s-liv", 3.6),
]:
	add(sfx, at(sc, t), click(), 0.2, 0.18)
chime([77, 84], at("s-mkt", 2.6), 0.05)  # a request comes in
for r in range(3 if "s-tel" in AT else 0):  # the phone rings
	for j, m in enumerate((81, 77, 81, 77)):
		add(sfx, at("s-tel", 0.85) + r * 0.5 * SL["s-tel"] + j * 0.08, pluck(m, 0.08), 0, 0.03)
chime([77, 81, 84], at("s-chat", 2.85), 0.05)  # appointment confirmed
add(sfx, at("s-agenda", 2.3), pluck(62, 0.3), 0, 0.04)  # a slot frees up
chime([72, 77], at("s-agenda", 3.4), 0.05)  # ...and is filled from the list
chime([81, 84], at("s-clin", 3.2), 0.04)  # note signed
chime([72, 77, 81], at("s-fatt", 2.8), 0.05)  # sent to Sistema TS
chime([81], at("s-acc", 0.8), 0.04)
tap(at("s-acc", 1.3))  # SMS, tap on the code
chime([72, 77, 84], at("s-acc", 2.85), 0.05)  # face recognised
for t in (1.45, 2.0, 2.85):
	tap(at("s-diet", t))
add(sfx, at("s-diet", 2.05), whoosh(0.4, 500, 3000), 0, 0.08)
chime([77, 81], at("s-diet", 3.12), 0.04)  # fish swapped
for t in (1.4, 2.1, 2.5, 2.9, 3.55):
	tap(at("s-ex", t))
chime([69, 74, 81], at("s-ex", 3.6), 0.05)  # exercise done
tap(at("s-app", 2.15))
chime([72, 77, 81], at("s-app", 3.4), 0.04)  # consent signed


# ---------- reverb ----------
def reverb(x, secs=2.2, mix=0.25):
	n = int(SR * secs)
	ir = rng.standard_normal((n, 2)) * np.exp(-np.arange(n) / SR * 3.2)[:, None]
	ir[:, 0] = lp(ir[:, 0], 5000)
	ir[:, 1] = lp(ir[:, 1], 5000)
	out = np.zeros_like(x)
	L = len(x) + n
	nfft = 1 << (L - 1).bit_length()
	for c in range(2):
		y = np.fft.irfft(np.fft.rfft(x[:, c], nfft) * np.fft.rfft(ir[:, c], nfft), nfft)[: len(x)]
		out[:, c] = y
	out /= np.max(np.abs(out)) + 1e-9
	out *= np.max(np.abs(x))
	return x * (1 - mix) + out * mix * 1.4


bus = music + sfx
bus = reverb(bus, 2.4, 0.28)
# fade in/out, soft limit, normalise
fi = int(SR * 0.05)
bus[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(SR * 0.6)
bus[-fo:] *= np.linspace(1, 0, fo)[:, None]
bus = np.tanh(bus * 1.3)
bus /= np.max(np.abs(bus))
bus *= 10 ** (-1.5 / 20)
pcm = (bus * 32767).astype(np.int16)
with wave.open(OUTWAV, "wb") as w:
	w.setnchannels(2)
	w.setsampwidth(2)
	w.setframerate(SR)
	w.writeframes(pcm.tobytes())
print("ok", len(pcm) / SR)
