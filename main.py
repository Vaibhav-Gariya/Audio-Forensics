import os
import hashlib
import numpy as np
import mutagen
import librosa
import librosa.display
import matplotlib.pyplot as plt

# -------------------------------
# CONFIGURATION
# -------------------------------
AUDIO_FILE = "sample.mp3"   # change path if needed
SAVE_GRAPHS = False         # True = save PNG, False = show plots

# -------------------------------
# METADATA EXTRACTION
# -------------------------------
def extract_metadata(file_path):
    audio = mutagen.File(file_path)

    metadata = {}
    if audio and audio.info:
        metadata["Duration (sec)"] = round(audio.info.length, 2)
        metadata["Sample Rate (Hz)"] = audio.info.sample_rate
        metadata["Channels"] = audio.info.channels
        metadata["Bitrate"] = getattr(audio.info, "bitrate", "Unknown")
        metadata["Format"] = file_path.split(".")[-1].upper()
    else:
        metadata["Error"] = "Unsupported or corrupted file"

    return metadata


# -------------------------------
# FILE INTEGRITY (SHA-256)
# -------------------------------
def generate_hash(file_path):
    with open(file_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


# -------------------------------
# COMPRESSION HISTORY CHECK
# -------------------------------
def compression_history_check(y, sr, file_ext):
    S = np.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    avg_spectrum = np.mean(S, axis=1)

    threshold = np.max(avg_spectrum) * 0.001
    significant = freqs[avg_spectrum > threshold]

    cutoff_freq = significant[-1] if len(significant) > 0 else 0

    verdict = "Likely Original / No strong compression traces"

    if file_ext in ["WAV", "FLAC"] and cutoff_freq < 20000:
        verdict = "⚠ Suspicious: Previously lossy-compressed then saved as lossless"
    elif file_ext == "MP3":
        if cutoff_freq < 17000:
            verdict = "Lossy MP3 (~128 kbps)"
        elif cutoff_freq < 19500:
            verdict = "Lossy MP3 (~192 kbps)"
        else:
            verdict = "High-quality MP3 (~320 kbps)"

    return round(cutoff_freq, 2), verdict


# -------------------------------
# VISUALIZATION
# -------------------------------
def visualize_audio(y, sr):
    # Waveform
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr)
    plt.title("Waveform")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")

    if SAVE_GRAPHS:
        plt.savefig("waveform.png")
        plt.close()
    else:
        plt.show()

    # Spectrogram
    plt.figure(figsize=(10, 4))
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(S))
    librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="hz", cmap="magma")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Spectrogram")

    if SAVE_GRAPHS:
        plt.savefig("spectrogram.png")
        plt.close()
    else:
        plt.show()


# -------------------------------
# MAIN EXECUTION
# -------------------------------
def main():
    if not os.path.exists(AUDIO_FILE):
        print(" Audio file not found!")
        return

    print("\n========== AUDIO FORENSICS REPORT ==========\n")

    # Metadata
    metadata = extract_metadata(AUDIO_FILE)
    print("METADATA:")
    for k, v in metadata.items():
        print(f"{k}: {v}")

    # Hash
    file_hash = generate_hash(AUDIO_FILE)
    print("\n SHA-256 HASH:")
    print(file_hash)

    # Load audio
    y, sr = librosa.load(AUDIO_FILE, sr=None)
    file_ext = AUDIO_FILE.split(".")[-1].upper()

    # Compression history
    cutoff, verdict = compression_history_check(y, sr, file_ext)
    print("\n COMPRESSION HISTORY CHECK:")
    print(f"Detected Frequency Cutoff: {cutoff} Hz")
    print(f"Verdict: {verdict}")

    # Visualization
    visualize_audio(y, sr)

    print("\n========== ANALYSIS COMPLETE ==========\n")


if __name__ == "__main__":
    main()
