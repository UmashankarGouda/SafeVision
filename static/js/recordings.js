let recordings = [];

// Load recordings on page load
document.addEventListener("DOMContentLoaded", function () {
  loadRecordings();
  loadStorageInfo();
});

function loadRecordings() {
  document.getElementById("recordings-loading").style.display = "block";
  document.getElementById("recordings-content").style.display = "none";

  fetch("/api/recording/list")
    .then((response) => response.json())
    .then((data) => {
      recordings = data.recordings || [];
      displayRecordings();
      document.getElementById("recordings-loading").style.display = "none";
      document.getElementById("recordings-content").style.display = "block";
    })
    .catch((error) => {
      console.error("Error loading recordings:", error);
      document.getElementById("recordings-loading").innerHTML = `
          <i class="fas fa-exclamation-triangle"></i>
          <p>Error loading recordings</p>
        `;
    });
}

function loadStorageInfo() {
  fetch("/api/recording/storage_info")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("total-recordings").textContent =
        data.recordings_count || 0;
      document.getElementById("storage-used").textContent = `${
        data.total_size_mb || 0
      } MB`;
      document.getElementById("free-space").textContent = `${
        data.disk_free_gb || 0
      } GB`;

      const usagePercent =
        ((data.disk_used_gb || 0) / (data.disk_total_gb || 1)) * 100;
      document.getElementById(
        "disk-usage"
      ).textContent = `${usagePercent.toFixed(1)}%`;
      document.getElementById("storage-bar").style.width = `${Math.min(
        100,
        usagePercent
      )}%`;
    })
    .catch((error) => console.error("Error loading storage info:", error));
}

function displayRecordings() {
  const grid = document.getElementById("recordings-grid");
  const noRecordings = document.getElementById("no-recordings");

  if (recordings.length === 0) {
    grid.innerHTML = "";
    noRecordings.style.display = "block";
    return;
  }

  noRecordings.style.display = "none";

  grid.innerHTML = recordings
    .map((recording) => {
      const startTime = recording.start_time
        ? new Date(recording.start_time)
        : new Date(recording.created_time);
      const endTime = recording.end_time ? new Date(recording.end_time) : null;
      const duration = recording.duration_seconds || 0;
      const frameCount = recording.frame_count || 0;
      const fileSize = recording.file_size_mb || 0;

      const statusClass = recording.status || "archived";
      const statusText =
        recording.status === "recording"
          ? "Recording"
          : recording.status === "completed"
          ? "Completed"
          : "Archived";

      return `
        <div class="recording-card">
          <div class="recording-thumbnail">
            <div class="recording-status ${statusClass}">${statusText}</div>
            ${
              recording.thumbnail
                ? `<img src="/api/recording/thumbnail/${recording.filename}" alt="Thumbnail" onerror="this.style.display='none'">`
                : '<i class="fas fa-video placeholder"></i>'
            }
          </div>
          <div class="recording-info">
            <div class="recording-title">${recording.filename}</div>
            <div class="recording-details">
              <div><i class="fas fa-clock"></i> ${startTime.toLocaleString()}</div>
              <div><i class="fas fa-stopwatch"></i> Duration: ${formatDuration(
                duration
              )}</div>
              <div><i class="fas fa-film"></i> Frames: ${frameCount.toLocaleString()}</div>
              <div><i class="fas fa-hdd"></i> Size: ${fileSize.toFixed(
                1
              )} MB</div>
            </div>
            <div class="recording-actions">
              <a href="/api/recording/download/${recording.filename}" 
                 class="btn btn-primary" download>
                <i class="fas fa-download"></i> Download
              </a>
              <button class="btn btn-danger" onclick="deleteRecording('${
                recording.filename
              }')">
                <i class="fas fa-trash"></i> Delete
              </button>
            </div>
          </div>
        </div>
      `;
    })
    .join("");
}

function formatDuration(seconds) {
  if (seconds < 60) {
    return `${seconds.toFixed(0)}s`;
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
}

function deleteRecording(filename) {
  if (
    !confirm(
      `Are you sure you want to delete "${filename}"? This action cannot be undone.`
    )
  ) {
    return;
  }

  fetch(`/api/recording/delete/${filename}`, {
    method: "DELETE",
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert("Recording deleted successfully");
        loadRecordings();
        loadStorageInfo();
      } else {
        alert(`Error deleting recording: ${data.error}`);
      }
    })
    .catch((error) => {
      console.error("Error deleting recording:", error);
      alert("Error deleting recording");
    });
}

function cleanupRecordings() {
  const maxAge = prompt("Delete recordings older than how many days?", "30");
  if (!maxAge || isNaN(maxAge) || maxAge < 1) {
    return;
  }

  if (
    !confirm(
      `This will delete all recordings older than ${maxAge} days. Continue?`
    )
  ) {
    return;
  }

  fetch("/api/recording/cleanup", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      max_age_days: parseInt(maxAge),
    }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        alert(
          `Cleanup completed: ${data.deleted_count} recordings deleted, ${data.size_freed_mb} MB freed`
        );
        loadRecordings();
        loadStorageInfo();
      } else {
        alert(`Cleanup failed: ${data.error}`);
      }
    })
    .catch((error) => {
      console.error("Error during cleanup:", error);
      alert("Cleanup failed");
    });
}

function refreshRecordings() {
  loadRecordings();
  loadStorageInfo();
}
