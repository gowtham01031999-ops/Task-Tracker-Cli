"""Clock abstraction for timestamp generation."""

from datetime import datetime, timezone


class SystemClock:
    """Returns UTC timestamps in the persisted wire format."""

    def now_iso(self) -> str:
        """Return the current UTC time in ISO 8601 format."""

        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
