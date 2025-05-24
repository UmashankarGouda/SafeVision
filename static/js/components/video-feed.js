// Initialize socket with explicit options for reliability
const socket = io({
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  timeout: 20000,
  forceNew: true,
});
const canvas = document.getElementById("video-canvas");
const ctx = canvas.getContext("2d");
const video = document.getElementById("video-element");
const statusDiv = document.getElementById("camera-status");
const analysisDiv = document.getElementById("analysis-info");
const switchCameraBtn = document.getElementById("switch-camera-btn");
const toggleRecordingBtn = document.getElementById("toggle-recording-btn");
const restartFeedBtn = document.getElementById("restart-feed-btn");

let isStreaming = false;
let frameInterval;
let frameCount = 0;
let analysisCount = 0;
let lastProcessedFrameTime = 0;
let processingTimeoutWarning = null;

// Advanced frame throttling variables
let pendingFrames = 0; // Track frames sent but not yet processed
let lastFrameSentTime = 0;
let currentAdaptiveFrameRate = 5; // Start with default
let processingLatencies = []; // Track processing times
let frameDropCount = 0; // Track dropped frames
let isFrameBeingProcessed = false;
let currentFacingMode = "user"; // "user" for front camera, "environment" for rear camera
let currentStream = null;
let isRecording = false;
let recordingStartTime = null;
let settings = {}; // Will be loaded from localStorage

// Load settings from localStorage or use defaults
function loadSettings() {
  const defaultSettings = {
    frameRate: 5, // Reduced from 10 to 5 FPS for better server performance
    videoQuality: 0.8,
    cameraFacing: "user",
    resolution: "640x480",
    webpQuality: 80,
    enableRecording: true,
    maxRecordingDuration: 5,
    mobileOptimizations: true,
    adaptiveFrameRate: true, // New: Adapt frame rate based on server processing
    maxFrameRate: 10, // Maximum frame rate allowed
    minFrameRate: 2, // Minimum frame rate to maintain
  };

  const saved = localStorage.getItem("safeVisionSettings");
  settings = saved
    ? { ...defaultSettings, ...JSON.parse(saved) }
    : defaultSettings;

  // Apply loaded settings
  currentFacingMode = settings.cameraFacing;

  // Update video dimensions based on resolution setting
  const [width, height] = settings.resolution.split("x").map(Number);
  canvas.width = width;
  canvas.height = height;
  video.width = width;
  video.height = height;

  // Show/hide recording button based on settings
  if (!settings.enableRecording) {
    toggleRecordingBtn.style.display = "none";
  }
}

// Make applySettings function available globally for settings page
window.applySettings = function (newSettings) {
  settings = newSettings;
  currentFacingMode = settings.cameraFacing;

  // Update video dimensions
  const [width, height] = settings.resolution.split("x").map(Number);
  canvas.width = width;
  canvas.height = height;
  video.width = width;
  video.height = height;

  // Restart camera with new settings if currently active
  if (currentStream) {
    stopFrameCapture();
    initCamera(currentFacingMode);
  }
};
// Initialize browser camera
async function initCamera(facingMode = "user") {
  try {
    statusDiv.textContent = "Requesting camera access...";

    // Stop existing stream if any
    if (currentStream) {
      currentStream.getTracks().forEach((track) => track.stop());
    }
    const constraints = {
      video: {
        width: { ideal: canvas.width },
        height: { ideal: canvas.height },
        facingMode: facingMode,
      },
      audio: false,
    };

    // Try with facingMode first, fallback without it if not supported
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    } catch (error) {
      console.warn(
        "Specific facing mode not supported, trying without facingMode:",
        error
      );
      delete constraints.video.facingMode;
      stream = await navigator.mediaDevices.getUserMedia(constraints);
    }

    currentStream = stream;
    currentFacingMode = facingMode;
    video.srcObject = stream;
    statusDiv.textContent = `Camera connected (${
      facingMode === "user" ? "Front" : "Rear"
    })`;
    statusDiv.style.color = "#4CAF50";
    statusDiv.className = "status-active";

    // Show camera switch button on mobile devices
    if (isMobileDevice()) {
      switchCameraBtn.style.display = "inline-block";
    }
    video.onloadedmetadata = () => {
      video.play();
      statusDiv.textContent = `Camera active (${
        facingMode === "user" ? "Front" : "Rear"
      }) - Waiting for server processing...`;

      // Show loading state on canvas until first processed frame arrives
      showLoadingState();
      startFrameCapture();

      // Set up failsafe timer to ensure video always shows
      setupProcessingFailsafe();
    };
  } catch (error) {
    console.error("Error accessing camera:", error);
    statusDiv.textContent = "Camera access denied or not available";
    statusDiv.style.color = "#ff6b6b";
    statusDiv.className = "status-error";

    // Show helpful error message
    if (error.name === "NotAllowedError") {
      statusDiv.textContent =
        "Camera permission denied. Please allow camera access and refresh.";
    } else if (error.name === "NotFoundError") {
      statusDiv.textContent =
        "No camera found. Please connect a camera and refresh.";
    } else if (error.name === "NotSupportedError") {
      statusDiv.textContent = "Camera not supported by this browser.";
    }
  }
}
// Show loading state on canvas
let spinnerAngle = 0;
let loadingAnimationFrame = null;

