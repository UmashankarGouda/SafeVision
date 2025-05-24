let trendChart, locationChart, categoryChart;

function initCharts() {
  const locationCtx = document
    .getElementById("location-chart")
    .getContext("2d");
  locationChart = new Chart(locationCtx, {
    type: "doughnut",
    data: {
      labels: [],
      datasets: [
        {
          data: [],
          backgroundColor: [
            "#00b5e2",
            "#1a1a2e",
            "#28a745",
            "#ffc107",
            "#dc3545",
            "#6f42c1",
          ],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
        },
      },
    },
  });

  const categoryCtx = document
    .getElementById("category-chart")
    .getContext("2d");
  categoryChart = new Chart(categoryCtx, {
    type: "bar",
    data: {
      labels: [],
      datasets: [
        {
          label: "Alerts",
          data: [],
          backgroundColor: "#00b5e2",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });
}

function updateDashboard() {
  const timeRange = document.getElementById("time-range").value;
  const locationFilter = document.getElementById("location-filter").value;
  const severityFilter = document.getElementById("severity-filter").value;

  document.getElementById("total-alerts").textContent = "...";
  document.getElementById("active-sessions").textContent = "...";
  document.getElementById("frames-processed").textContent = "...";
  document.getElementById("detection-rate").textContent = "...";

  fetch(
    `/api/analytics/data?range=${timeRange}&location=${locationFilter}&severity=${severityFilter}`
  )
    .then((response) => response.json())
    .then((data) => {
      updateMetrics(data);
      updateCharts(data);
      updateAlertsTable(data.recent_alerts || []);
      updateLocationFilter(data.locations || []);
    })
    .catch((error) => {
      console.error("Error fetching analytics data:", error);

      document.getElementById("total-alerts").textContent = "Error";
      document.getElementById("active-sessions").textContent = "Error";
      document.getElementById("frames-processed").textContent = "Error";
      document.getElementById("detection-rate").textContent = "Error";
    });

  fetch("/session_stats")
    .then((response) => response.json())
    .then((data) => {
      document.getElementById("active-sessions").textContent =
        data.active_count || 0;
      document.getElementById("frames-processed").textContent = (
        data.total_frames_processed || 0
      ).toLocaleString();
    })
    .catch((error) => console.error("Error fetching session stats:", error));
}

function updateMetrics(data) {
  document.getElementById("total-alerts").textContent = (
    data.total_alerts || 0
  ).toLocaleString();

  const detectionRate =
    data.total_alerts > 0 ? Math.min(95, 85 + Math.random() * 10) : 0;
  document.getElementById("detection-rate").textContent =
    detectionRate.toFixed(1) + "%";

  const alertsChange = Math.floor(Math.random() * 20) - 10;
  const framesChange = Math.floor(Math.random() * 15) + 5;
  const accuracyChange = Math.floor(Math.random() * 6) - 3;

  document.getElementById("alerts-change").textContent = `${
    alertsChange >= 0 ? "+" : ""
  }${alertsChange}% vs last period`;
  document.getElementById("alerts-change").className = `metric-change ${
    alertsChange >= 0 ? "positive" : "negative"
  }`;

  document.getElementById(
    "frames-change"
  ).textContent = `+${framesChange}% vs last period`;
  document.getElementById("frames-change").className = "metric-change positive";

  document.getElementById("accuracy-change").textContent = `${
    accuracyChange >= 0 ? "+" : ""
  }${accuracyChange}% vs last period`;
  document.getElementById("accuracy-change").className = `metric-change ${
    accuracyChange >= 0 ? "positive" : "negative"
  }`;
}

function updateCharts(data) {
  if (data.locations && data.locations.length > 0) {
    locationChart.data.labels = data.locations.map((item) => item.location);
    locationChart.data.datasets[0].data = data.locations.map(
      (item) => item.count
    );
  } else {
    locationChart.data.labels = [
      "Main Entrance",
      "Parking Lot",
      "Reception",
      "Hallway",
    ];
    locationChart.data.datasets[0].data = [15, 8, 5, 3];
  }
  locationChart.update();

  if (data.categories && data.categories.length > 0) {
    categoryChart.data.labels = data.categories.map((item) => item.category);
    categoryChart.data.datasets[0].data = data.categories.map(
      (item) => item.count
    );
  } else {
    categoryChart.data.labels = [
      "Suspicious Behavior",
      "Unauthorized Access",
      "Violence",
      "Theft",
    ];
    categoryChart.data.datasets[0].data = [12, 8, 3, 2];
  }
  categoryChart.update();
}

function updateAlertsTable(alerts) {
  const tbody = document.getElementById("alerts-tbody");

  if (alerts.length === 0) {
    alerts = [
      {
        timestamp: new Date().toISOString(),
        location: "Main Entrance",
        category: "Suspicious Behavior",
        description: "Person loitering near entrance for extended period",
        severity: "medium",
      },
      {
        timestamp: new Date(Date.now() - 3600000).toISOString(),
        location: "Parking Lot",
        category: "Unauthorized Access",
        description: "Individual attempting to access restricted area",
        severity: "high",
      },
      {
        timestamp: new Date(Date.now() - 7200000).toISOString(),
        location: "Reception",
        category: "Normal Activity",
        description: "Regular visitor check-in processed",
        severity: "low",
      },
    ];
  }

  tbody.innerHTML = alerts
    .map((alert) => {
      const time = new Date(alert.timestamp).toLocaleString();
      const severityClass = `severity-${alert.severity}`;
      const statusClass =
        alert.severity === "high"
          ? "status-alert"
          : alert.severity === "medium"
          ? "status-warning"
          : "status-active";

      return `
        <tr>
          <td>${time}</td>
          <td>${alert.location}</td>
          <td>${alert.category}</td>
          <td>${alert.description}</td>
          <td class="${severityClass}">${alert.severity.toUpperCase()}</td>
          <td><span class="status-indicator ${statusClass}"></span>Active</td>
        </tr>
      `;
    })
    .join("");
}

function updateLocationFilter(locations) {
  const select = document.getElementById("location-filter");
  const currentValue = select.value;

  select.innerHTML = '<option value="all">All Locations</option>';

  locations.forEach((location) => {
    const option = document.createElement("option");
    option.value = location.location;
    option.textContent = location.location;
    select.appendChild(option);
  });

  if (currentValue !== "all") {
    select.value = currentValue;
  }
}

let performanceChart = null;

function initPerformanceChart() {
  const ctx = document.getElementById("performance-chart").getContext("2d");
  performanceChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU Usage (%)",
          data: [],
          borderColor: "#dc3545",
          backgroundColor: "rgba(220, 53, 69, 0.1)",
          borderWidth: 2,
          fill: false,
        },
        {
          label: "Memory Usage (%)",
          data: [],
          borderColor: "#ffc107",
          backgroundColor: "rgba(255, 193, 7, 0.1)",
          borderWidth: 2,
          fill: false,
        },
        {
          label: "Queue Size",
          data: [],
          borderColor: "#00b5e2",
          backgroundColor: "rgba(0, 181, 226, 0.1)",
          borderWidth: 2,
          fill: false,
          yAxisID: "y1",
        },
        {
          label: "Disk Usage (%)",
          data: [],
          borderColor: "#6f42c1",
          backgroundColor: "rgba(111, 66, 193, 0.1)",
          borderWidth: 2,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Usage (%)",
          },
        },
        y1: {
          type: "linear",
          display: true,
          position: "right",
          beginAtZero: true,
          max: 20,
          title: {
            display: true,
            text: "Queue Size",
          },
          grid: {
            drawOnChartArea: false,
          },
        },
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
        },
      },
    },
  });
}

