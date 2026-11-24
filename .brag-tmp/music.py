"""Synthesise a soft music bed + transitions and mix it under the narration."""
import json, os, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(7)

with open(os.path.join(".brag-tmp", "timing.json"), encoding="utf-8") as f:
    T = json.load(f)
scenes = T["scenes"]
TOTAL = T["total"]
N = int(TOTAL * SR)


def read_wav_mono(path):
    with wave.open(path) as w:
        assert w.getframerate() == SR
        data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    return data


def env_adsr(n, a, d, s, r, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(d * sr), int(r * sr)
    s_n = max(0, n - a_n - d_n - r_n)
    return np.concatenate([
        np.linspace(0, 1, max(1, a_n), endpoint=False),
        np.linspace(1, s, max(1, d_n), endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, max(1, r_n)),
    ])[:n]


# ---------------- pad ----------------
BPM = 96.0
BEAT = 60.0 / BPM          # 0.625 s
CHORD_LEN = BEAT * 8       # 5 s
PROG = [
    ("Am", [220.00, 261.63, 329.63], 110.00),
    ("F",  [174.61, 220.00, 261.63],  87.31),
    ("C",  [196.00, 261.63, 329.63], 130.81),
    ("G",  [196.00, 246.94, 293.66],  98.00),
]

pad = np.zeros(N, dtype=np.float32)
i = 0
while i * CHORD_LEN < TOTAL:
    name, notes, root = PROG[i % len(PROG)]
    t0 = i * CHORD_LEN
    n = int((CHORD_LEN + 1.6) * SR)
    tt = np.arange(n) / SR
    gain = env_adsr(n, 1.1, 0.6, 0.85, 1.6)
    voice = np.zeros(n, dtype=np.float32)
    for f in notes:
        for det in (-0.003, 0.0, 0.004):
            fr = f * (1 + det)
            voice += (np.sin(2 * np.pi * fr * tt) * 1.0
                      + np.sin(2 * np.pi * fr * 2 * tt) * 0.32
                      + np.sin(2 * np.pi * fr * 3 * tt) * 0.11
                      + np.sin(2 * np.pi * fr * 0.5 * tt) * 0.10).astype(np.float32)
    voice *= gain / (len(notes) * 3 * 1.55)
    # slow stereo-ish shimmer
    voice *= (1 + 0.08 * np.sin(2 * np.pi * 0.21 * tt + i)).astype(np.float32)
    s0 = int(t0 * SR)
    s1 = min(N, s0 + n)
    pad[s0:s1] += voice[: s1 - s0]
    i += 1

# ---------------- bass ----------------
bass = np.zeros(N, dtype=np.float32)
step = 0
while step * BEAT * 2 < TOTAL:
    t0 = step * BEAT * 2
    name, notes, root = PROG[int(t0 // CHORD_LEN) % len(PROG)]
    n = int(BEAT * 1.9 * SR)
    tt = np.arange(n) / SR
    e = np.exp(-tt * 3.1).astype(np.float32)
    tone = (np.sin(2 * np.pi * root * tt) + 0.25 * np.sin(2 * np.pi * root * 2 * tt)).astype(np.float32)
    s0 = int(t0 * SR); s1 = min(N, s0 + n)
    bass[s0:s1] += (tone * e)[: s1 - s0] * 0.5
    step += 1

# ---------------- hats ----------------
hats = np.zeros(N, dtype=np.float32)
noise = rng.standard_normal(N).astype(np.float32)
hp = np.diff(noise, prepend=0.0)  # cheap high-pass
k = 0
while k * BEAT / 2 < TOTAL:
    t0 = k * BEAT / 2
    n = int(0.06 * SR)
    tt = np.arange(n) / SR
    e = np.exp(-tt * 90).astype(np.float32)
    s0 = int(t0 * SR); s1 = min(N, s0 + n)
    amp = 0.5 if k % 2 else 0.22
    hats[s0:s1] += (hp[s0:s1] * e[: s1 - s0]) * amp
    k += 1

music = pad * 0.85 + bass * 0.55 + hats * 0.16

# ---------------- whooshes at scene changes ----------------
fx = np.zeros(N, dtype=np.float32)
for s in scenes[1:]:
    t0 = max(0.0, s["start"] - 0.12)
    n = int(0.42 * SR)
    s0 = int(t0 * SR); s1 = min(N, s0 + n)
    m = s1 - s0
    tt = np.linspace(0, 1, m)
    nz = rng.standard_normal(m).astype(np.float32)
    # one-pole low-pass whose cutoff sweeps up then down
    out = np.empty(m, dtype=np.float32)
    y = 0.0
    cut = 0.03 + 0.32 * np.sin(np.pi * tt) ** 2
    for j in range(m):
        y += cut[j] * (nz[j] - y)
        out[j] = y
    e = np.sin(np.pi * tt) ** 1.6
    fx[s0:s1] += (out * e).astype(np.float32) * 0.55

# ---------------- voice ----------------
voice = np.zeros(N, dtype=np.float32)
for s in scenes:
    w = read_wav_mono(s["wav"])
    s0 = int(s["speech_start"] * SR)
    s1 = min(N, s0 + len(w))
    voice[s0:s1] += w[: s1 - s0]
voice *= 0.92 / max(1e-6, np.abs(voice).max())

# ---------------- duck the music under speech ----------------
mask = (np.abs(voice) > 0.012).astype(np.float32)
win = int(0.22 * SR)
kern = np.ones(win, dtype=np.float32) / win
mask = np.convolve(mask, kern, mode="same")
duck = 1.0 - 0.45 * np.clip(mask * 1.6, 0, 1)
music_gain = (0.115 * duck).astype(np.float32)

# fade in / out
fade_in = int(0.8 * SR)
music_gain[:fade_in] *= np.linspace(0, 1, fade_in)
fade_out = int(2.0 * SR)
music_gain[-fade_out:] *= np.linspace(1, 0, fade_out)

left = voice + music * music_gain + fx * 0.5
right = voice + np.roll(music, int(0.008 * SR)) * music_gain + fx * 0.5
mix = np.stack([left, right], axis=1)
mix *= 0.97 / max(1e-6, np.abs(mix).max())

out = os.path.join(".brag-tmp", "mix.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print("wrote", out, round(len(mix) / SR, 2), "s")
