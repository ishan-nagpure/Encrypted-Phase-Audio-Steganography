import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

def normalize_audio(arr):
    """
    FIX (Critical): Replaced the hardcoded / 32768.0 with dtype-aware normalization.

    The old code did: o_f = o.astype(np.float64) / 32768.0
    This ONLY works if sample.wav is int16. If it is float32 (range -1 to 1),
    dividing by 32768 makes o_f values microscopic (~0.00003), while s_f stays
    in [-1, 1]. The subtraction noise = o_f - s_f becomes approximately -s_f,
    making p_noise ≈ p_signal and SNR collapses to 0 dB — even if the audio
    is perfectly steganographic.

    The fix detects the actual dtype and scales accordingly so both arrays
    always land in the same [-1.0, 1.0] space before comparison.
    """
    arr_f = arr.astype(np.float64)
    if arr.dtype == np.int16:
        return arr_f / 32768.0
    elif arr.dtype == np.int32:
        return arr_f / 2147483648.0
    else:
        # float32 or float64: already in [-1, 1] range from the encoder
        peak = np.max(np.abs(arr_f))
        return arr_f / peak if peak > 0 else arr_f

def analyze(f_orig, f_stego):
    # 1. Load audio
    sr1, o = wavfile.read(f_orig)
    sr2, s = wavfile.read(f_stego)

    # FIX: assert sample rates match before doing any math
    assert sr1 == sr2, f"Sample rate mismatch: {sr1} vs {sr2}"

    # Convert to mono if necessary
    if len(o.shape) == 2: o = o.mean(axis=1)
    if len(s.shape) == 2: s = s.mean(axis=1)

    # 2. Dtype-aware normalization — both arrays land in [-1.0, 1.0]
    o_f = normalize_audio(o)
    s_f = normalize_audio(s)

    # 3. Trim to same length before subtraction
    # FIX: without this guard, mismatched lengths crash with a shape error
    min_len = min(len(o_f), len(s_f))
    o_f, s_f = o_f[:min_len], s_f[:min_len]

    # 4. Calculate SNR
    noise = o_f - s_f
    p_sig   = np.mean(o_f**2)
    p_noise = np.mean(noise**2)

    snr = 10 * np.log10(p_sig / p_noise) if p_noise != 0 else float('inf')
    print(f"SNR: {snr:.2f} dB" if snr != float('inf') else "Files identical.")

    # 5. Plot Spectrograms (using the normalized, same-scale data)
    plt.figure(figsize=(12, 5))

    plt.subplot(1, 2, 1)
    Pxx, freqs, bins, im1 = plt.specgram(o_f, NFFT=1024, Fs=sr1, cmap='magma')
    plt.title('Original Audio')
    plt.ylabel('Frequency (Hz)')

    # Lock color scale from original so both plots are visually comparable
    vmin, vmax = im1.get_clim()

    plt.subplot(1, 2, 2)
    plt.specgram(s_f, NFFT=1024, Fs=sr2, cmap='magma', vmin=vmin, vmax=vmax)
    plt.ylabel('Frequency (Hz)')

    # FIX: inf SNR caused ValueError with :.2f format specifier
    snr_label = f"{snr:.2f} dB" if snr != float('inf') else "∞ (identical)"
    plt.title(f'Stego Audio (SNR: {snr_label})')

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    analyze('sample.wav', 'encoded_sample.wav')
