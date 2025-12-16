from flask import Flask, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
import os
import base64
import traceback
import json
import uuid

# Import your metadata forensics functions
from metadata import (
    extract_metadata, 
    generate_hash, 
    compression_history_check
)

# Import audio enhancement
from enhancement import enhance_audio

import librosa
import librosa.display
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
PLOT_FOLDER = 'static/plots'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg', 'flac'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Create folders if they don't exist
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, PLOT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Store enhancement results temporarily (in production, use Redis or database)
enhancement_results = {}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_visualizations(y, sr, filename_prefix):
    """Generate waveform and spectrogram and return base64 encoded images"""
    try:
        # Waveform
        plt.figure(figsize=(10, 4))
        librosa.display.waveshow(y, sr=sr)
        plt.title("Waveform")
        plt.xlabel("Time (s)")
        plt.ylabel("Amplitude")
        plt.tight_layout()
        
        waveform_path = os.path.join(app.config['PLOT_FOLDER'], f'waveform_{filename_prefix}.png')
        plt.savefig(waveform_path, bbox_inches='tight', dpi=100)
        plt.close()
        
        # Spectrogram
        plt.figure(figsize=(10, 4))
        S = librosa.stft(y)
        S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)
        librosa.display.specshow(S_db, sr=sr, x_axis='time', y_axis='hz', cmap='magma')
        plt.colorbar(format='%+2.0f dB')
        plt.title("Spectrogram")
        plt.tight_layout()
        
        spectrogram_path = os.path.join(app.config['PLOT_FOLDER'], f'spectrogram_{filename_prefix}.png')
        plt.savefig(spectrogram_path, bbox_inches='tight', dpi=100)
        plt.close()
        
        # Convert images to base64
        with open(waveform_path, 'rb') as f:
            waveform_base64 = base64.b64encode(f.read()).decode()
        
        with open(spectrogram_path, 'rb') as f:
            spectrogram_base64 = base64.b64encode(f.read()).decode()
        
        return waveform_base64, spectrogram_base64
    
    except Exception as e:
        print(f"❌ Error generating visualizations: {e}")
        traceback.print_exc()
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze audio file"""
    print("\n" + "="*60)
    print("🔍 ANALYZE REQUEST RECEIVED")
    print("="*60)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    print(f"📄 Filename from frontend: {file.filename}")
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Supported: WAV, MP3, OGG, FLAC'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        print(f"✅ File saved to: {filepath}")
        
        # 1. Extract metadata
        print("\n1️⃣ Extracting metadata...")
        metadata = extract_metadata(filepath)
        print(f"✅ Metadata: {metadata}")
        
        if metadata is None or "Error" in metadata:
            error_msg = metadata.get("Error", "Failed to extract metadata") if metadata else "Failed to extract metadata"
            return jsonify({'error': error_msg}), 500
        
        # 2. Generate hash
        print("\n2️⃣ Generating hash...")
        file_hash = generate_hash(filepath)
        print(f"✅ Hash: {file_hash[:32]}...")
        
        # 3. Load audio
        print("\n3️⃣ Loading audio...")
        y, sr = librosa.load(filepath, sr=None)
        file_ext = filename.split('.')[-1].upper()
        print(f"✅ Audio loaded: SR={sr}, Duration={len(y)/sr:.2f}s")
        
        # 4. Compression check
        print("\n4️⃣ Checking compression...")
        cutoff_freq, verdict = compression_history_check(y, sr, file_ext)
        print(f"✅ Cutoff: {cutoff_freq} Hz, Verdict: {verdict}")
        
        # 5. Generate visualizations
        print("\n5️⃣ Generating visualizations...")
        waveform_base64, spectrogram_base64 = generate_visualizations(y, sr, filename)
        print(f"✅ Visualizations generated")
        
        # 6. Prepare response
        bitrate = metadata.get('Bitrate', 'Unknown')
        if bitrate != 'Unknown' and isinstance(bitrate, int):
            bitrate = f"{bitrate // 1000} kbps"
        
        response_data = {
            'duration': str(metadata.get('Duration (sec)', 'Unknown')),
            'sample_rate': str(metadata.get('Sample Rate (Hz)', 'Unknown')),
            'channels': str(metadata.get('Channels', 'Unknown')),
            'bitrate': str(bitrate),
            'format': metadata.get('Format', 'Unknown'),
            'sha256_hash': file_hash,
            'compression_verdict': verdict,
            'cutoff_frequency': f"{cutoff_freq} Hz",
            'waveform': f'data:image/png;base64,{waveform_base64}',
            'spectrogram': f'data:image/png;base64,{spectrogram_base64}'
        }
        
        print(f"✅ Response ready!")
        print("="*60 + "\n")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/enhance', methods=['POST'])
def enhance():
    """Enhance audio - Step 1: Process and return session ID"""
    print("\n" + "="*60)
    print("✨ ENHANCE REQUEST RECEIVED")
    print("="*60)
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400
    
    try:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        print(f"📄 Original file saved: {input_path}")
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        print(f"🆔 Session ID: {session_id}")
        
        # Extract original metadata
        print("\n1️⃣ Extracting original metadata...")
        original_metadata = extract_metadata(input_path)
        print(f"✅ Original metadata: {original_metadata}")
        
        # Load original audio
        print("\n2️⃣ Loading original audio...")
        y_original, sr_original = librosa.load(input_path, sr=None)
        print(f"✅ Original audio loaded: SR={sr_original}")
        
        # Generate original visualizations
        print("\n3️⃣ Generating original visualizations...")
        waveform_original, spectrogram_original = generate_visualizations(
            y_original, sr_original, f"original_{session_id}"
        )
        print(f"✅ Original visualizations generated")
        
        # Enhance audio
        output_filename = f'enhanced_{filename.rsplit(".", 1)[0]}.wav'
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        print("\n4️⃣ Enhancing audio...")
        enhance_audio(input_path, output_path)
        print(f"✅ Enhanced file saved: {output_path}")
        
        # Extract enhanced metadata
        print("\n5️⃣ Extracting enhanced metadata...")
        enhanced_metadata = extract_metadata(output_path)
        print(f"✅ Enhanced metadata: {enhanced_metadata}")
        
        # Load enhanced audio
        print("\n6️⃣ Loading enhanced audio...")
        y_enhanced, sr_enhanced = librosa.load(output_path, sr=None)
        print(f"✅ Enhanced audio loaded: SR={sr_enhanced}")
        
        # Generate enhanced visualizations
        print("\n7️⃣ Generating enhanced visualizations...")
        waveform_enhanced, spectrogram_enhanced = generate_visualizations(
            y_enhanced, sr_enhanced, f"enhanced_{session_id}"
        )
        print(f"✅ Enhanced visualizations generated")
        
        # Generate comparison data
        bitrate_original = original_metadata.get('Bitrate', 'Unknown')
        if bitrate_original != 'Unknown' and isinstance(bitrate_original, int):
            bitrate_original = f"{bitrate_original // 1000} kbps"
        
        bitrate_enhanced = enhanced_metadata.get('Bitrate', 'Unknown')
        if bitrate_enhanced != 'Unknown' and isinstance(bitrate_enhanced, int):
            bitrate_enhanced = f"{bitrate_enhanced // 1000} kbps"
        
        comparison_data = {
            'original': {
                'duration': str(original_metadata.get('Duration (sec)', 'Unknown')),
                'sample_rate': str(original_metadata.get('Sample Rate (Hz)', 'Unknown')),
                'channels': str(original_metadata.get('Channels', 'Unknown')),
                'bitrate': str(bitrate_original),
                'format': original_metadata.get('Format', 'Unknown'),
                'waveform': f'data:image/png;base64,{waveform_original}',
                'spectrogram': f'data:image/png;base64,{spectrogram_original}'
            },
            'enhanced': {
                'duration': str(enhanced_metadata.get('Duration (sec)', 'Unknown')),
                'sample_rate': str(enhanced_metadata.get('Sample Rate (Hz)', 'Unknown')),
                'channels': str(enhanced_metadata.get('Channels', 'Unknown')),
                'bitrate': str(bitrate_enhanced),
                'format': enhanced_metadata.get('Format', 'Unknown'),
                'waveform': f'data:image/png;base64,{waveform_enhanced}',
                'spectrogram': f'data:image/png;base64,{spectrogram_enhanced}'
            },
            'original_filename': filename,
            'enhanced_path': output_path,
            'enhanced_filename': output_filename
        }
        
        # Store in temporary storage
        enhancement_results[session_id] = comparison_data
        
        print(f"\n✅ Enhancement complete! Session: {session_id}")
        print("="*60 + "\n")
        
        # Return session ID and basic info
        return jsonify({
            'session_id': session_id,
            'success': True,
            'message': 'Enhancement complete'
        }), 200
        
    except Exception as e:
        print(f"❌ Enhancement error: {str(e)}")
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'error': f'Enhancement failed: {str(e)}'}), 500

@app.route('/enhance/comparison/<session_id>', methods=['GET'])
def get_comparison(session_id):
    """Get comparison data for a session"""
    print(f"\n📊 Fetching comparison data for session: {session_id}")
    
    if session_id not in enhancement_results:
        return jsonify({'error': 'Session not found'}), 404
    
    comparison_data = enhancement_results[session_id]
    print(f"✅ Comparison data found")
    
    return jsonify(comparison_data), 200

@app.route('/enhance/download/<session_id>', methods=['GET'])
def download_enhanced(session_id):
    """Download enhanced audio file"""
    print(f"\n💾 Download request for session: {session_id}")
    
    if session_id not in enhancement_results:
        return jsonify({'error': 'Session not found'}), 404
    
    comparison_data = enhancement_results[session_id]
    output_path = comparison_data['enhanced_path']
    output_filename = comparison_data['enhanced_filename']
    
    if not os.path.exists(output_path):
        return jsonify({'error': 'Enhanced file not found'}), 404
    
    print(f"✅ Sending file: {output_filename}")
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_filename,
        mimetype='audio/wav'
    )

if __name__ == '__main__':
    print("\n🎵 Audio Enhancement Tool")
    print("📁 Upload files from frontend - no hardcoded paths!")
    print("🌐 Server: http://localhost:5000\n")
    app.run(debug=True, host='0.0.0.0', port=5000)