function showLoadingState() {
  function animateLoading() {
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw loading message
    ctx.fillStyle = "#ffffff";
    ctx.font = "20px Arial";
    ctx.textAlign = "center";
    ctx.fillText(
      "Processing frames on server...",
      canvas.width / 2,
      canvas.height / 2 - 30
    );

    ctx.font = "14px Arial";
    ctx.fillText(
      "Your camera feed is being processed for privacy",
      canvas.width / 2,
      canvas.height / 2
    );

    // Draw animated loading spinner
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2 + 40;
    const radius = 15;

    ctx.strokeStyle = "#4CAF50";
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.arc(
      centerX,
      centerY,
      radius,
      spinnerAngle,
      spinnerAngle + Math.PI * 1.5
    );
    ctx.stroke();

    // Add dots around spinner
    for (let i = 0; i < 8; i++) {
      const angle = (i * Math.PI * 2) / 8 + spinnerAngle;
      const dotX = centerX + Math.cos(angle) * (radius + 8);
      const dotY = centerY + Math.sin(angle) * (radius + 8);
      const opacity = Math.max(0.3, 1 - i * 0.1);

      ctx.fillStyle = `rgba(76, 175, 80, ${opacity})`;
      ctx.beginPath();
      ctx.arc(dotX, dotY, 2, 0, Math.PI * 2);
      ctx.fill();
    }

    spinnerAngle += 0.1;
    if (spinnerAngle > Math.PI * 2) spinnerAngle = 0;

    loadingAnimationFrame = requestAnimationFrame(animateLoading);
  }

  if (loadingAnimationFrame) {
    cancelAnimationFrame(loadingAnimationFrame);
  }
  animateLoading();
}

function stopLoadingState() {
  if (loadingAnimationFrame) {
    cancelAnimationFrame(loadingAnimationFrame);
    loadingAnimationFrame = null;
  }
}

// Check if device is mobile
function isMobileDevice() {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
}