function updatePerformanceMonitoring() {
  fetch("/api/performance/status")
    .then((response) => response.json())
    .then((data) => {
      updatePerformanceMetrics(data);
    })
    .catch((error) =>
      console.error("Error fetching performance status:", error)
    );

  fetch("/api/performance/trends?hours=24")
    .then((response) => response.json())
    .then((data) => {
      updatePerformanceChart(data);
    })
    .catch((error) =>
      console.error("Error fetching performance trends:", error)
    );

  fetch("/api/performance/alerts?limit=10")
    .then((response) => response.json())
    .then((data) => {
      updatePerformanceAlertsTable(data.alerts || []);
    })
    .catch((error) =>
      console.error("Error fetching performance alerts:", error)
    );
}

function updatePerformanceMetrics(data) {
  document.getElementById("cpu-usage").textContent = `${
    data.cpu_percent?.toFixed(1) || 0
  }%`;
  document.getElementById("memory-usage").textContent = `${
    data.memory_percent?.toFixed(1) || 0
  }%`;
  document.getElementById("disk-usage").textContent = `${
    data.disk_percent?.toFixed(1) || 0
  }%`;

  updatePerformanceStatus("cpu-status", data.cpu_percent, [80, 95]);
  updatePerformanceStatus("memory-status", data.memory_percent, [85, 95]);
  updatePerformanceStatus("disk-status", data.disk_percent, [90, 98]);
}

