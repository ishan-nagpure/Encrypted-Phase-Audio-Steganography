# SpectraMux — Complete Error & Troubleshooting Guide

Every error a user can encounter across `multiple_enco.py`, `snr_test.py`, and the encryption key system — what causes it, what you see, and how to fix it.

---

## Table of Contents
1. [Setup & Installation Errors](#1-setup--installation-errors)
2. [Audio File Errors](#2-audio-file-errors)
3. [Encryption Key Errors](#3-encryption-key-errors)
4. [Frequency & Payload Errors](#4-frequency--payload-errors)
5. [Input Validation Errors](#5-input-validation-errors)
6. [Silent Failures (no error shown, but data is lost)](#6-silent-failures-no-error-shown-but-data-is-lost)
7. [SNR Analyzer Errors](#7-snr-analyzer-errors)
8. [Platform-Specific Errors](#8-platform-specific-errors)

---

## 1. Setup & Installation Errors

---

### E01 — `ModuleNotFoundError: No module named 'cryptography'`

**When you see it:** On first run of `multiple_enco.py`.

**Cause:** The `cryptography` library is not listed in a `requirements.txt`, so users who install only the obvious packages (`numpy`, `scipy`, `matplotlib`) miss it.

**Fix:**
```bash
pip install numpy scipy matplotlib cryptography
```

Or install everything at once:
```bash
pip install -r requirements.txt
```

**Recommended:** Add a `requirements.txt` to the repo:
```
numpy
scipy
matplotlib
cryptography
```

---

### E02 — `ModuleNotFoundError: No module named 'scipy'` / `'numpy'` / `'matplotlib'`

**Cause:** Running on a bare Python environment without any scientific packages.

**Fix:**
```bash
pip install numpy scipy matplotlib cryptography
```

If you're using a virtual environment, make sure it's activated first:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

---

## 2. Audio File Errors

---

### E03 — `FileNotFoundError: [Errno 2] No such file or directory: 'sample.wav'`

**When you see it:** Immediately on running `multiple_enco.py` or `snr_test.py`.

**Cause:** The script looks for `sample.wav` in the same directory it's run from. If you run from a different folder, or if the file has a different name, this crash occurs.

**Fix:** Make sure you run the script from the same folder as your audio file:
```bash
cd /path/to/your/project
python multiple_enco.py
```

Or rename your audio file to `sample.wav`, or edit the filename at the bottom of the script:
```python
# Change this line:
analyze('sample.wav', 'encoded_sample.wav')
# To your actual filenames:
analyze('my_audio.wav', 'my_audio_encoded.wav')
```

---

### E04 — `ValueError: File format b'...' not understood. Only 'RIFF', 'RIFX', and 'RF64' supported.`

**When you see it:** When you load a corrupted file or a non-WAV file with a `.wav` extension.

**Cause:** The file is not a valid WAV file. Common causes:
- You renamed an MP3 to `.wav` (changing the extension doesn't change the format)
- The file was partially downloaded or corrupted
- The file is a video format (MP4, MOV) with a wrong extension

**Fix:** Convert your audio to a proper WAV file:
```bash
# Using ffmpeg (free, command line):
ffmpeg -i input.mp3 output.wav
ffmpeg -i input.mp4 -vn output.wav
```

Or use Audacity: File → Export → Export as WAV.

---

### E05 — `ValueError: Unsupported bit depth: 24`

**When you see it:** When loading a 24-bit WAV file. Many DAWs (GarageBand, Audacity, Logic Pro) export 24-bit by default.

**Cause:** `scipy.io.wavfile` does not support 24-bit PCM WAV files — only 8, 16, and 32-bit.

**Fix:** Re-export your audio as 16-bit WAV from your audio editor.

In **Audacity**: File → Export → Export as WAV → change "Encoding" to "Signed 16-bit PCM".

In **ffmpeg**:
```bash
ffmpeg -i input_24bit.wav -sample_fmt s16 output_16bit.wav
```

---

### E06 — `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`

**When you see it:** On Windows only, when the WAV file is open in another application.

**Cause:** Audacity, VLC, Windows Media Player, or another app has the file locked.

**Fix:** Close the application that has the file open, then run the script again.

---

### E07 — `OSError: [Errno 28] No space left on device`

**When you see it:** During `wavfile.write('encoded_sample.wav', ...)`.

**Cause:** Your disk is full. Float32 WAV files are larger than the original int16 files (2× the size).

**Fix:** Free up disk space and re-run. Check available space:
```bash
# macOS/Linux
df -h .

# Windows
dir
```

---

### E08 — Stereo audio with out-of-phase channels → silent output, no encoding

**When you see it:** No error message. Encoder prints `SUCCESS` but the decoded output is empty or garbage.

**Cause:** The encoder converts stereo to mono using `mean(axis=1)`. If your stereo file has equal and opposite channels (a common mastering artifact called "mid-side" encoding), they cancel each other out: `(+30000 + -30000) / 2 = 0`. The entire audio becomes silence, and you cannot embed phase data into a zero-magnitude signal.

**Fix:** Check your audio is not silent after mono conversion:
```python
import numpy as np
from scipy.io import wavfile
sr, data = wavfile.read('your_file.wav')
if len(data.shape) == 2:
    mono = data.mean(axis=1)
    print(f'Max amplitude after mono: {np.max(np.abs(mono))}')
    # If this prints 0.0 or near-zero, your channels cancel!
```

**Solution:** Use a different audio file, or export a mono version from your DAW.

---

## 3. Encryption Key Errors

---

### E09 — `cryptography.fernet.InvalidToken`

**When you see it:** In the decoder, after extraction of binary data.

**Cause (most common):** You are using a different `encryption.key` file than the one used when encoding. This happens when:
- You deleted and re-ran the encoder (which generates a new key)
- You ran the encoder on a different machine
- You manually regenerated the key

**This is the most dangerous silent failure in the project.** When `encryption.key` is missing, `get_key()` silently generates a brand new key and saves it, with no warning that the old key is gone. The encoder then runs with the new key, and any previously encoded files become permanently unreadable.

**Fix:** You must use the same key that was used to encode. If you lost the key, the data is unrecoverable.

**Best practice:** Back up `encryption.key` immediately after first encoding:
```bash
# Copy your key to a safe location
cp encryption.key ~/Documents/spectra_backup.key
```

Never delete `encryption.key` between encode and decode sessions.

---

### E10 — Wrong delimiter during decode → empty or garbled output

**When you see it:** Decoder runs without errors but extracted text is empty or nonsense.

**Cause:** The decoder searches for the delimiter string to find where the payload ends. If the delimiter passed to the decoder doesn't match exactly what was used during encoding, the split fails and you get the full raw (decrypted but unsplit) Fernet token, or nothing at all.

**Fix:** Use the exact same delimiter string in both encoder and decoder. If you used the UI prompt and typed `SECRET`, the actual stored delimiter is `###SECRET###`. Pass `###SECRET###` to the decoder.

---

## 4. Frequency & Payload Errors

---

### E11 — `ERROR: Payload at {freq}Hz exceeds Nyquist limit. Aborting.`

**When you see it:** During encoding, before any phase injection happens.

**Cause:** Your target frequency is above the Nyquist frequency (half the sample rate). For a 44100 Hz WAV, the Nyquist limit is 22050 Hz. Any frequency at or above this limit is beyond what the audio can represent.

**Fix:** Use a frequency below half your sample rate:
```
Sample rate 44100 Hz → max usable frequency ≈ 20000 Hz (keep some headroom)
Sample rate 22050 Hz → max usable frequency ≈ 10000 Hz
Sample rate 48000 Hz → max usable frequency ≈ 22000 Hz
```

Recommended safe ranges: 2000–18000 Hz for standard 44100 Hz audio.

---

### E12 — `ERROR: Payloads at {freqA}Hz and {freqB}Hz OVERLAP. Aborting.`

**When you see it:** During encoding when two payload bin ranges collide.

**Cause:** Your message is too long for the gap between the two frequency lanes. Each character requires 8 bits, plus Fernet adds ~150 characters of overhead. If the encoded message at 5000 Hz spills into the 5500 Hz region, and you also have a payload there, they will corrupt each other.

**To calculate safe spacing:** Each character = 8 bits = 8 FFT bins. The Fernet overhead is ~150 characters (~1200 bits minimum). So:

```
Required bin gap = (len(your_text) + 150) × 8
Required Hz gap  = Required bin gap × (sample_rate / n_samples)

For a 3-second 44100 Hz file (n=132300):
Hz per bin = 44100 / 132300 ≈ 0.33 Hz/bin

A 20-character message needs: (20 + 150) × 8 = 1360 bins = ~453 Hz gap minimum
```

**Fix:** Either increase the gap between frequencies (e.g., use 5000 Hz and 8000 Hz instead of 5000 Hz and 5500 Hz), or shorten your message.

---

### E13 — Frequency of 0 Hz entered → encoder says SUCCESS but nothing is written

**When you see it:** No error. Encoder completes normally.

**Cause:** Frequency 0 Hz maps to bin index 0 (the DC component). The encoder guards against writing to bin 0 (`if pos == 0: continue`), so every single bit is skipped. The file is saved unchanged with no payload.

**Fix:** Never use 0 Hz as a frequency lane. Use at minimum 500 Hz, ideally 2000 Hz or higher to stay well clear of the DC bin and the low-frequency content of most audio.

---

### E14 — Negative frequency entered → encoder says SUCCESS but decoder finds nothing

**When you see it:** No error. Encoder completes and saves the file. Decoder at the equivalent positive frequency finds garbage or nothing.

**Cause:** A negative frequency like -5000 wraps the FFT index to the negative-frequency (mirror) side of the spectrum. The encoder writes there, but the decoder computes a positive bin index and reads from the wrong location.

**Fix:** Only enter positive frequencies. Add a validation check yourself if you want to be safe:
```python
if freq <= 0:
    print("ERROR: Frequency must be a positive number (e.g., 5000).")
    continue
```

---

### E15 — Very long message causes poor audio quality (high noise floor)

**When you see it:** SNR drops significantly. Audio may sound noticeably different.

**Cause:** Each bit of payload forces a frequency bin's phase to ±π/2, overriding the natural phase of the carrier audio. The more bits you inject, the wider the frequency band affected, and the more the original phase structure of the audio is disturbed. Very long messages at low frequencies will audibly alter the sound.

**Fix:** Keep messages short. As a rule of thumb:
- Inject at high frequencies (12000–18000 Hz) where humans are least sensitive
- Keep messages under 500 characters for best transparency
- Use multiple shorter payloads across separate lanes rather than one very long one

---

## 5. Input Validation Errors

---

### E16 — `ValueError: invalid literal for int() with base 10: '5000.5'`

**When you see it:** When entering a decimal frequency like `5000.5` or `12.5k`.

**Cause:** The encoder uses `int(input(...))` which rejects any non-integer string, including valid decimal numbers.

**Fix:** Enter whole numbers only: `5000`, not `5000.5` or `5.0k`.

If you want to use a decimal, round it: `5000.5 Hz → enter 5000` or `5001`.

**Developer fix:**
```python
freq = int(float(input("Enter the frequency lane in Hz: ")))
```
This handles `5000.0` and `5000.5` without crashing.

---

### E17 — `ValueError: Please enter a valid number.` (for message count)

**When you see it:** When you type something non-numeric for "How many messages?"

**Cause:** `int(input(...))` rejects anything that isn't a plain integer.

**Fix:** Enter a plain integer: `1`, `2`, `3`. Not `one`, `two`, or `1.0`.

---

## 6. Silent Failures (no error shown, but data is lost)

These are the most dangerous issues — the encoder prints `SUCCESS` but the payload is unrecoverable.

---

### SF01 — Silent audio input → phase encoding produces nothing

**Cause:** Phase steganography works by keeping the existing magnitude and changing only the phase: `output = magnitude × e^(j×phase)`. If the carrier audio is silent (all zeros), magnitude = 0 everywhere, so `0 × e^(j×phase) = 0`. No information survives the IFFT.

**How to detect:** Check that your audio is not silent before encoding:
```python
from scipy.io import wavfile
import numpy as np
sr, data = wavfile.read('sample.wav')
print(f"Max amplitude: {np.max(np.abs(data))}")
# If this is 0 or extremely small, your audio is effectively silent.
```

**Fix:** Use audio with real content — music, speech, nature sounds. Avoid synthetically generated silence or pure tones at frequencies far from your injection bands.

---

### SF02 — Deleted `encryption.key` between encode and decode → new key silently generated

**Cause:** `get_key()` creates a new key if the file doesn't exist. This means deleting or losing `encryption.key` after encoding permanently destroys the ability to decrypt — but the encoder reports `SUCCESS` on the next run.

**How to detect:** Check the key file timestamp. If it's newer than `encoded_sample.wav`, you have a new key and the data is gone.

**Fix:** Treat `encryption.key` like a password. Back it up. Never delete it. Consider renaming it to something descriptive: `project_name_2024.key`.

---

### SF03 — Large length mismatch between original and stego in SNR test

**Cause:** `snr_test.py` silently trims both arrays to `min_len` before comparison. If your original is 30 seconds and stego is 3 seconds (or vice versa), only 3 seconds are compared. The SNR will look artificially good because the comparison is not representative.

**How to detect:** Print lengths before trimming:
```python
print(f"Original: {len(o_f)} samples ({len(o_f)/sr1:.1f}s)")
print(f"Stego:    {len(s_f)} samples ({len(s_f)/sr2:.1f}s)")
```

**Fix:** Always compare files of the same length. The encoded file should be exactly the same length as the original — if it's not, something went wrong in the encoder.

---

## 7. SNR Analyzer Errors

---

### E18 — `RuntimeWarning: divide by zero encountered in log10` *(fixed in latest version)*

**When you see it:** As a console warning during `plt.specgram()`.

**Cause:** `plt.specgram()` internally computes `10 × log10(power_spectrum)`. Phase-modified audio can produce FFT bins with exactly zero power, and `log10(0) = -∞`. This generates the warning and can cause dark rendering artifacts in the spectrogram.

**Fix (already applied in latest `snr_test.py`):** Replace `plt.specgram()` with the manual `safe_specgram()` implementation that floors the power spectrum at `1e-10` before the log10 call.

---

### E19 — `AssertionError: Sample rate mismatch: 44100 vs 22050`

**When you see it:** In `snr_test.py` when comparing two files with different sample rates.

**Cause:** The original and stego files have different sample rates. This should never happen if the stego was produced from the original by this encoder, but can occur if you accidentally compare two unrelated files.

**Fix:** Make sure you're comparing `sample.wav` with `encoded_sample.wav` (both produced in the same encoding session). If you resampled either file externally, re-encode.

---

### E20 — SNR reads 0.00 dB *(fixed in latest version)*

**When you see it:** `SNR: 0.00 dB` even though the files look different.

**Cause:** The original `snr_test.py` hardcoded `/ 32768.0` to normalize the original audio — correct only for int16 WAV files. If `sample.wav` is float32 (range ±1.0), dividing by 32768 makes it effectively zero, so the "noise" becomes the entire stego signal.

**Fix (already applied in latest `snr_test.py`):** The `normalize_audio()` function now detects `dtype` automatically and scales correctly for int16, int32, and float32/float64 inputs.

---

### E21 — SNR reads as a very large negative number (e.g., -90 dB)

**When you see it:** When the stego audio sounds noticeably different from the original.

**Cause:** This is not a bug — it means the encoder has significantly altered the audio. Likely causes:
- You encoded into a near-silent audio file (magnitude ≈ 0, so phase changes dominate)
- You encoded an extremely long payload that covers a very wide frequency band
- Your carrier audio has very little high-frequency content (so injecting at 15000 Hz overwrites most of the energy at that band)

**Fix:** Use richer carrier audio (broadband content like music or speech), shorter payloads, and inject at frequencies where the carrier has strong natural energy.

---

## 8. Platform-Specific Errors

---

### E22 — `matplotlib` display errors on headless servers (no GUI)

**When you see it:** `_tkinter.TclError: no display name and no $DISPLAY environment variable` or similar on Linux servers.

**Cause:** `plt.show()` requires a display. Servers and WSL (Windows Subsystem for Linux) without an X server will crash.

**Fix:** Use a non-interactive backend and save to file instead:
```python
import matplotlib
matplotlib.use('Agg')   # Add this BEFORE importing pyplot
import matplotlib.pyplot as plt

# Replace plt.show() with:
plt.savefig('spectrogram_output.png', dpi=150)
print("Spectrogram saved to spectrogram_output.png")
```

---

### E23 — Encoding works but decoded audio sounds different / has artifacts

**When you see it:** Audible metallic or phase artifacts after encoding, especially on tonal audio (piano, sine waves).

**Cause:** Phase steganography works best on broadband, noisy-spectrum audio (speech, drums, ambient sound). On pure tonal audio (a single sine wave), the phase relationship between harmonics is perceptually very significant. Forcing phase to ±π/2 at specific bins will alter the sound noticeably.

**Fix:** Use broadband carrier audio — music with multiple instruments, speech recordings, or nature sounds. Avoid pure tones, synthesized music, or audio with very sparse frequency content.

---

## Quick Diagnostic Checklist

When something goes wrong, run through this in order:

```
□ Is sample.wav in the same folder as the script?
□ Is sample.wav a standard 16-bit PCM WAV (not MP3, not 24-bit)?
□ Is encryption.key present and unchanged since encoding?
□ Is the delimiter in the decoder EXACTLY matching what was typed in the encoder?
□ Is the target frequency below half the sample rate?
□ Does the original audio have real content (not silence)?
□ Are all dependencies installed? (numpy, scipy, matplotlib, cryptography)
```
