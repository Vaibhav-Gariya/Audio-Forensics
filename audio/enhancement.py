from pedalboard.io import AudioFile
from pedalboard import Pedalboard, HighpassFilter, LowpassFilter, NoiseGate
import noisereduce as nr
import numpy as np
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def enhance_audio(input_file, output_file="enhanced.wav", verbose=False):
    """
    Enhance audio by removing noise and applying filtering.
    
    Args:
        input_file: Path to input audio file
        output_file: Path to save enhanced audio
        verbose: Enable detailed logging
    """
    try:
        # Validate input file exists
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        logger.info(f"Loading audio from: {input_file}")
        
        # 1. Load audio
        with AudioFile(str(input_file)) as f:
            audio = f.read(f.frames)
            sr = f.samplerate
        
        logger.info(f"Sample rate: {sr} Hz, Duration: {audio.shape[1]/sr:.2f}s")
        
        # Convert stereo -> mono (optional, forensic work often uses mono)
        if audio.shape[0] > 1:
            audio = np.mean(audio, axis=0)
            logger.info("Converted stereo to mono")
        else:
            audio = audio[0]  # Get first channel if mono
        
        # 2. Pedalboard basic cleanup
        board = Pedalboard([
            HighpassFilter(cutoff_frequency_hz=80.0),    # remove rumble
            LowpassFilter(cutoff_frequency_hz=8000.0),   # reduce hiss
            NoiseGate(threshold_db=-40, ratio=2.0),      # gate quiet background
        ])
        
        logger.info("Applying pedalboard filters...")
        processed = board(audio, sr)
        
        # 3. Noise reduction (spectral gating)
        logger.info("Reducing noise...")
        reduced_noise = nr.reduce_noise(y=processed, sr=sr)
        
        # Normalize to prevent clipping
        max_val = np.max(np.abs(reduced_noise))
        if max_val > 0:
            if max_val > 1.0:
                reduced_noise = reduced_noise / max_val
                logger.info("Normalized audio to prevent clipping")
        
        # 4. Save result
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving enhanced audio to: {output_file}")
        
        # Ensure audio is 2D array for AudioFile
        if reduced_noise.ndim == 1:
            reduced_noise = reduced_noise.reshape(1, -1)
        
        with AudioFile(str(output_path), 'w', sr, reduced_noise.shape[0]) as f:
            f.write(reduced_noise.astype(np.float32))
        
        logger.info("✓ Audio enhancement completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error during audio enhancement: {e}")
        import traceback
        traceback.print_exc()  # Print full error for debugging
        return False

# Main execution
if __name__ == "__main__":
    # Use your ORIGINAL audio file (the one you want to enhance)
    input_file = r"C:\Users\Manish\Downloads\audio1.wav"  # Your source file
    output_file = r"C:\Users\Manish\PY AND FWD\audio\enhanced.wav"  # Output will be saved here
    
    enhance_audio(input_file, output_file, verbose=True)