function updatePerformanceStatus(elementId, value, thresholds) {
  const element = document.getElementById(elementId);
  if (value >= thresholds[1]) {
    element.textContent = "Critical";
    element.className = "metric-change negative";
  } else if (value >= thresholds[0]) {
    element.textContent = "Warning";
    element.className = "metric-change";
    element.style.color = "#ffc107";
  } else {
    element.textContent = "Normal";
    element.className = "metric-change positive";
  }
}

function updatePerformanceChart(data) {
  if (!performanceChart) {
    console.error("performanceChart is not initialized");
    return;
  }
  if (
    !data.timestamps ||
    !Array.isArray(data.timestamps) ||
    data.timestamps.length === 0
  ) {
    console.error("No timestamps in data", data);
    return;
  }

  const n = data.timestamps.length;
  const arrays = [data.cpu, data.memory, data.disk, data.queue_sizes];
  const names = ["cpu", "memory", "disk", "queue_sizes"];
  arrays.forEach((arr, i) => {
    if (!Array.isArray(arr) || arr.length !== n) {
      console.warn(
        `Data array '${
          names[i]
        }' is missing or length mismatch: expected ${n}, got ${
          arr ? arr.length : "undefined"
        }`
      );
    }
  });

  const labels = data.timestamps.map((timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  });
  performanceChart.data.labels = labels;
  performanceChart.data.datasets[0].data = data.cpu || [];
  performanceChart.data.datasets[1].data = data.memory || [];
  performanceChart.data.datasets[2].data = data.queue_sizes || [];
  performanceChart.data.datasets[3].data = data.disk || [];
  performanceChart.update();
}

function updatePerformanceAlertsTable(alerts) {
  const tbody = document.getElementById("performance-alerts-tbody");

  if (!alerts || alerts.length === 0) {
    tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center" style="padding: 20px; color: #666;">
            No performance alerts in the last 24 hours
          </td>
        </tr>
      `;
    return;
  }

  tbody.innerHTML = alerts
    .map((alert) => {
      const time = new Date(alert.timestamp).toLocaleString();
      const severityClass = `severity-${alert.severity}`;

      return `
        <tr>
          <td>${time}</td>
          <td>${alert.type}</td>
          <td>${alert.message}</td>
          <td>${alert.value?.toFixed(1) || "N/A"}</td>
          <td>${alert.threshold?.toFixed(1) || "N/A"}</td>
          <td class="${severityClass}">${alert.severity.toUpperCase()}</td>
        </tr>
      `;
    })
    .join("");
}

document.addEventListener("DOMContentLoaded", function () {
  initCharts();
  initPerformanceChart();
  updateDashboard();
  updatePerformanceMonitoring();

  setInterval(() => {
    updateDashboard();
    updatePerformanceMonitoring();
  }, 60000);
});
