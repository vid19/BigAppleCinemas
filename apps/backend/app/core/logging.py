import json
import logging
from datetime import UTC, datetime

STANDARD_LOG_RECORD_FIELDS = set(
    logging.makeLogRecord({}).__dict__.keys()
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_RECORD_FIELDS or key.startswith("_"):
                continue
            payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(*, debug: bool) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]
