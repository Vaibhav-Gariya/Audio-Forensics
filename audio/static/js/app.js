const uploadArea = document.getElementById("uploadArea");
const fileInput = document.getElementById("fileInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const enhanceBtn = document.getElementById("enhanceBtn");
const progressContainer = document.getElementById("progressContainer");
const progressFill = document.getElementById("progressFill");
const status = document.getElementById("status");
const audioPlayer = document.getElementById("audioPlayer");
const audioElement = document.getElementById("audioElement");
const downloadBtn = document.getElementById("downloadBtn");

let currentFile = null;
let enhancedAudioUrl = null;
let currentSessionId = null;

// Drag and Drop handlers
uploadArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  uploadArea.classList.add("dragover");
});

uploadArea.addEventListener("dragleave", () => {
  uploadArea.classList.remove("dragover");
});

uploadArea.addEventListener("drop", (e) => {
  e.preventDefault();
  uploadArea.classList.remove("dragover");
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
});

uploadArea.addEventListener("click", () => {
  fileInput.click();
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    handleFile(e.target.files[0]);
  }
});

function handleFile(file) {
  currentFile = file;
  uploadArea.querySelector("p").textContent = `Selected: ${file.name}`;
  analyzeBtn.disabled = false;
  enhanceBtn.disabled = false;
  status.textContent = "File ready for processing";
  status.className = "status";
  status.style.display = "block";
}

// Function to clear analysis results
function clearAnalysisResults() {
  const resultsContainer = document.getElementById("resultsContainer");
  if (resultsContainer) {
    resultsContainer.style.display = "none";
    resultsContainer.innerHTML = "";
  }
}

// Function to clear enhancement results
function clearEnhancementResults() {
  const comparisonContainer = document.getElementById("comparisonContainer");
  if (comparisonContainer) {
    comparisonContainer.style.display = "none";
    comparisonContainer.innerHTML = "";
  }
  currentSessionId = null;
  enhancedAudioUrl = null;
}

// Smooth progress animation function
function animateProgress(targetPercent, duration = 1000) {
  const currentPercent = parseInt(progressFill.style.width) || 0;
  const increment = (targetPercent - currentPercent) / (duration / 50);
  let current = currentPercent;

  const interval = setInterval(() => {
    current += increment;
    if (
      (increment > 0 && current >= targetPercent) ||
      (increment < 0 && current <= targetPercent)
    ) {
      current = targetPercent;
      clearInterval(interval);
    }
    progressFill.style.width = `${Math.round(current)}%`;
    progressFill.textContent = `${Math.round(current)}%`;
  }, 50);
}

// Analyze Audio
analyzeBtn.addEventListener("click", async () => {
  if (!currentFile) {
    alert("Please select a file first");
    return;
  }

  // Clear enhancement results when starting analysis
  clearEnhancementResults();

  const formData = new FormData();
  formData.append("file", currentFile);

  analyzeBtn.disabled = true;
  enhanceBtn.disabled = true;
  status.textContent = "📤 Uploading file...";
  status.className = "status";
  status.style.display = "block";
  progressContainer.style.display = "block";
  progressFill.style.width = "0%";
  progressFill.textContent = "0%";

  try {
    // Step 1: Upload (0-20%)
    animateProgress(20, 500);
    await new Promise((resolve) => setTimeout(resolve, 500));

    status.textContent = "🔍 Analyzing audio metadata...";
    animateProgress(40, 800);

    // Make the request
    const fetchPromise = fetch("/analyze", {
      method: "POST",
      body: formData,
    });

    // Simulate progress while waiting
    const progressPromise = new Promise((resolve) => {
      setTimeout(() => {
        status.textContent = "🎵 Loading audio data...";
        animateProgress(60, 1000);
      }, 1000);

      setTimeout(() => {
        status.textContent = "📊 Generating visualizations...";
        animateProgress(80, 1000);
      }, 2500);

      setTimeout(() => {
        status.textContent = "🔬 Performing compression analysis...";
        animateProgress(90, 500);
        resolve();
      }, 4000);
    });

    // Wait for both fetch and simulated progress
    const [response] = await Promise.all([fetchPromise, progressPromise]);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Analysis failed");
    }

    const data = await response.json();
    console.log("Received data:", data);

    // Complete progress
    animateProgress(100, 300);
    status.textContent = "✅ Finalizing results...";

    await new Promise((resolve) => setTimeout(resolve, 300));

    // Display results
    displayResults(data);

    status.textContent = "✅ Analysis complete!";
    status.className = "status success";
    status.style.display = "block";
  } catch (error) {
    console.error("Error:", error);
    status.textContent = `❌ Error: ${error.message}`;
    status.className = "status error";
    status.style.display = "block";
    progressFill.style.width = "0%";
    progressFill.textContent = "0%";
  } finally {
    setTimeout(() => {
      progressContainer.style.display = "none";
    }, 1500);
    analyzeBtn.disabled = false;
    enhanceBtn.disabled = false;
  }
});

