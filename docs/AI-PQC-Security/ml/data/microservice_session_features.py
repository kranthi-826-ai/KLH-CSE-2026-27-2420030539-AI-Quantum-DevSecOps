"""Causal HTTP-history features, deliberately separate from network-flow schemas."""
from collections import deque
import math

FEATURE_COLUMNS = (
    'is_login', 'is_identity_read', 'has_bearer', 'has_history',
    'prior_requests_1s', 'prior_requests_5s', 'prior_401_5s',
    'prior_failed_login_5s', 'seconds_since_previous_start',
)


class RequestHistory:
    """One trusted client/account history; call before_request BEFORE sending HTTP."""

    def __init__(self):
        self.events = deque()
        self.last_start = None

    def before_request(self, now, route, has_bearer):
        if not math.isfinite(now) or (self.last_start is not None and now < self.last_start):
            raise ValueError('Request clock must be finite and monotonic')
        while self.events and self.events[0]['completed'] < now - 5:
            self.events.popleft()
        # Only completed responses strictly preceding this decision are usable.
        previous = [e for e in self.events if e['completed'] < now]
        return {
            'is_login': int(route == '/api/v1/auth/login'),
            'is_identity_read': int(route == '/api/v1/auth/me'),
            'has_bearer': int(bool(has_bearer)),
            'has_history': int(self.last_start is not None),
            'prior_requests_1s': sum(e['start'] >= now - 1 for e in previous),
            'prior_requests_5s': len(previous),
            'prior_401_5s': sum(e['status'] == 401 for e in previous),
            'prior_failed_login_5s': sum(e['status'] == 401 and e['route'] == '/api/v1/auth/login' for e in previous),
            'seconds_since_previous_start': min(5., now - self.last_start) if self.last_start is not None else 5.,
        }

    def after_response(self, start, completed, route, status):
        if not all(math.isfinite(v) for v in (start, completed)) or completed < start:
            raise ValueError('Invalid response clock')
        if self.last_start is not None and start < self.last_start:
            raise ValueError('Out-of-order history')
        self.events.append({'start': start, 'completed': completed, 'route': route, 'status': status})
        self.last_start = start
