"""
Alerting system for monitoring critical API metrics.
Tracks error rates and response times to detect issues.
"""
from datetime import datetime, timedelta
from collections import deque
from typing import Deque, Tuple
import structlog

logger = structlog.get_logger(__name__)


class AlertManager:
    """Manages alerts for critical system metrics."""
    
    def __init__(self):
        # Track last 100 requests for error rate calculation
        self.recent_requests: Deque[Tuple[datetime, bool]] = deque(maxlen=100)
        # Track last 50 response times for slow request detection
        self.recent_response_times: Deque[Tuple[datetime, float]] = deque(maxlen=50)
        
        # Alert thresholds
        self.error_rate_threshold = 0.05  # 5%
        self.slow_response_threshold = 2.0  # 2 seconds
        
        # Prevent alert spam
        self.last_error_rate_alert = None
        self.last_slow_response_alert = None
        self.alert_cooldown = timedelta(minutes=5)
    
    def record_request(self, is_error: bool, duration_ms: float):
        """
        Record a request for monitoring.
        
        Args:
            is_error: Whether the request resulted in an error (5xx status)
            duration_ms: Request duration in milliseconds
        """
        now = datetime.utcnow()
        self.recent_requests.append((now, is_error))
        self.recent_response_times.append((now, duration_ms / 1000))  # Convert to seconds
        
        self._check_error_rate()
        self._check_slow_responses()
    
    def _check_error_rate(self):
        """Check if error rate exceeds threshold and trigger alert."""
        if len(self.recent_requests) < 20:  # Need minimum sample size
            return
        
        error_count = sum(1 for _, is_error in self.recent_requests if is_error)
        error_rate = error_count / len(self.recent_requests)
        
        if error_rate > self.error_rate_threshold:
            if self._should_send_alert(self.last_error_rate_alert):
                logger.error(
                    "ALERT: High error rate detected",
                    error_rate=f"{error_rate:.1%}",
                    threshold=f"{self.error_rate_threshold:.1%}",
                    sample_size=len(self.recent_requests)
                )
                self.last_error_rate_alert = datetime.utcnow()
    
    def _check_slow_responses(self):
        """Check if response times are consistently slow and trigger alert."""
        if len(self.recent_response_times) < 10:  # Need minimum sample size
            return
        
        # Check if more than 30% of recent requests are slow
        slow_count = sum(1 for _, duration in self.recent_response_times 
                        if duration > self.slow_response_threshold)
        slow_rate = slow_count / len(self.recent_response_times)
        
        if slow_rate > 0.3:  # 30% of requests are slow
            if self._should_send_alert(self.last_slow_response_alert):
                avg_duration = sum(d for _, d in self.recent_response_times) / len(self.recent_response_times)
                logger.warning(
                    "ALERT: API response time degraded",
                    slow_request_rate=f"{slow_rate:.1%}",
                    avg_response_time=f"{avg_duration:.2f}s",
                    threshold=f"{self.slow_response_threshold}s"
                )
                self.last_slow_response_alert = datetime.utcnow()
    
    def _should_send_alert(self, last_alert_time) -> bool:
        """Check if enough time has passed since last alert to avoid spam."""
        if last_alert_time is None:
            return True
        return datetime.utcnow() - last_alert_time > self.alert_cooldown


# Global alert manager instance
_alert_manager: AlertManager = None


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance."""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
