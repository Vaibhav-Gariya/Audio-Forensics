from pedalboard.io import AudioFile
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, NoiseGate
import noisereduce as nr
import numpy as np

# Input / output
input_file = r"C:\Users\Manish\Downloads\audio1.wav"
output_file = "enhanced.wav"

# 1. Load audio
with AudioFile(input_file) as f:
    audio = f.read(f.frames)
    sr = f.samplerate

# Convert stereo -> mono (optional, forensic work often uses mono)
if audio.ndim > 1:
    audio = np.mean(audio, axis=0)

# 2. Pedalboard basic cleanup
board = Pedalboard([
    HighpassFilter(cutoff_frequency_hz=80.0),   # remove rumble
    LowpassFilter(cutoff_frequency_hz=8000.0), # reduce hiss
    NoiseGate(threshold_db=-40, ratio=2.0),    # gate very quiet background
])

processed = board(audio, sr)

# 3. Noise reduction (spectral gating)
reduced_noise = nr.reduce_noise(y=processed, sr=sr)

# 4. Save result
with AudioFile(output_file, 'w', sr, 1) as f:
    f.write(reduced_noise.astype(np.float32))

print("Enhanced audio saved to:", output_file)
