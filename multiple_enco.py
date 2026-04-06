import numpy as np
import os
from scipy.io import wavfile
from cryptography.fernet import Fernet

# --- 1. Key Management ---
def get_key():
    if not os.path.exists("encryption.key"):
        print("'encryption.key' not found. Generating a new one...")
        with open("encryption.key", "wb") as f:
            f.write(Fernet.generate_key())
    with open("encryption.key", "rb") as f:
        return f.read()
    
# --- 2. Load the Audio ---
try:
    sample_rate, audio_data = wavfile.read('sample.wav')
    if len(audio_data.shape) == 2:
        audio_data = audio_data.mean(axis=1) 
except FileNotFoundError:
    print("ERROR: 'sample.wav' not found.")
    exit()

# --- 3. The Multi-Channel DSP Engine ---
def Multi_Encoding(payload_dict):
    print("\nInitializing Multi-Channel Steganography...")
    f = Fernet(get_key())
    
    # Run Forward FFT once
    fft_data = np.fft.fft(audio_data)
    mag = np.abs(fft_data)
    phase = np.angle(fft_data)
    n = len(audio_data)

    # Loop through the dictionary and inject every frequency lane
    for target_freq, data in payload_dict.items():
        text = data['text']
        delimiter = data['delim']
        
        main = f.encrypt(text.encode()).decode() + delimiter
        binary = ''.join(format(ord(char), '08b') for char in main)
        binary_array = [int(bit) for bit in binary]

        # Calculate exact starting bin for this specific frequency
        idx = int(target_freq * n / sample_rate)
        free= idx + len(binary_array)
        print(f"\nInjecting message at {target_freq} Hz (starting bin: {idx}) with {len(binary_array)} bits... bits available from {free}\n-*check if it overlaps with the other frequencies!*-\n")
        
        # Safety Check
        if len(binary_array) > n // 2 - idx:
            print(f"ERROR: Message at {target_freq}Hz is too long. Skipping.")
            continue

        # Phase Coding
        for i, b in enumerate(binary_array):
            pos = idx + i
            val = np.pi/2 if b == 0 else -np.pi/2
            phase[pos], phase[-pos] = val, -val

    # Rebuild complex signal and run Inverse FFT once
    print("Rebuilding audio waveform...")
    modified_fft = mag * np.exp(1j * phase)
    modified_audio = np.fft.ifft(modified_fft).real
    
    # The Lossless Float32 Normalization
    max_amplitude = np.max(np.abs(modified_audio))
    if max_amplitude > 0:
        modified_audio = (modified_audio / max_amplitude).astype(np.float32)
    else:
        modified_audio = modified_audio.astype(np.float32)
    
    wavfile.write('encoded_sample.wav', sample_rate, modified_audio)
    print("SUCCESS: Multi-channel file saved as 'encoded_sample.wav'")

# --- 4. User Interface ---
if __name__ == "__main__":
    print("=== MULTI-CHANNEL AUDIO STEGANOGRAPHY ===")
    
    try:
        entries = int(input("How many different messages do you want to hide? "))
    except ValueError:
        print("Please enter a valid number.")
        exit()

    # Create an empty dictionary to hold all our payloads
    master_payloads = {}

    for i in range(entries):
        print(f"\n--- Message {i + 1} ---")
        my_text = input("Enter the secret text: ")
        de = input("Enter the delimiter: ")
        
        try:
            freq = int(input("Enter the frequency lane in Hz ascending order (e.g., 5000, 10000, 15000): "))
        except ValueError:
            print("Invalid frequency. Skipping this entry.")
            continue
            
        # Add to dictionary. 
        # Note: If you enter the exact same frequency twice, it overwrites the previous one!
        master_payloads[freq] = {
            "text": my_text,
            "delim": "###" + de + "###"
        }

    # Pass the fully built dictionary to the DSP engine
    if master_payloads:
        Multi_Encoding(master_payloads)
    else:
        print("No valid payloads to encode.")