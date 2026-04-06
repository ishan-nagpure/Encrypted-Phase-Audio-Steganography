import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile

def analyze(f_orig, f_stego):
    # 1. Load audio
    sr1, o = wavfile.read(f_orig)
    sr2, s = wavfile.read(f_stego)
    
    # Convert to mono if necessary
    if len(o.shape) == 2: o = o.mean(axis=1)
    if len(s.shape) == 2: s = s.mean(axis=1)

    # 2. The Ultimate Normalization
    o_f = o.astype(np.float64)
    s_f = s.astype(np.float64)
    
    # Force both audio arrays to a strict -1.0 to 1.0 scale
    o_f = o_f / np.max(np.abs(o_f))
    s_f = s_f / np.max(np.abs(s_f))

    # 3. Calculate SNR
    noise = o_f - s_f
    p_sig = np.mean(o_f**2)
    p_noise = np.mean(noise**2)
    
    snr = 10 * np.log10(p_sig / p_noise) if p_noise != 0 else float('inf')
    print(f"SNR: {snr:.2f} dB" if snr != float('inf') else "Files identical.")

    # 4. Plot Spectrograms (Using the NORMALIZED data)
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    # Notice we are passing o_f instead of o
    Pxx, freqs, bins, im1 = plt.specgram(o_f, NFFT=1024, Fs=sr1, cmap='magma')
    plt.title('Original Audio')
    #plt.axhline(20000, color='w', ls='--', alpha=0.3)
    plt.ylabel('Frequency (Hz)')
    
    # Grab the color limits
    vmin, vmax = im1.get_clim()
    
    plt.subplot(1, 2, 2)
    # Notice we are passing s_f instead of s
    plt.specgram(s_f, NFFT=1024, Fs=sr2, cmap='magma', vmin=vmin, vmax=vmax)
    plt.title(f'Stego Audio (SNR: {snr:.2f} dB)')
    #plt.axhline(20000, color='w', ls='--', alpha=0.3)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    analyze('sample.wav', 'encoded_sample.wav')