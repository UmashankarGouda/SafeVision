"""
Performance monitoring service for SafeVision.
Monitors system resources and generates alerts when thresholds are exceeded.
"""

import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Callable


class PerformanceAlert:
    """Represents a performance alert."""

    def __init__(
        self,
        alert_type: str,
        severity: str,
        message: str,
        value: float,
        threshold: float,
    ):
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.value = value
        self.threshold = threshold
        self.timestamp = datetime.now()
        self.id = f"{alert_type}_{int(time.time())}"


class PerformanceMonitor:
    """Monitors system performance and generates alerts."""

    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.alert_callbacks: List[Callable] = []
        self.recent_alerts: List[PerformanceAlert] = []
        self.max_recent_alerts = 100

        self.thresholds = {
            "cpu_percent": {"warning": 80.0, "critical": 95.0},
            "memory_percent": {"warning": 85.0, "critical": 95.0},
            "disk_percent": {"warning": 90.0, "critical": 98.0},
            "queue_size": {"warning": 8, "critical": 10},
            "frame_processing_lag": {"warning": 2.0, "critical": 5.0},
        }

        self.monitor_interval = 10

        self.performance_history = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "queue_sizes": [],
            "timestamps": [],
        }
        self.max_history_points = 288

    def add_alert_callback(self, callback: Callable):
        """Add a callback function to be called when alerts are generated."""
        self.alert_callbacks.append(callback)

    def start_monitoring(self):
        """Start performance monitoring in a background thread."""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitoring_thread = threading.Thread(
                target=self._monitor_loop, daemon=True
            )
            self.monitoring_thread.start()
            print("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=1)
        print("Performance monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                self._check_system_performance()
                time.sleep(self.monitor_interval)
            except Exception as e:
                print(f"Error in performance monitoring: {e}")
                time.sleep(self.monitor_interval)

    def _check_system_performance(self):
        """Check system performance metrics and generate alerts if needed."""
        current_time = datetime.now()

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        self.performance_history["cpu"].append(cpu_percent)
        self.performance_history["memory"].append(memory.percent)
        self.performance_history["disk"].append(disk.percent)
        self.performance_history["timestamps"].append(current_time)

        if len(self.performance_history["timestamps"]) > self.max_history_points:
            for key in self.performance_history:
                self.performance_history[key] = self.performance_history[key][
                    -self.max_history_points :
                ]

        self._check_threshold("cpu_percent", cpu_percent, "CPU usage")

        self._check_threshold("memory_percent", memory.percent, "Memory usage")

        self._check_threshold("disk_percent", disk.percent, "Disk usage")

    def check_queue_performance(
        self, incoming_queue_size: int, processed_queue_size: int
    ):
        """Check queue performance metrics."""
        max_queue_size = max(incoming_queue_size, processed_queue_size)
        self.performance_history["queue_sizes"].append(max_queue_size)

        if len(self.performance_history["queue_sizes"]) > self.max_history_points:
            self.performance_history["queue_sizes"] = self.performance_history[
                "queue_sizes"
            ][-self.max_history_points :]

        self._check_threshold("queue_size", max_queue_size, "Queue size")

    def _check_threshold(self, metric_type: str, value: float, description: str):
        """Check if a metric exceeds thresholds and generate alerts."""
        thresholds = self.thresholds.get(metric_type, {})

        if value >= thresholds.get("critical", float("inf")):
            alert = PerformanceAlert(
                alert_type=metric_type,
                severity="critical",
                message=f"{description} is critically high: {value:.1f}%",
                value=value,
                threshold=thresholds["critical"],
            )
            self._generate_alert(alert)
        elif value >= thresholds.get("warning", float("inf")):
            alert = PerformanceAlert(
                alert_type=metric_type,
                severity="warning",
                message=f"{description} is high: {value:.1f}%",
                value=value,
                threshold=thresholds["warning"],
            )
            self._generate_alert(alert)

    def _generate_alert(self, alert: PerformanceAlert):
        """Generate and process a performance alert."""

        recent_similar = [
            a
            for a in self.recent_alerts
            if a.alert_type == alert.alert_type
            and a.severity == alert.severity
            and (alert.timestamp - a.timestamp).total_seconds() < 300
        ]

        if recent_similar:
            return

        self.recent_alerts.append(alert)
        if len(self.recent_alerts) > self.max_recent_alerts:
            self.recent_alerts = self.recent_alerts[-self.max_recent_alerts :]

        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Error in alert callback: {e}")

        print(f"Performance Alert: {alert.message}")

    def get_current_status(self) -> Dict:
        """Get current performance status."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "is_monitoring": self.is_monitoring,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def get_recent_alerts(self, limit: int = 10) -> List[Dict]:
        """Get recent performance alerts."""
        recent = self.recent_alerts[-limit:] if limit else self.recent_alerts
        return [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "message": alert.message,
                "value": alert.value,
                "threshold": alert.threshold,
                "timestamp": alert.timestamp.isoformat(),
            }
            for alert in reversed(recent)
        ]

    def get_performance_trends(self, hours: int = 24) -> Dict:
        """Get performance trends for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        filtered_data = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "queue_sizes": [],
            "timestamps": [],
        }

        for i, timestamp in enumerate(self.performance_history["timestamps"]):
            if timestamp >= cutoff_time:
                filtered_data["cpu"].append(self.performance_history["cpu"][i])
                filtered_data["memory"].append(self.performance_history["memory"][i])
                filtered_data["disk"].append(self.performance_history["disk"][i])
                if i < len(self.performance_history["queue_sizes"]):
                    filtered_data["queue_sizes"].append(
                        self.performance_history["queue_sizes"][i]
                    )
                filtered_data["timestamps"].append(timestamp.isoformat())

        return filtered_data

    def update_thresholds(self, new_thresholds: Dict):
        """Update performance thresholds."""
        for metric, thresholds in new_thresholds.items():
            if metric in self.thresholds:
                self.thresholds[metric].update(thresholds)
        print(f"Updated performance thresholds: {self.thresholds}")


performance_monitor = PerformanceMonitor()
