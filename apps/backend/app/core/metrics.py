from collections import defaultdict
from threading import Lock

METRIC_DEFINITIONS: dict[str, str] = {
    "app_requests_total": "Total HTTP requests handled by the API process.",
    "reservation_attempt_total": "Reservation create attempts.",
    "reservation_success_total": "Successful reservation holds created.",
    "reservation_conflict_total": "Reservation attempts rejected due to seat conflicts.",
    "checkout_session_attempt_total": "Checkout session creation attempts.",
    "checkout_session_success_total": "Successful checkout sessions created.",
    "checkout_finalize_success_total": "Orders finalized as PAID.",
    "ticket_scan_attempt_total": "Ticket scan attempts.",
    "ticket_scan_valid_total": "Ticket scans validated and marked used.",
    "ticket_scan_invalid_total": "Ticket scans rejected as invalid.",
    "ticket_scan_already_used_total": "Ticket scans rejected as already used.",
}


class _MetricsStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: defaultdict[str, int] = defaultdict(int)

    def increment(self, metric_name: str, value: int = 1) -> None:
        with self._lock:
            self._counters[metric_name] += value

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return dict(self._counters)


_metrics_store = _MetricsStore()


def increment_metric(metric_name: str, value: int = 1) -> None:
    _metrics_store.increment(metric_name, value)


def render_prometheus_metrics() -> str:
    snapshot = _metrics_store.snapshot()
    lines: list[str] = []
    metric_names = sorted(set(METRIC_DEFINITIONS).union(snapshot))
    for metric_name in metric_names:
        help_text = METRIC_DEFINITIONS.get(metric_name, "Application metric.")
        metric_value = snapshot.get(metric_name, 0)
        lines.append(f"# HELP {metric_name} {help_text}")
        lines.append(f"# TYPE {metric_name} counter")
        lines.append(f"{metric_name} {metric_value}")
    return "\n".join(lines) + "\n"
