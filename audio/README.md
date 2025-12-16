Audio Enhancement & Forensics Tool

A professional web application for audio analysis and enhancement with before/after comparison.

Features

Audio Analysis**

- Metadata extraction (Duration, Sample Rate, Channels, Bitrate, Format)
- SHA-256 hash generation for file integrity
- Compression history detection
- Waveform & spectrogram visualization

Audio Enhancement**

- Noise reduction
- Audio normalization
- Dynamic range compression
- High-pass filtering
- Before/after comparison with visualizations

## Installation

```bash
# Clone repository
git clone <your-repo-url>
cd audio

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

Usage

```bash
# Run the application
python app.py

# Open browser
http://localhost:5000
```

Tech Stack

- **Backend:** Flask (Python)
- **Audio Processing:** librosa, scipy, noisereduce
- **Visualization:** matplotlib
- **Frontend:** HTML, CSS, JavaScript
- **Metadata:** mutagen

Project Structure

```
audio/
├── app.py              # Flask backend
├── metadata.py         # Audio forensics
├── enhancement.py      # Audio enhancement
├── templates/          # HTML templates
├── static/             # CSS, JS, plots
├── uploads/            # User uploads (gitignored)
└── outputs/            # Enhanced files (gitignored)
```

