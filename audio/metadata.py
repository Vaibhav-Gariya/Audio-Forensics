import mutagen
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
import hashlib
import librosa
import librosa.display
import matplotlib.pyplot as plt
import numpy as np
import os

# -------------------------------
# METADATA EXTRACTION
# -------------------------------
def extract_metadata(file_path):
    """Extract metadata from audio file"""
    try:
        print(f"   📁 Reading file: {file_path}")
        print(f"   📁 File exists: {os.path.exists(file_path)}")
        print(f"   📁 File size: {os.path.getsize(file_path)} bytes")
        
        file_ext = file_path.split('.')[-1].lower()
        
        # Try loading with mutagen
        audio = None
        try:
            if file_ext == 'mp3':
                audio = MP3(file_path)
            elif file_ext == 'wav':
                audio = WAVE(file_path)
            elif file_ext == 'ogg':
                audio = OggVorbis(file_path)
            elif file_ext == 'flac':
                audio = FLAC(file_path)
            else:
                audio = mutagen.File(file_path)
        except Exception as mutagen_error:
            print(f"   ⚠️ Mutagen error: {mutagen_error}")
            audio = None
        
        print(f"   📁 Audio object: {audio}")
        print(f"   📁 Audio type: {type(audio).__name__ if audio else 'None'}")
        print(f"   📁 Has info attr: {hasattr(audio, 'info') if audio else False}")
        print(f"   📁 Info object: {audio.info if audio and hasattr(audio, 'info') else 'None'}")
        
        # If mutagen fails, use librosa to get basic info
        if not audio or not hasattr(audio, 'info') or not audio.info:
            print(f"   ⚠️ Mutagen failed, using librosa as fallback...")
            
            # Use librosa to get metadata
            y, sr = librosa.load(file_path, sr=None)
            duration = len(y) / sr
            
            # Try to get more info from librosa
            import soundfile as sf
            try:
                info = sf.info(file_path)
                metadata = {
                    "Duration (sec)": round(duration, 2),
                    "Sample Rate (Hz)": sr,
                    "Channels": info.channels,
                    "Bitrate": sr * info.channels * 16,  # Assuming 16-bit
                    "Format": file_ext.upper()
                }
                print(f"   ✅ Metadata extracted using soundfile!")
                return metadata
            except:
                # Minimal metadata from librosa
                metadata = {
                    "Duration (sec)": round(duration, 2),
                    "Sample Rate (Hz)": sr,
                    "Channels": 1 if len(y.shape) == 1 else y.shape[0],
                    "Bitrate": "Unknown",
                    "Format": file_ext.upper()
                }
                print(f"   ✅ Metadata extracted using librosa!")
                return metadata
        
        # If mutagen worked, extract metadata
        metadata = {}
        metadata["Duration (sec)"] = round(audio.info.length, 2)
        metadata["Sample Rate (Hz)"] = audio.info.sample_rate
        metadata["Channels"] = audio.info.channels
        
        # Bitrate calculation
        if file_ext == 'wav':
            bits_per_sample = getattr(audio.info, 'bits_per_sample', 16)
            bitrate = audio.info.sample_rate * audio.info.channels * bits_per_sample
            metadata["Bitrate"] = bitrate
        else:
            metadata["Bitrate"] = getattr(audio.info, "bitrate", "Unknown")
        
        metadata["Format"] = file_ext.upper()
        
        print(f"   ✅ Metadata extracted successfully!")
        return metadata
        
    except Exception as e:
        print(f"   ❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"Error": f"{type(e).__name__}: {str(e)}"}


# -------------------------------
# FILE INTEGRITY (SHA-256)
# -------------------------------
def generate_hash(file_path):
    """Generate SHA-256 hash for file integrity"""
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"   ❌ Hash error: {e}")
        return f"Error: {str(e)}"


# -------------------------------
# COMPRESSION HISTORY CHECK
# -------------------------------
def compression_history_check(y, sr, file_ext):
    """Check compression history of audio file"""
    try:
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
        elif file_ext == "OGG":
            if cutoff_freq < 16000:
                verdict = "Low quality OGG"
            elif cutoff_freq < 19000:
                verdict = "Medium quality OGG"
            else:
                verdict = "High quality OGG"

        return round(cutoff_freq, 2), verdict
    except Exception as e:
        print(f"   ❌ Compression check error: {e}")
        return 0, f"Error: {str(e)}"


# -------------------------------
# VISUALIZATION (Optional - for standalone use)
# -------------------------------
def visualize_audio(y, sr):
    """Generate waveform and spectrogram visualizations"""
    plt.figure(figsize=(10, 4))
    librosa.display.waveshow(y, sr=sr)
    plt.title("Waveform")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.show()

    plt.figure(figsize=(10, 4))
    S = librosa.stft(y)
    S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
    librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="hz", cmap="magma")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Spectrogram")
    plt.show()


# -------------------------------
# STANDALONE TESTING ONLY
# -------------------------------
def main():
    """Test function - NOT USED BY FLASK APP!"""
    print("\n⚠️  STANDALONE TEST MODE - NOT USED BY FLASK!\n")
    
    test_file = r"C:\Users\Manish\PY AND FWD\audio\enhanced.wav"
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return
    
    print("="*60)
    print("TESTING metadata.py")
    print("="*60)
    
    metadata = extract_metadata(test_file)
    print(f"\nMetadata: {metadata}")
    
    file_hash = generate_hash(test_file)
    print(f"\nHash: {file_hash[:32]}...")
    
    y, sr = librosa.load(test_file, sr=None)
    file_ext = test_file.split(".")[-1].upper()
    cutoff, verdict = compression_history_check(y, sr, file_ext)
    print(f"\nCutoff: {cutoff} Hz")
    print(f"Verdict: {verdict}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()