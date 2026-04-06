import numpy as np
import os
from scipy.io import wavfile
from cryptography.fernet import Fernet

# 1. Load the Encryption Key
def get_key():
    if not os.path.exists("encryption.key"):
        raise FileNotFoundError("encryption.key not found! You need the exact key used during encoding.")
    with open("encryption.key", "rb") as f:
        return f.read()

# 2. The Main Decoding Function
def decode_audio(stego_file, delimiter, target_freq):
    print(f"\nLoading '{stego_file}' and extracting data...")

    # Initialize the AES decryption engine
    try:
        cipher = Fernet(get_key())
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return

    # Read the stego audio file
    try:
        sr, audio_data = wavfile.read(stego_file)
    except FileNotFoundError:
        print(f"ERROR: '{stego_file}' not found in this folder.")
        return

    # Convert to mono if it's stereo
    if len(audio_data.shape) == 2:
        audio_data = audio_data.mean(axis=1)

    # Run FFT and extract the phase array
    fft_data = np.fft.fft(audio_data)
    phase = np.angle(fft_data)

    # Calculate the exact target frequency starting bin
    start_idx = int((target_freq * len(audio_data)) / sr)

    # 3. Optimized Extraction Loop
    bits = []
    extracted_text = ""
    idx = start_idx

    print(f"Scanning high-frequency phase angles for delimiter '{delimiter}'...")

    while idx < len(phase) // 2:
        # Pull the bit
        bit = 0 if phase[idx] > 0 else 1
        bits.append(bit)
        idx += 1

        # Every time we get 8 new bits (1 byte)
        if len(bits) % 8 == 0:
            # Grab ONLY the last 8 bits we just added
            current_byte = bits[-8:]
            
            # Convert just that one byte into a character
            char = chr(int(''.join(map(str, current_byte)), 2))
            extracted_text += char
            
            # Print a progress update every 100 characters so you know it's working
            if len(extracted_text) % 100 == 0:
                print(f"Scanned {len(extracted_text)} characters...")

            # Check if our dynamic delimiter is in the text we've built so far
            if delimiter in extracted_text:
                encrypted_payload = extracted_text.replace(delimiter, "")
                break
    else:
        # If the while loop finishes without hitting 'break', the delimiter wasn't there
        print(f"ERROR: Reached the end of the file. No '{delimiter}' delimiter found.")
        print("The audio might have been compressed, corrupted, or you entered the wrong delimiter.")
        return

    # 4. Decrypt the Payload (WITH DIAGNOSTICS)
    try:
        decrypted_message = cipher.decrypt(encrypted_payload.encode()).decode()
        print("\nEXTRACTION SUCCESSFUL!")
        print("-" * 50)
        print(f"Secret Message: {decrypted_message}")
        print("-" * 50)
    except Exception as e:
        print(f"\nDECRYPTION FAILED. Python Error: {e}")
        print("This usually means the wrong key was used, the audio was altered, or the delimiter was incorrect.")
        
# --- Run the Decoder ---
if __name__ == "__main__":
    # Ensure 'encoded_sample.wav' is in the same folder along with your 'encryption.key' file.
    
    # Ask the user for the delimiter so it matches the encoder perfectly
    freq = int(input("Enter the frequency lane you used during encoding (e.g., 5000, 10000, 15000): "))
    user_delimiter = input("Enter the delimiter you used during encoding: ")
    full_delimiter = "###" + user_delimiter + "###"
    
    decode_audio("encoded_sample.wav", full_delimiter, freq)