// Switch between front and rear camera
async function switchCamera() {
  const newFacingMode = currentFacingMode === "user" ? "environment" : "user";
  stopFrameCapture();
  await initCamera(newFacingMode);
}
function startFrameCapture() {
  if (isStreaming) return;
  isStreaming = true;

  // Reset frame throttling variables
  pendingFrames = 0;
  lastFrameSentTime = 0;
  currentAdaptiveFrameRate = settings.frameRate;
  processingLatencies = [];
  frameDropCount = 0;

  // Use adaptive frame rate if enabled
  const getEffectiveFrameRate = () => {
    if (!settings.adaptiveFrameRate) {
      return settings.frameRate;
    }
    return Math.max(
      settings.minFrameRate,
      Math.min(settings.maxFrameRate, currentAdaptiveFrameRate)
    );
  };

  // Capture and send frames to server with intelligent throttling
  frameInterval = setInterval(() => {
    if (video.readyState === video.HAVE_ENOUGH_DATA) {
      const now = Date.now();
      const effectiveFrameRate = getEffectiveFrameRate();
      const minInterval = 1000 / effectiveFrameRate;

      // Check if enough time has passed since last frame
      if (now - lastFrameSentTime < minInterval) {
        return; // Skip this frame - too soon
      }
      // Enhanced frame dropping logic with priority for latest frames
      if (pendingFrames > 3) {
        frameDropCount++;
        // Adaptive dropping - reduce frame rate temporarily when overwhelmed
        if (settings.adaptiveFrameRate) {
          currentAdaptiveFrameRate = Math.max(
            settings.minFrameRate,
            currentAdaptiveFrameRate - 0.5
          );
        }

        // Drop frame but update stats with more detailed info
        const effectiveRate = Math.round(
          settings.adaptiveFrameRate
            ? currentAdaptiveFrameRate
            : settings.frameRate
        );
        statusDiv.textContent = `Camera active (${
          currentFacingMode === "user" ? "Front" : "Rear"
        }) - Server overwhelmed, ${effectiveRate}fps (${frameDropCount} dropped, ${pendingFrames} pending)`;
        statusDiv.style.color = "#ff9800";
        statusDiv.className = "status-warning";
        return;
      }

      // Smart frame skipping - prioritize latest frames
      if (isFrameBeingProcessed && pendingFrames > 1) {
        frameDropCount++;
        // Only skip frames when multiple are already pending
        return;
      }
      frameCount++;
      lastFrameSentTime = now;

      // Calculate dynamic quality based on server performance
      let dynamicQuality = settings.videoQuality;
      if (settings.adaptiveFrameRate) {
        // Reduce quality when server is struggling
        if (pendingFrames > 2) {
          dynamicQuality = Math.max(0.3, settings.videoQuality - 0.3);
        } else if (pendingFrames > 1) {
          dynamicQuality = Math.max(0.5, settings.videoQuality - 0.2);
        } else if (processingLatencies.length > 0) {
          const avgLatency =
            processingLatencies.reduce((a, b) => a + b, 0) /
            processingLatencies.length;
          if (avgLatency > 1000) {
            dynamicQuality = Math.max(0.4, settings.videoQuality - 0.2);
          }
        }
      }

      // Create a temporary canvas to capture the frame without displaying it
      const tempCanvas = document.createElement("canvas");
      tempCanvas.width = canvas.width;
      tempCanvas.height = canvas.height;
      const tempCtx = tempCanvas.getContext("2d");

      // Draw video frame to temporary canvas (not visible to user)
      tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);
      // Convert temporary canvas to blob and send to server
      tempCanvas.toBlob(
        (blob) => {
          if (blob) {
            // Check max recording duration if recording is active
            if (isRecording && settings.enableRecording && recordingStartTime) {
              const recordingDuration =
                (Date.now() - recordingStartTime) / 1000 / 60; // minutes
              if (recordingDuration >= settings.maxRecordingDuration) {
                stopRecording();
              }
            }

            const reader = new FileReader();
            reader.onload = () => {
              const arrayBuffer = reader.result;
              const frameSentTime = Date.now();

              // Mark frame as being processed
              isFrameBeingProcessed = true;
              pendingFrames++;

              // Fix: Send only the frame data first (to maintain compatibility)
              // Then add metadata as separate properties
              socket.emit("process_frame", {
                frame: arrayBuffer,
                timestamp: frameSentTime,
                frameId: frameCount,
                quality: dynamicQuality,
              });

              // Set up timeout warning if no processed frames are received
              if (!processingTimeoutWarning) {
                processingTimeoutWarning = setTimeout(() => {
                  if (Date.now() - lastProcessedFrameTime > 5000) {
                    // 5 seconds
                    statusDiv.textContent = `Camera active - Server processing slow/unavailable`;
                    statusDiv.style.color = "#ff9800";
                    statusDiv.className = "status-warning";
                  }
                }, 5000);
              }
            };
            reader.readAsArrayBuffer(blob);
          }
        },
        "image/jpeg",
        dynamicQuality // Use dynamic quality instead of fixed
      ); // Update frame count in status with comprehensive throttling info
      const effectiveRate = Math.round(getEffectiveFrameRate());
      const qualityPercent = Math.round(dynamicQuality * 100);

      let statusText = `Camera active (${
        currentFacingMode === "user" ? "Front" : "Rear"
      }) - ${effectiveRate}fps`;

      // Add quality info if it's been reduced
      if (dynamicQuality < settings.videoQuality) {
        statusText += ` (${qualityPercent}% quality)`;
      }

      // Add performance metrics
      if (pendingFrames > 0) {
        statusText += ` - ${pendingFrames} pending`;
      }

      if (frameDropCount > 0) {
        statusText += ` - ${frameDropCount} dropped`;
      }

      statusText += ` - Frame ${frameCount}`;

      statusDiv.textContent = statusText;

      // Color code based on current performance
      if (pendingFrames > 2 || dynamicQuality < settings.videoQuality * 0.8) {
        statusDiv.style.color = "#ff9800"; // Orange for degraded performance
        statusDiv.className = "status-warning";
      } else if (pendingFrames > 0) {
        statusDiv.style.color = "#2196F3"; // Blue for moderate load
        statusDiv.className = "status-sending";
      } else {
        statusDiv.style.color = "#4CAF50"; // Green for optimal
        statusDiv.className = "status-active";
      }
    }
  }, 100); // Check every 100ms but throttle based on frame rate
}

