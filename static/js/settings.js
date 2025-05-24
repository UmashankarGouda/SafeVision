// Initialize settings from localStorage or defaults
const defaultSettings = {
  frameRate: 10,
  videoQuality: 0.8,
  cameraFacing: "user",
  resolution: "640x480",
  webpQuality: 80,
  queueSize: 10,
  enableFrameDropping: true,
  mobileOptimizations: true,
  enableRecording: true,
  maxRecordingDuration: 5,
  autoDownload: false,
  detectionSensitivity: 0.5,
  saveAlertImages: true,
  alertCooldown: 10,
  enableMonitoring: true,
  cpuWarningThreshold: 80,
  cpuCriticalThreshold: 95,
  memoryWarningThreshold: 85,
  memoryCriticalThreshold: 95,
  monitoringInterval: 10,
};

let currentSettings = { ...defaultSettings };

// Load settings from localStorage
function loadSettings() {
  const saved = localStorage.getItem("safeVisionSettings");
  if (saved) {
    currentSettings = { ...defaultSettings, ...JSON.parse(saved) };
  }
  updateUI();
}

// Update UI elements with current settings
function updateUI() {
  document.getElementById("frame-rate").value = currentSettings.frameRate;
  document.getElementById("frame-rate-value").textContent =
    currentSettings.frameRate;

  document.getElementById("video-quality").value = currentSettings.videoQuality;
  document.getElementById("video-quality-value").textContent =
    currentSettings.videoQuality;

  document.getElementById("camera-facing").value = currentSettings.cameraFacing;
  document.getElementById("resolution").value = currentSettings.resolution;

  document.getElementById("webp-quality").value = currentSettings.webpQuality;
  document.getElementById("webp-quality-value").textContent =
    currentSettings.webpQuality;

  document.getElementById("queue-size").value = currentSettings.queueSize;
  document.getElementById("queue-size-value").textContent =
    currentSettings.queueSize;

  document.getElementById("enable-frame-dropping").checked =
    currentSettings.enableFrameDropping;
  document.getElementById("mobile-optimizations").checked =
    currentSettings.mobileOptimizations;

  document.getElementById("enable-recording").checked =
    currentSettings.enableRecording;
  document.getElementById("max-recording-duration").value =
    currentSettings.maxRecordingDuration;
  document.getElementById("max-recording-duration-value").textContent =
    currentSettings.maxRecordingDuration;
  document.getElementById("auto-download").checked =
    currentSettings.autoDownload;
  document.getElementById("detection-sensitivity").value =
    currentSettings.detectionSensitivity;
  document.getElementById("detection-sensitivity-value").textContent =
    currentSettings.detectionSensitivity;
  document.getElementById("save-alert-images").checked =
    currentSettings.saveAlertImages;
  document.getElementById("alert-cooldown").value =
    currentSettings.alertCooldown;
  document.getElementById("alert-cooldown-value").textContent =
    currentSettings.alertCooldown;

  // Performance monitoring settings
  document.getElementById("enable-monitoring").checked =
    currentSettings.enableMonitoring;
  document.getElementById("cpu-warning-threshold").value =
    currentSettings.cpuWarningThreshold;
  document.getElementById("cpu-warning-threshold-value").textContent =
    currentSettings.cpuWarningThreshold;
  document.getElementById("cpu-critical-threshold").value =
    currentSettings.cpuCriticalThreshold;
  document.getElementById("cpu-critical-threshold-value").textContent =
    currentSettings.cpuCriticalThreshold;
  document.getElementById("memory-warning-threshold").value =
    currentSettings.memoryWarningThreshold;
  document.getElementById("memory-warning-threshold-value").textContent =
    currentSettings.memoryWarningThreshold;
  document.getElementById("memory-critical-threshold").value =
    currentSettings.memoryCriticalThreshold;
  document.getElementById("memory-critical-threshold-value").textContent =
    currentSettings.memoryCriticalThreshold;
  document.getElementById("monitoring-interval").value =
    currentSettings.monitoringInterval;
  document.getElementById("monitoring-interval-value").textContent =
    currentSettings.monitoringInterval;
}

// Update range value displays
function setupRangeListeners() {
  const ranges = document.querySelectorAll('input[type="range"]');
  ranges.forEach((range) => {
    range.addEventListener("input", function () {
      const valueSpan = document.getElementById(this.id + "-value");
      if (valueSpan) {
        valueSpan.textContent = this.value;
      }
    });
  });
}

