import hashlib
from mutagen import File

def extract_metadata(file_path):
    audio = File(file_path, easy=True)
    metadata = {}
    
    if audio is not None:
        # Basic properties
        metadata["duration"] = audio.info.length
        metadata["sample_rate"] = audio.info.sample_rate
        metadata["bitrate"] = getattr(audio.info, 'bitrate', 'Unknown')
        metadata["channels"] = audio.info.channels
        
        # Tags (if available)
        if audio.tags:
            for key, value in audio.tags.items():
                metadata[key] = value
    else:
        metadata["error"] = "Unsupported file format"
    
    # Generate file hash (for integrity check)
    with open(file_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    metadata["sha256"] = file_hash
    
    return metadata

# Example use
file_path = "sample.mp3"
info = extract_metadata(file_path)
for key, value in info.items():
    print(f"{key}: {value}")