function displayResults(data) {
  console.log("Displaying results:", data);

  let resultsContainer = document.getElementById("resultsContainer");

  if (!resultsContainer) {
    resultsContainer = document.createElement("div");
    resultsContainer.id = "resultsContainer";
    resultsContainer.className = "results-container";
    document.querySelector(".main-content").appendChild(resultsContainer);
  }

  resultsContainer.innerHTML = `
    <div class="results-panel">
      <h2>📊 Analysis Results</h2>
      
      <div class="results-grid">
        <div class="result-item">
          <span class="result-label">Duration</span>
          <span class="result-value">${data.duration} sec</span>
        </div>
        
        <div class="result-item">
          <span class="result-label">Sample Rate</span>
          <span class="result-value">${data.sample_rate} Hz</span>
        </div>
        
        <div class="result-item">
          <span class="result-label">Channels</span>
          <span class="result-value">${data.channels}</span>
        </div>
        
        <div class="result-item">
          <span class="result-label">Bitrate</span>
          <span class="result-value">${data.bitrate}</span>
        </div>
        
        <div class="result-item">
          <span class="result-label">Format</span>
          <span class="result-value">${data.format}</span>
        </div>
        
        <div class="result-item full-width">
          <span class="result-label">SHA-256 Hash</span>
          <span class="result-value hash">${data.sha256_hash}</span>
        </div>
        
        <div class="result-item full-width compression-verdict">
          <span class="result-label">🔍 Compression Analysis</span>
          <div class="verdict-details">
            <span class="result-value">${data.compression_verdict}</span>
            <span class="cutoff-freq">📊 Cutoff Frequency: ${data.cutoff_frequency}</span>
          </div>
        </div>
      </div>
      
      <div class="visualizations">
        <h3>🎵 Waveform</h3>
        <img src="${data.waveform}" alt="Waveform" class="visualization-img">
        
        <h3>📊 Spectrogram</h3>
        <img src="${data.spectrogram}" alt="Spectrogram" class="visualization-img">
      </div>
    </div>
  `;

  resultsContainer.style.display = "block";
  resultsContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

// Enhance Audio
enhanceBtn.addEventListener("click", async () => {
  if (!currentFile) {
    alert("Please select a file first");
    return;
  }

  // Clear analysis results when starting enhancement
  clearAnalysisResults();

  console.log("🎵 Starting enhancement...");

  const formData = new FormData();
  formData.append("file", currentFile);

  analyzeBtn.disabled = true;
  enhanceBtn.disabled = true;
  status.textContent = "📤 Uploading file...";
  status.className = "status";
  status.style.display = "block";
  progressContainer.style.display = "block";
  progressFill.style.width = "0%";
  progressFill.textContent = "0%";

  try {
    console.log("📤 Sending enhancement request...");

    // Animate progress with status updates
    animateProgress(15, 500);
    await new Promise((resolve) => setTimeout(resolve, 500));

    status.textContent = "🔊 Loading original audio...";
    animateProgress(30, 800);

    const fetchPromise = fetch("/enhance", {
      method: "POST",
      body: formData,
    });

    // Simulate enhancement steps
    const progressPromise = new Promise((resolve) => {
      setTimeout(() => {
        status.textContent = "🎨 Generating original visualizations...";
        animateProgress(45, 1000);
      }, 1200);

      setTimeout(() => {
        status.textContent = "✨ Applying noise reduction...";
        animateProgress(60, 1200);
      }, 2500);

      setTimeout(() => {
        status.textContent = "🔧 Normalizing audio...";
        animateProgress(75, 1000);
      }, 4000);

      setTimeout(() => {
        status.textContent = "📊 Generating enhanced visualizations...";
        animateProgress(90, 800);
        resolve();
      }, 5500);
    });

    // Wait for both
    const [response] = await Promise.all([fetchPromise, progressPromise]);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || "Enhancement failed");
    }

    const data = await response.json();
    currentSessionId = data.session_id;
    console.log("🆔 Session ID:", currentSessionId);

    status.textContent = "📦 Fetching comparison data...";
    animateProgress(95, 500);

    // Step 2: Fetch comparison data
    console.log("📊 Fetching comparison data...");
    const comparisonResponse = await fetch(
      `/enhance/comparison/${currentSessionId}`
    );

    if (!comparisonResponse.ok) {
      throw new Error("Failed to fetch comparison data");
    }

    const comparisonData = await comparisonResponse.json();
    console.log("✅ Comparison data received");

    animateProgress(100, 300);
    status.textContent = "✅ Preparing results...";

    // Create original audio URL
    const originalAudioUrl = window.URL.createObjectURL(currentFile);

    // Create enhanced audio URL
    const enhancedAudioUrl = `/enhance/download/${currentSessionId}`;

    await new Promise((resolve) => setTimeout(resolve, 300));

    // Display before/after comparison with metadata
    console.log("🎨 Displaying comparison...");
    displayEnhancementComparison(
      originalAudioUrl,
      enhancedAudioUrl,
      comparisonData
    );

    status.textContent = "✅ Enhancement complete! Compare before/after below.";
    status.className = "status success";
    status.style.display = "block";
  } catch (error) {
    console.error("❌ Enhancement error:", error);
    status.textContent = `❌ Error: ${error.message}`;
    status.className = "status error";
    status.style.display = "block";
    progressFill.style.width = "0%";
    progressFill.textContent = "0%";
  } finally {
    setTimeout(() => {
      progressContainer.style.display = "none";
    }, 1500);
    analyzeBtn.disabled = false;
    enhanceBtn.disabled = false;
  }
});