// Save settings to localStorage and apply them
function saveSettings() {
  // Collect current UI values
  currentSettings = {
    frameRate: parseInt(document.getElementById("frame-rate").value),
    videoQuality: parseFloat(document.getElementById("video-quality").value),
    cameraFacing: document.getElementById("camera-facing").value,
    resolution: document.getElementById("resolution").value,
    webpQuality: parseInt(document.getElementById("webp-quality").value),
    queueSize: parseInt(document.getElementById("queue-size").value),
    enableFrameDropping: document.getElementById("enable-frame-dropping")
      .checked,
    mobileOptimizations: document.getElementById("mobile-optimizations")
      .checked,
    enableRecording: document.getElementById("enable-recording").checked,
    maxRecordingDuration: parseInt(
      document.getElementById("max-recording-duration").value
    ),
    autoDownload: document.getElementById("auto-download").checked,
    detectionSensitivity: parseFloat(
      document.getElementById("detection-sensitivity").value
    ),
    saveAlertImages: document.getElementById("save-alert-images").checked,
    alertCooldown: parseInt(document.getElementById("alert-cooldown").value),
    enableMonitoring: document.getElementById("enable-monitoring").checked,
    cpuWarningThreshold: parseInt(
      document.getElementById("cpu-warning-threshold").value
    ),
    cpuCriticalThreshold: parseInt(
      document.getElementById("cpu-critical-threshold").value
    ),
    memoryWarningThreshold: parseInt(
      document.getElementById("memory-warning-threshold").value
    ),
    memoryCriticalThreshold: parseInt(
      document.getElementById("memory-critical-threshold").value
    ),
    monitoringInterval: parseInt(
      document.getElementById("monitoring-interval").value
    ),
  };

  // Save to localStorage
  localStorage.setItem("safeVisionSettings", JSON.stringify(currentSettings));

  // Update performance monitoring thresholds via API
  if (currentSettings.enableMonitoring) {
    fetch("/api/performance/thresholds", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        cpu_percent: {
          warning: currentSettings.cpuWarningThreshold,
          critical: currentSettings.cpuCriticalThreshold,
        },
        memory_percent: {
          warning: currentSettings.memoryWarningThreshold,
          critical: currentSettings.memoryCriticalThreshold,
        },
      }),
    }).catch((err) =>
      console.warn("Failed to update performance thresholds:", err)
    );
  }

  // Apply settings to current session if on home page
  // Only apply settings if we're in a trusted context
  if (window.parent && window.parent !== window) {
    try {
      // Check if parent is same origin
      const parentLocation = window.parent.location.href;
      if (window.parent.applySettings) {
        window.parent.applySettings(currentSettings);
      }
    } catch (e) {
      // Cross-origin access will throw, which is expected
      console.warn("Cannot access parent window - different origin");
    }
  }

  alert("Settings saved successfully!");
}

// Reset settings to defaults
function resetSettings() {
  if (confirm("Are you sure you want to reset all settings to defaults?")) {
    currentSettings = { ...defaultSettings };
    updateUI();
    localStorage.removeItem("safeVisionSettings");
    alert("Settings reset to defaults.");
  }
}

// Export settings as JSON file
function exportSettings() {
  const dataStr = JSON.stringify(currentSettings, null, 2);
  const dataBlob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(dataBlob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "safevision-settings.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Update system status
function updateSystemStatus() {
  fetch("/session_stats")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("active-sessions").textContent =
        data.active_count || 0;
      document.getElementById("frames-processed").textContent =
        data.total_frames_processed || 0;
      document.getElementById("processing-status").textContent =
        data.processing_status ? "Active" : "Idle";
    })
    .catch((error) => console.error("Error fetching session stats:", error));

  fetch("/system_status")
    .then((response) => response.json())
    .then((data) => {
      if (data.system && data.system.cpu_percent !== undefined) {
        document.getElementById("cpu-usage").textContent =
          data.system.cpu_percent.toFixed(1) + "%";
      }
    })
    .catch((error) => console.error("Error fetching system status:", error));
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  loadSettings();
  setupRangeListeners();
  updateSystemStatus();

  // Update status every 5 seconds
  setInterval(updateSystemStatus, 5000);
});
