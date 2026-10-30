"""Versioned gateway contract. No token values/digests, identities or current outcomes."""
from microservice_session_features import FEATURE_COLUMNS

RICH_COLUMNS = FEATURE_COLUMNS + (
    'context_prior_requests_5s', 'context_prior_401_5s', 'context_prior_success_5s',
    'route_prior_requests_5s', 'route_prior_401_5s', 'route_prior_success_5s',
    'peer_consecutive_401', 'context_consecutive_401', 'context_is_new',
    'context_last_was_401', 'route_last_was_401', 'peer_last_was_401',
    'unique_bearer_contexts_5s', 'prior_success_5s', 'seconds_since_context_start',
)