function stopFrameCapture() {
  isStreaming = false;
  if (frameInterval) {
    clearInterval(frameInterval);
    frameInterval = null;
  }
} // Handle processed frames from server
socket.on("processed_frame", (data) => {
  try {
    // Check if frame data exists and is valid
    if (!data || !data.frame || data.frame.byteLength === 0) {
      console.error("Received empty or invalid frame data");
      return;
    }

    const blob = new Blob([data.frame], { type: "image/webp" });
    createImageBitmap(blob)
      .then((imageBitmap) => {
        // Stop loading animation when first processed frame arrives
        stopLoadingState();

        // If we were in fallback mode, disable it since we're receiving frames now
        if (fallbackMode) {
          disableFallbackMode();
        }

        // Reset the failsafe timer since we got a valid frame
        if (processingFailsafeTimer) {
          clearTimeout(processingFailsafeTimer);
        }
        setupProcessingFailsafe();

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(imageBitmap, 0, 0, canvas.width, canvas.height);

        // Update timing and clear any timeout warnings
        const processedTime = Date.now();
        lastProcessedFrameTime = processedTime;
        if (processingTimeoutWarning) {
          clearTimeout(processingTimeoutWarning);
          processingTimeoutWarning = null;
        }

        // Track processing latency for adaptive frame rate
        if (data.timestamp) {
          const latency = processedTime - data.timestamp;
          processingLatencies.push(latency);

          // Keep only last 10 latency measurements
          if (processingLatencies.length > 10) {
            processingLatencies.shift();
          }
          // Adjust adaptive frame rate based on processing performance
          if (settings.adaptiveFrameRate && processingLatencies.length >= 3) {
            const avgLatency =
              processingLatencies.reduce((a, b) => a + b, 0) /
              processingLatencies.length;

            // Adjust frame rate based on latency (slower processing = lower frame rate)
            if (avgLatency > 2000) {
              // >2 seconds is very slow
              currentAdaptiveFrameRate = Math.max(
                settings.minFrameRate,
                currentAdaptiveFrameRate - 1
              );
            } else if (avgLatency > 1000) {
              // >1 second is slow
              currentAdaptiveFrameRate = Math.max(
                settings.minFrameRate,
                currentAdaptiveFrameRate - 0.5
              );
            } else if (avgLatency < 300) {
              // <300ms is fast
              currentAdaptiveFrameRate = Math.min(
                settings.maxFrameRate,
                currentAdaptiveFrameRate + 0.5
              );
            } else if (avgLatency < 500) {
              // <500ms is good
              currentAdaptiveFrameRate = Math.min(
                settings.maxFrameRate,
                currentAdaptiveFrameRate + 0.2
              );
            }

            // Reset towards base frame rate if consistently good performance
            if (
              avgLatency < 400 &&
              pendingFrames === 0 &&
              processingLatencies.length >= 5
            ) {
              const recentLatencies = processingLatencies.slice(-5);
              const allGood = recentLatencies.every((lat) => lat < 500);
              if (allGood && currentAdaptiveFrameRate < settings.frameRate) {
                currentAdaptiveFrameRate = Math.min(
                  settings.frameRate,
                  currentAdaptiveFrameRate + 0.3
                );
              }
            }
          }
        }

        // Decrease pending frame count and mark as no longer processing
        pendingFrames = Math.max(0, pendingFrames - 1);
        isFrameBeingProcessed = false;

        // Update status to show server processing is working with performance info
        if (isStreaming) {
          const avgLatency =
            processingLatencies.length > 0
              ? Math.round(
                  processingLatencies.reduce((a, b) => a + b, 0) /
                    processingLatencies.length
                )
              : 0;
          const effectiveRate = Math.round(
            settings.adaptiveFrameRate
              ? currentAdaptiveFrameRate
              : settings.frameRate
          );

          statusDiv.textContent = `Camera active (${
            currentFacingMode === "user" ? "Front" : "Rear"
          }) - ${effectiveRate}fps (${avgLatency}ms avg) - Frames: ${frameCount}`;

          // Color code based on performance
          if (avgLatency > 1000 || pendingFrames > 2) {
            statusDiv.style.color = "#ff9800"; // Orange for slow
            statusDiv.className = "status-warning";
          } else if (avgLatency > 500 || pendingFrames > 1) {
            statusDiv.style.color = "#2196F3"; // Blue for moderate
            statusDiv.className = "status-sending";
          } else {
            statusDiv.style.color = "#4CAF50"; // Green for good
            statusDiv.className = "status-active";
          }
        }
      })
      .catch((e) => {
        console.error("Error processing frame:", e);
        // Mark as no longer processing even on error
        pendingFrames = Math.max(0, pendingFrames - 1);
        isFrameBeingProcessed = false;
      });
  } catch (error) {
    console.error("Error handling processed frame:", error);
    // Mark as no longer processing even on error
    pendingFrames = Math.max(0, pendingFrames - 1);
    isFrameBeingProcessed = false;
  }
});

