"""Generates NEON VEIL's original M00 ambience and score bed (Bible §4 sound brief: restrained
low-frequency industrial pulse, clean HVAC, distant maglev, rain beyond sealed glass; music drops
out before the handshake). All synthesis is procedural and original; loops are seamless
(equal-power crossfade of the tail into the head). Run: python generate_m00_audio.py
Outputs 48 kHz 16-bit WAVs next to this script.
"""
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(2017)

def lowpass(x, hz, order=4):
    b, a = signal.butter(order, hz / (SR / 2), "low")
    return signal.filtfilt(b, a, x)

def highpass(x, hz, order=2):
    b, a = signal.butter(order, hz / (SR / 2), "high")
    return signal.filtfilt(b, a, x)

def bandpass(x, lo, hi, order=2):
    b, a = signal.butter(order, [lo / (SR / 2), hi / (SR / 2)], "band")
    return signal.filtfilt(b, a, x)

def seamless(x, fade_s=2.0):
    """Crossfade the last fade_s seconds into the first so the file loops without a seam."""
    n = int(fade_s * SR)
    head, body, tail = x[:n], x[n:-n] if x.ndim == 1 else x[n:-n], x[-n:]
    t = np.linspace(0, np.pi / 2, n)
    fin, fout = np.sin(t), np.cos(t)
    if x.ndim == 2:
        fin, fout = fin[:, None], fout[:, None]
    mixed = head * fin + tail * fout
    return np.concatenate([mixed, x[n:-n]])

def norm(x, peak_db=-3.0):
    return x / (np.max(np.abs(x)) + 1e-9) * 10 ** (peak_db / 20)

def stereo(l, r):
    return np.stack([l, r], axis=1)

def write(name, x):
    wavfile.write(name, SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
    print("wrote", name, x.shape)

def brown(n):
    w = rng.standard_normal(n)
    b = np.cumsum(w)
    b = highpass(b, 15)
    return b / np.max(np.abs(b))

# ---------------------------------------------------------------- HVAC: clean, airy, steady
def hvac(seconds=32):
    n = (seconds + 2) * SR
    l = bandpass(rng.standard_normal(n), 120, 2400) * 0.6 + lowpass(brown(n), 300) * 0.8
    r = bandpass(rng.standard_normal(n), 120, 2400) * 0.6 + lowpass(brown(n), 300) * 0.8
    t = np.arange(n) / SR
    hum = 0.05 * np.sin(2 * np.pi * 60 * t) + 0.02 * np.sin(2 * np.pi * 120 * t)   # faint mains hum
    sway = 1.0 + 0.08 * np.sin(2 * np.pi * t / 11.0)
    x = stereo(l * sway + hum, r * sway + hum)
    return norm(seamless(x), -6)

# ---------------------------------------------------------------- industrial pulse: deep, slow
def pulse(seconds=32, period=2.0):
    n = (seconds + 2) * SR
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(int((seconds + 2) / period) + 1):
        t0 = k * period
        m = (t >= t0)
        dt = t[m] - t0
        env = np.exp(-dt * 3.2) * (1 - np.exp(-dt * 60))
        x[m] += env * (np.sin(2 * np.pi * 43 * dt) + 0.35 * np.sin(2 * np.pi * 86 * dt))
    drone = 0.25 * np.sin(2 * np.pi * 36.7 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * t / 16))
    x = lowpass(x + drone, 220)
    return norm(seamless(stereo(x, x)), -4)

# ---------------------------------------------------------------- distant maglev passes + rain on glass
def city(seconds=40):
    n = (seconds + 2) * SR
    t = np.arange(n) / SR
    l = np.zeros(n); r = np.zeros(n)
    for start, dur, pan in ((3.0, 9.0, -1), (17.0, 7.0, 1), (29.0, 10.0, -0.4)):
        m = (t >= start) & (t < start + dur)
        u = (t[m] - start) / dur
        env = np.sin(np.pi * u) ** 2
        whoosh = bandpass(rng.standard_normal(m.sum()), 200, 1600) * env
        tone = 0.3 * np.sin(2 * np.pi * (180 + 60 * (0.5 - u)) * (t[m] - start)) * env   # doppler-ish
        p = pan * (1 - 2 * u)
        l[m] += (whoosh + tone) * (0.5 - 0.5 * p)
        r[m] += (whoosh + tone) * (0.5 + 0.5 * p)
    # rain beyond sealed glass: muffled (low-passed) dense hiss
    rain_l = lowpass(highpass(rng.standard_normal(n), 400), 2200) * 0.35
    rain_r = lowpass(highpass(rng.standard_normal(n), 400), 2200) * 0.35
    x = stereo(lowpass(l, 1800) * 0.8 + rain_l, lowpass(r, 1800) * 0.8 + rain_r)
    return norm(seamless(x, 3.0), -8)

# ---------------------------------------------------------------- score bed: "supreme control to first unease"
def score(seconds=64):
    n = (seconds + 4) * SR
    t = np.arange(n) / SR
    # D minor add9 cluster that slowly drifts flat (unease) and back
    base = [73.42, 110.0, 146.83, 164.81, 220.0]
    drift = 1.0 - 0.006 * (0.5 - 0.5 * np.cos(2 * np.pi * t / seconds))
    x = np.zeros(n)
    for i, f in enumerate(base):
        ph = 2 * np.pi * np.cumsum(f * drift) / SR
        amp = 0.6 / (i + 1) * (0.7 + 0.3 * np.sin(2 * np.pi * t / (13 + 3 * i) + i))
        # soft saw-ish timbre (3 partials) for warmth
        x += amp * (np.sin(ph) + 0.33 * np.sin(2 * ph) + 0.14 * np.sin(3 * ph))
    # slow filter sweep: closed -> open -> closed
    cutoff_env = 500 + 900 * (0.5 - 0.5 * np.cos(2 * np.pi * t / (seconds / 2)))
    # time-varying 2-pole low-pass (two cascaded one-poles), smooth: no block seams
    a = np.exp(-2 * np.pi * cutoff_env / SR)
    out = np.empty(n)
    y1 = y2 = 0.0
    for i in range(n):
        y1 = (1 - a[i]) * x[i] + a[i] * y1
        y2 = (1 - a[i]) * y1 + a[i] * y2
        out[i] = y2
    # glassy high motif every 16 s (sparse, cold)
    for k, t0 in enumerate(np.arange(6, seconds, 16)):
        m = (t >= t0) & (t < t0 + 6)
        dt = t[m] - t0
        f = (587.33, 659.25, 554.37, 587.33)[k % 4]
        out[m] += 0.12 * np.sin(2 * np.pi * f * dt) * np.exp(-dt * 0.7)
    l = out + 0.15 * np.roll(out, int(0.023 * SR))
    r = out + 0.15 * np.roll(out, int(0.031 * SR))
    return norm(seamless(stereo(l, r), 4.0), -5)

if __name__ == "__main__":
    write("SFX_AMB_Crown_HVAC.wav", hvac())
    write("SFX_AMB_Crown_IndustrialPulse.wav", pulse())
    write("SFX_AMB_Crown_CityRain.wav", city())
    write("MUS_M00_CrownBed.wav", score())