function displayEnhancementComparison(
  originalUrl,
  enhancedUrl,
  comparisonData
) {
  console.log("🎨 displayEnhancementComparison called");

  let comparisonContainer = document.getElementById("comparisonContainer");

  if (!comparisonContainer) {
    console.log("⚠️ Creating comparison container");
    comparisonContainer = document.createElement("div");
    comparisonContainer.id = "comparisonContainer";
    comparisonContainer.className = "comparison-container";
    document.querySelector(".main-content").appendChild(comparisonContainer);
  }

  // Build metadata comparison HTML
  let metadataHTML = "";
  if (comparisonData) {
    metadataHTML = `
      <div class="metadata-comparison">
        <h3>📊 Metadata Comparison</h3>
        <div class="metadata-grid">
          <div class="metadata-column">
            <h4>📥 Original</h4>
            <div class="metadata-item">
              <strong>Duration:</strong>
              <span>${comparisonData.original.duration} sec</span>
            </div>
            <div class="metadata-item">
              <strong>Sample Rate:</strong>
              <span>${comparisonData.original.sample_rate} Hz</span>
            </div>
            <div class="metadata-item">
              <strong>Channels:</strong>
              <span>${comparisonData.original.channels}</span>
            </div>
            <div class="metadata-item">
              <strong>Bitrate:</strong>
              <span>${comparisonData.original.bitrate}</span>
            </div>
            <div class="metadata-item">
              <strong>Format:</strong>
              <span>${comparisonData.original.format}</span>
            </div>
          </div>
          
          <div class="metadata-arrow">➡️</div>
          
          <div class="metadata-column enhanced-meta">
            <h4>✨ Enhanced</h4>
            <div class="metadata-item">
              <strong>Duration:</strong>
              <span>${comparisonData.enhanced.duration} sec</span>
            </div>
            <div class="metadata-item">
              <strong>Sample Rate:</strong>
              <span>${comparisonData.enhanced.sample_rate} Hz</span>
            </div>
            <div class="metadata-item">
              <strong>Channels:</strong>
              <span>${comparisonData.enhanced.channels}</span>
            </div>
            <div class="metadata-item">
              <strong>Bitrate:</strong>
              <span>${comparisonData.enhanced.bitrate}</span>
            </div>
            <div class="metadata-item">
              <strong>Format:</strong>
              <span>${comparisonData.enhanced.format}</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Build visualizations comparison HTML
  let visualizationsHTML = "";
  if (
    comparisonData &&
    comparisonData.original.waveform &&
    comparisonData.enhanced.waveform
  ) {
    visualizationsHTML = `
      <div class="visualizations-comparison">
        <h3>📊 Waveform Comparison</h3>
        <div class="viz-grid">
          <div class="viz-column">
            <h4>📥 Original Waveform</h4>
            <img src="${comparisonData.original.waveform}" alt="Original Waveform" class="viz-img">
          </div>
          <div class="viz-column enhanced-viz">
            <h4>✨ Enhanced Waveform</h4>
            <img src="${comparisonData.enhanced.waveform}" alt="Enhanced Waveform" class="viz-img">
          </div>
        </div>
        
        <h3>📈 Spectrogram Comparison</h3>
        <div class="viz-grid">
          <div class="viz-column">
            <h4>📥 Original Spectrogram</h4>
            <img src="${comparisonData.original.spectrogram}" alt="Original Spectrogram" class="viz-img">
          </div>
          <div class="viz-column enhanced-viz">
            <h4>✨ Enhanced Spectrogram</h4>
            <img src="${comparisonData.enhanced.spectrogram}" alt="Enhanced Spectrogram" class="viz-img">
          </div>
        </div>
      </div>
    `;
  }

  comparisonContainer.innerHTML = `
    <div class="comparison-panel">
      <h2>🎧 Before & After Comparison</h2>
      
      ${metadataHTML}
      
      <div class="audio-comparison">
        <div class="audio-item">
          <h3>📥 Original Audio</h3>
          <audio controls>
            <source src="${originalUrl}" type="audio/*">
            Your browser does not support the audio element.
          </audio>
          <p class="audio-label">Original file: ${currentFile.name}</p>
        </div>
        
        <div class="comparison-arrow">➡️</div>
        
        <div class="audio-item enhanced">
          <h3>✨ Enhanced Audio</h3>
          <audio controls>
            <source src="${enhancedUrl}" type="audio/wav">
            Your browser does not support the audio element.
          </audio>
          <p class="audio-label">Enhanced file (WAV format)</p>
        </div>
      </div>
      
      ${visualizationsHTML}
      
      <div class="enhancement-info">
        <h3>🔧 Enhancements Applied:</h3>
        <ul>
          <li>✅ Noise Reduction</li>
          <li>✅ Audio Normalization</li>
          <li>✅ Dynamic Range Compression</li>
          <li>✅ High-pass Filtering (50 Hz)</li>
        </ul>
      </div>
      
      <button class="btn btn-primary download-btn" id="downloadEnhancedBtn">
        💾 Download Enhanced Audio
      </button>
    </div>
  `;

  comparisonContainer.style.display = "block";
  console.log("✅ Comparison container displayed");

  // Add download button event listener
  document
    .getElementById("downloadEnhancedBtn")
    .addEventListener("click", () => {
      console.log("💾 Download button clicked");
      if (currentSessionId) {
        window.location.href = `/enhance/download/${currentSessionId}`;
        console.log("✅ Download initiated");
      }
    });

  comparisonContainer.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
