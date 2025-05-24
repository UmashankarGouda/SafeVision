function setConfidenceLevel(value) {
  const circle = document.getElementById("progress");
  const text = document.getElementById("percentage");
  const maxOffset = 251.2;
  const offset = maxOffset - (value / 100) * maxOffset;
  circle.style.strokeDashoffset = offset;
  text.textContent = value + "%";
}

function fetchConfidenceLevel() {
  fetch("/get_confidence")
    .then((response) => response.json())
    .then((data) => {
      setConfidenceLevel(data.confidence);
    })
    .catch((error) => console.error("Error fetching confidence level:", error));
}

// Fetch confidence level every 5 seconds
setInterval(fetchConfidenceLevel, 3000);

// Initial fetch when the page loads
fetchConfidenceLevel();
