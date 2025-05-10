class ConfidenceMeter {
  constructor(elementId, updateInterval = 3000) {
    this.elementId = elementId;
    this.updateInterval = updateInterval;
    this.init();
  }

  init() {
    this.fetchConfidenceLevel();
    setInterval(() => this.fetchConfidenceLevel(), this.updateInterval);
  }

  setConfidenceLevel(value) {
    const circle = document.getElementById("progress");
    const text = document.getElementById("percentage");
    const maxOffset = 251.2;
    const offset = maxOffset - (value / 100) * maxOffset;

    if (circle && text) {
      circle.style.strokeDashoffset = offset;
      text.textContent = value + "%";
    }
  }

  fetchConfidenceLevel() {
    fetch("/get_confidence")
      .then((response) => response.json())
      .then((data) => {
        this.setConfidenceLevel(data.confidence_level);
      })
      .catch((error) =>
        console.error("Error fetching confidence level:", error)
      );
  }
}

// Initialize when DOM is fully loaded
document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector(".metrics")) {
    new ConfidenceMeter("progress");
  }
});