// Handle analysis results
socket.on("analysis_result", (data) => {
  analysisCount++;

  // Update analysis display
  const peopleCount = data.people_count || 0;
  const behaviors = data.behaviors || [];
  const behaviorDetected = data.behavior_detected || false;

  let analysisText = `<p>People detected: ${peopleCount}</p>`;
  if (behaviors.length > 0) {
    analysisText += `<p>Behaviors: ${behaviors.join(", ")}</p>`;
  }
  if (behaviorDetected) {
    let warningText = "";
    analysisDiv.style.background = "rgba(200, 200, 0, 0.8)";
    warningText = `<p>⚠️ ALERT: Suspicious behavior detected!</p>`;
    behaviors.forEach((behavior) => {
      if (behavior.toLowerCase().indexOf("panicked") !== -1) {
        warningText += `<p>🚨 Panic detected! Please check the feed.</p>`;
        analysisDiv.style.background = "rgba(255, 0, 0, 0.8)";
      }
    });
    analysisText += warningText;
  } else {
    analysisDiv.style.background = "rgba(0, 0, 0, 0.7)";
  }

  analysisDiv.innerHTML = analysisText;
});
// Handle errors from server
socket.on("error", (data) => {
  console.error("Server error:", data);
  statusDiv.textContent = `Error: ${data.message}`;
  statusDiv.style.color = "#ff6b6b";
  statusDiv.className = "status-error";
});
socket.on("connect", () => {
  console.log("Connected to server - Socket ID: " + socket.id);
  statusDiv.textContent = "Connected to server - Initializing camera...";
  statusDiv.style.color = "#4CAF50";
  statusDiv.className = "status-active";

  // Reset connection-related variables
  processingLatencies = [];
  frameDropCount = 0;
  pendingFrames = 0;

  loadSettings(); // Load settings before initializing camera
  initCamera(settings.cameraFacing);
});

