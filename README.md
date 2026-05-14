# SpectraMux — Multi-Band Phase Steganography (MBPS)

> **Hide encrypted payloads inside audio files using frequency-domain phase manipulation — completely invisible to the human ear.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://www.python.org/)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-green)](LICENSE)
[![DSP](https://img.shields.io/badge/Domain-Signal%20Processing-orange)]()
[![Crypto](https://img.shields.io/badge/Encryption-AES%20%28Fernet%29-red)]()

---

## What Is SpectraMux?

SpectraMux is an advanced Python-based **Digital Signal Processing (DSP) and cybersecurity suite** that functions as an acoustic **Frequency Division Multiplexer (FDM)**.

It allows users to **securely embed, isolate, and extract multiple AES-encrypted text payloads** within specific frequency lanes of a single standard `.wav` audio file.

Unlike traditional steganography (e.g., LSB encoding) that manipulates audio *samples in time*, SpectraMux operates entirely **in the frequency domain**. It achieves near-perfect stealth by manipulating the microscopic **phase angles** of the carrier audio's waveform while leaving the original **magnitude (volume) completely untouched** — making it perceptually and spectrographically invisible.

---

## How It Works

```
Carrier Audio (.wav)
        │
        ▼
  FFT (numpy.fft)
        │
  ┌─────┴──────────────────────────────────┐
  │  Separate: Magnitude  |  Phase         │
  └────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              │  Force phase at target bin:     │
              │   bit 0 → +π/2                  │
              │   bit 1 → −π/2                  │
              └────────────────┬────────────────┘
                               │
                    Apply Hermitian Symmetry
                               │
                        IFFT → .wav output
```

Each payload is **AES-encrypted** before injection. Even if an attacker identifies the correct frequency lane and extracts the binary phase data, they only recover a cryptographic token.

---

## Key Features

| Feature | Detail |
|---|---|
| **Frequency Division Multiplexing** | Multiple payloads injected into isolated frequency lanes (e.g., 5 kHz, 12 kHz) with zero bandwidth bleed |
| **Phase-Only Encoding** | Magnitude spectrum is completely untouched — no audible artifacts |
| **AES Encryption (Fernet)** | All payloads are encrypted before injection |
| **32-bit Float Architecture** | Prevents int16 overflow clipping and bit-death during IFFT |
| **Hermitian Symmetry Enforcement** | Guarantees a valid, playable real-valued waveform after IFFT |
| **Built-in SNR Analyzer** | Verifies stealth via Signal-to-Noise Ratio and spectrogram comparison |

---

## Repository Structure

```
Encrypted-Phase-Audio-Steganography/
├── multiple_enco.py      # Multi-channel encoder — embeds multiple payloads
├── decoder.py            # Targeted receiver — extracts and decrypts a payload
├── snr_test.py           # DSP analyzer — verifies stealth via SNR + spectrograms
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/ishan-nagpure/Encrypted-Phase-Audio-Steganography.git
cd Encrypted-Phase-Audio-Steganography
```

**2. Install dependencies**

```bash
pip install -r requirements.txt
```

**Dependencies:** `numpy`, `scipy`, `matplotlib`, `cryptography`

---

## Usage

### 1. Encode — Embed Multiple Payloads

`multiple_enco.py` ingests a dictionary of payloads, assigns each to an isolated frequency lane, verifies no bandwidth overlap, and injects all payloads simultaneously into the carrier wave.

```bash
python multiple_enco.py
```

Inside the script, configure your payloads like this:

```python
CARRIER_FILE  = "input.wav"
OUTPUT_FILE   = "stego_output.wav"
FERNET_KEY    = b"<your-base64-fernet-key>"  # Generate with Fernet.generate_key()

payloads = {
    5000:  "Secret message on the 5kHz lane.",
    12000: "Another payload on the 12kHz lane.",
}
```

Each frequency value (Hz) becomes a dedicated, non-overlapping data channel.

---

### 2. Decode — Extract and Decrypt a Payload

`decoder.py` is a tunable extraction engine. Specify the target frequency lane and your delimiter; it skips all other bands, isolates the phase array, rebuilds the binary stream, and decrypts the AES payload.

```bash
python decoder.py
```

Configure the extraction target:

```python
STEGO_FILE    = "stego_output.wav"
FERNET_KEY    = b"<your-base64-fernet-key>"
TARGET_FREQ   = 12000   # Hz — the lane to decode
DELIMITER     = "###"   # Must match what was used during encoding
```

---

### 3. Analyze — Verify Stealth with SNR & Spectrograms

`snr_test.py` is a built-in diagnostic tool. It loads both the original and steganographic audio, performs a normalized apples-to-apples comparison, calculates the exact **Signal-to-Noise Ratio (SNR)**, and renders a side-by-side **heat-mapped spectrogram** using `matplotlib`.

```bash
python snr_test.py
```

Configure the comparison:

```python
ORIGINAL_FILE = "input.wav"
STEGO_FILE    = "stego_output.wav"
```

---

## Core Engineering Challenges Solved

**Eliminated Phase Smearing**
Avoided metallic/robotic acoustic artifacts by refusing to manipulate the magnitude of the carrier signal — all data is carried in phase variance only.

**Apples-to-Apples SNR Scaling**
Solved false-alarm noise floor readings in testing by dynamically scaling `int16` and `float32` arrays to equivalent maximum amplitudes before calculating SNR.

**Prevented Bit-Death**
Switched from integer audio saving to 32-bit floating-point arrays to prevent fractional IFFT results from rounding hidden phase bits down to zero.

**Solved int16 Overflow (Clipping)**
Implemented a high-resolution `float32` normalization architecture that scales the waveform precisely between `-1.0` and `1.0`, preserving microscopic phase changes without amplifying noise.

---

## Technical Architecture

### Frequency Division Multiplexing (FDM)
The audio spectrum is treated like a digital radio broadcast. Each payload is assigned to an isolated "lane" at a specific Hz target. The DSP engine calculates the exact FFT bin index for each frequency, ensuring payloads are mathematically separated with no inter-channel bleed.

### Phase-Coded Injection (FFT / IFFT)
```
numpy.fft → complex frequency components
    → separate Magnitude (loudness) and Phase (timing)
    → force phase at target bins:
          bit 0  →  +π/2
          bit 1  →  −π/2
    → enforce Hermitian symmetry
    → numpy.ifft → real-valued, playable audio
```

### Cryptographic Encapsulation
Payloads are padded with a unique delimiter, then encrypted with **symmetric AES cryptography** via `cryptography.fernet`. The binary stream injected into the audio represents a ciphertext token — raw text is never embedded.

---

## Potential Applications

- **Covert Communications** — Transmit sensitive data over monitored audio channels (VoIP, radio broadcasts) with no detectable signal.
- **Audio Watermarking** — Embed invisible, unbreakable copyright information or tracking IDs into digital music tracks or corporate audio assets.
- **Data Integrity Verification** — Detect tampering or deepfakes in audio recordings by verifying continuity of the hidden phase wave.

---

## Security Notes

- This project is intended for **research, education, and authorized use** only.
- The security of the hidden data depends entirely on the secrecy of the Fernet key. Store and transmit keys through a separate secure channel.
- Phase steganography is not a substitute for transport-layer security in production systems.

---

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See [LICENSE](LICENSE) for full terms.

---

## Author

**Ishan Nagpure** — [github.com/ishan-nagpure](https://github.com/ishan-nagpure)
