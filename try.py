import mutagen
import hashlib
import librosa, librosa.display
import matplotlib.pyplot as plt

# --- Load file ---
file_path = "sample.mp3"

# --- Metadata extraction ---
audio = mutagen.File(file_path)
print("Duration:", audio.info.length, "seconds")
print("Sample Rate:", audio.info.sample_rate)
print("Channels:", audio.info.channels)

# --- Hash for integrity ---
with open(file_path, "rb") as f:
    sha256_hash = hashlib.sha256(f.read()).hexdigest()
print("SHA-256 Hash:", sha256_hash)

# --- Load for visualization ---
y, sr = librosa.load(file_path, sr=None)

# --- Waveform ---
plt.figure(figsize=(10, 4))
librosa.display.waveshow(y, sr=sr)
plt.title("Waveform")
plt.show()

# --- Spectrogram ---
plt.figure(figsize=(10, 4))
S = librosa.stft(y)
S_db = librosa.amplitude_to_db(abs(S))
librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="hz", cmap="magma")
plt.colorbar(format="%+2.0f dB")
plt.title("Spectrogram")
plt.show()