// Add connection error handling
socket.on("connect_error", (error) => {
  console.error("Socket connection error:", error);
  statusDiv.textContent = `Connection error: ${error.message}. Retrying...`;
  statusDiv.style.color = "#ff6b6b";
  statusDiv.className = "status-error";
  stopFrameCapture();

  // Show connection error on canvas
  ctx.fillStyle = "#2c2c2c";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ff6b6b";
  ctx.font = "20px Arial";
  ctx.textAlign = "center";
  ctx.fillText("Connection Error", canvas.width / 2, canvas.height / 2 - 40);
  ctx.font = "14px Arial";
  ctx.fillText(`Error: ${error.message}`, canvas.width / 2, canvas.height / 2);
  ctx.fillText(
    "Attempting to reconnect...",
    canvas.width / 2,
    canvas.height / 2 + 40
  );
});
socket.on("disconnect", () => {
  console.log("Disconnected from server");
  statusDiv.textContent = "Disconnected from server - Reconnecting...";
  statusDiv.style.color = "#ff6b6b";
  statusDiv.className = "status-error";
  stopFrameCapture();

  // Show disconnection state on canvas
  ctx.fillStyle = "#2c2c2c";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ff6b6b";
  ctx.font = "20px Arial";
  ctx.textAlign = "center";
  ctx.fillText(
    "Server Connection Lost",
    canvas.width / 2,
    canvas.height / 2 - 10
  );
  ctx.font = "14px Arial";
  ctx.fillText(
    "Attempting to reconnect...",
    canvas.width / 2,
    canvas.height / 2 + 20
  );
});
// Stop camera when page is unloaded
window.addEventListener("beforeunload", () => {
  stopFrameCapture();
  if (currentStream) {
    currentStream.getTracks().forEach((track) => track.stop());
  }
});

// Handle visibility change (pause when tab is not active)
document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopFrameCapture();
    statusDiv.textContent = "Camera paused (tab not active)";
  } else if (currentStream && !isStreaming) {
    startFrameCapture();
  }
});

// Event listeners for new buttons
switchCameraBtn.addEventListener("click", switchCamera);

toggleRecordingBtn.addEventListener("click", toggleRecording);
restartFeedBtn.addEventListener("click", () => {
  statusDiv.textContent = "Restarting video feed...";
  statusDiv.style.color = "#ff9800";
  statusDiv.className = "status-warning";

  // If in fallback mode, disable it first
  if (fallbackMode) {
    disableFallbackMode();
  }

  // Stop any processing timers
  if (processingFailsafeTimer) {
    clearTimeout(processingFailsafeTimer);
    processingFailsafeTimer = null;
  }

  if (processingTimeoutWarning) {
    clearTimeout(processingTimeoutWarning);
    processingTimeoutWarning = null;
  }

  // Reset frame tracking variables
  frameCount = 0;
  analysisCount = 0;
  pendingFrames = 0;
  lastProcessedFrameTime = Date.now(); // Reset to prevent immediate fallback

  // Restart camera with the current facing mode
  stopFrameCapture();

  // If socket is disconnected, try to reconnect
  if (!socket.connected) {
    socket.connect();
  }

  // Initialize the camera after a short delay to ensure clean start
  setTimeout(() => {
    initCamera(currentFacingMode);
  }, 500);
});
// Recording functionality
function toggleRecording() {
  if (!isRecording) {
    startRecording();
  } else {
    stopRecording();
  }
}
function startRecording() {
  // Validate prerequisites
  if (!socket || !socket.connected) {
    analysisDiv.textContent = "Cannot record: Not connected to server";
    return;
  }

  if (!isStreaming) {
    analysisDiv.textContent = "Cannot record: Camera not active";
    return;
  }

  // Disable button to prevent double-clicks
  toggleRecordingBtn.disabled = true;
  analysisDiv.textContent = "Starting recording...";

  // Start server-side recording
  fetch("/api/recording/start", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: socket.id,
      user_agent: navigator.userAgent,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        isRecording = true;
        recordingStartTime = Date.now();
        toggleRecordingBtn.textContent = "⏹️ Stop";
        toggleRecordingBtn.style.background = "rgba(255, 0, 0, 0.8)";
        statusDiv.textContent = statusDiv.textContent + " - Recording";
        analysisDiv.textContent = `Recording started: ${data.filename}`;
      } else {
        console.error("Failed to start recording:", data.error);
        analysisDiv.textContent = `Recording failed: ${data.error}`;
      }
    })
    .catch((error) => {
      console.error("Error starting recording:", error);
      analysisDiv.textContent = `Recording start failed: ${error.message}`;
    })
    .finally(() => {
      toggleRecordingBtn.disabled = false;
    });
}
function stopRecording() {
  // Validate recording is active
  if (!isRecording) {
    analysisDiv.textContent = "No recording to stop";
    return;
  }

  // Disable button to prevent double-clicks
  toggleRecordingBtn.disabled = true;
  analysisDiv.textContent = "Stopping recording...";

  // Stop server-side recording
  fetch("/api/recording/stop", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: socket.id,
    }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return response.json();
    })
    .then((data) => {
      if (data.success) {
        isRecording = false;
        recordingStartTime = null;
        toggleRecordingBtn.textContent = "🔴 Record";
        toggleRecordingBtn.style.background = "rgba(0, 0, 0, 0.7)";

        const recording = data.recording_info;
        const duration = Math.round(recording.duration_seconds || 0);
        const frameCount = recording.frame_count || 0;
        const fileSize = recording.file_size_mb || 0;

        analysisDiv.textContent = `Recording saved: ${recording.filename} (${duration}s, ${frameCount} frames, ${fileSize}MB)`;

        // Update status text to remove "Recording"
        statusDiv.textContent = statusDiv.textContent.replace(
          " - Recording",
          ""
        );

        // Show download link or success message
        setTimeout(() => {
          analysisDiv.textContent =
            "Recording completed! Check Recordings page to download.";
        }, 2000);

        setTimeout(() => {
          analysisDiv.textContent = "Waiting for analysis...";
        }, 5000);
      } else {
        console.error("Failed to stop recording:", data.error);
        analysisDiv.textContent = `Recording stop failed: ${data.error}`;
        // Reset recording state on failure
        isRecording = false;
        recordingStartTime = null;
        toggleRecordingBtn.textContent = "🔴 Record";
        toggleRecordingBtn.style.background = "rgba(0, 0, 0, 0.7)";
        statusDiv.textContent = statusDiv.textContent.replace(
          " - Recording",
          ""
        );
      }
    })
    .catch((error) => {
      console.error("Error stopping recording:", error);
      analysisDiv.textContent = `Recording stop failed: ${error.message}`;
      // Reset recording state on error
      isRecording = false;
      recordingStartTime = null;
      toggleRecordingBtn.textContent = "🔴 Record";
      toggleRecordingBtn.style.background = "rgba(0, 0, 0, 0.7)";
      statusDiv.textContent = statusDiv.textContent.replace(" - Recording", "");
    })
    .finally(() => {
      toggleRecordingBtn.disabled = false;
    });
}
// Hide camera switch button initially
switchCameraBtn.style.display = "none";

// Add a failsafe fallback to ensure video feed works
let processingFailsafeTimer = null;
let fallbackMode = false;

function enableFallbackMode() {
  if (fallbackMode) return; // Already in fallback mode

  fallbackMode = true;
  console.warn("SafeVision: Enabling fallback mode due to processing issues");
  statusDiv.textContent = "Server processing issues - Using local display";
  statusDiv.style.color = "#ff9800";
  statusDiv.className = "status-warning";

  // Show video element directly (remove privacy mode temporarily)
  video.style.display = "block";
  canvas.style.display = "none"; // <-- Hide canvas

  // Create a local processing loop
  function localProcessingLoop() {
    if (!fallbackMode) return;

    // Draw video frame directly to canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Add fallback mode indicator
    ctx.fillStyle = "rgba(255, 152, 0, 0.7)";
    ctx.fillRect(10, 10, 180, 30);
    ctx.fillStyle = "#fff";
    ctx.font = "12px Arial";
    ctx.fillText("FALLBACK MODE: NO AI ANALYSIS", 20, 30);

    requestAnimationFrame(localProcessingLoop);
  }

  localProcessingLoop();
}

function disableFallbackMode() {
  if (!fallbackMode) return;

  fallbackMode = false;
  console.log(
    "SafeVision: Disabling fallback mode, returning to server processing"
  );

  // Hide video element to restore privacy
  video.style.display = "none";
  canvas.style.display = "block"; // <-- Show canvas again
}

// Set up processing failsafe - if no processed frames after 10 seconds, enable fallback
function setupProcessingFailsafe() {
  clearTimeout(processingFailsafeTimer);
  processingFailsafeTimer = setTimeout(() => {
    if (Date.now() - lastProcessedFrameTime > 10000) {
      enableFallbackMode();
    }
  }, 10000);
}
// The processed_frame event handler is already defined earlier in the file
// No need for a second handler

// Re-enable processing failsafe on disconnect
socket.on("disconnect", () => {
  // ... existing code ...

  // Re-enable processing failsafe
  setupProcessingFailsafe();
});

// Initial setup - load settings and start camera
loadSettings();
initCamera(settings.cameraFacing);
