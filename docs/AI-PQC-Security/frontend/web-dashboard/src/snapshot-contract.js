// Validate display-driving fields before accepting a source as retrieved evidence.
// This is a rendering/evidence boundary, not authentication or record attestation.
const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
const text = (value, max) => typeof value === 'string' && value.trim().length > 0 && value.length <= max;
const optionalText = (value, max) => value == null || typeof value === 'string' && value.length <= max;
const milliseconds = value => Number.isSafeInteger(value) && value >= 0;
const score = value => typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 1;
const profiles = {
  CLASSICAL:'X25519+AES-256-GCM+ECDSA-P256',
  HYBRID:'X-Wing+AES-256-GCM+ML-DSA-65',
  PQC:'ML-KEM-768+AES-256-GCM+ML-DSA-65'
};
const eventFields = new Set(['eventId','occurredAt','eventType','outcome','sourceService','username',
  'correlationId','requestMethod','requestPath','sourceIp','detail']);
const executionFields = new Set(['executionId','executedAt','decisionId','correlationId','username',
  'riskLevel','riskScore','selectedMode','algorithmProfile','selectionReason','policyVersion','modelVersion',
  'policyLatencyMillis','cryptoLatencyMillis','totalLatencyMillis','roundTripVerified','outcome','errorDetail']);

function validEvent(row) {
  return text(row.eventId,36) && text(row.eventType,160) && text(row.sourceService,100) &&
    ['SUCCESS','DENIED','FAILURE'].includes(row.outcome) &&
    ['username','correlationId','requestMethod','requestPath','sourceIp','detail','occurredAt']
      .every(field => optionalText(row[field],field === 'detail' ? 4096 : field === 'requestPath' ? 2048 : 100));
  // Missing/unparseable timestamp strings deliberately render as Time unavailable.
}

function validExecution(row) {
  if (!text(row.executionId,36) || !['STARTED','SUCCESS','FAILED'].includes(row.outcome) ||
      typeof row.roundTripVerified !== 'boolean' || !score(row.riskScore) ||
      !['policyLatencyMillis','cryptoLatencyMillis','totalLatencyMillis'].every(field => milliseconds(row[field])) ||
      !['decisionId','correlationId','username','algorithmProfile','selectionReason','policyVersion','modelVersion','errorDetail','executedAt']
        .every(field => optionalText(row[field],['selectionReason','errorDetail'].includes(field) ? 4096 : 160))) return false;
  if (row.roundTripVerified && row.outcome === 'STARTED') return false;
  if ((row.outcome === 'SUCCESS' || row.roundTripVerified) && (row.policyLatencyMillis > row.totalLatencyMillis ||
      row.cryptoLatencyMillis > row.totalLatencyMillis)) return false;
  if (row.decisionId == null) {
    return row.selectedMode == null && row.riskLevel == null && !row.roundTripVerified && row.outcome !== 'SUCCESS';
  }
  return text(row.decisionId,36) && ['LOW','MEDIUM','HIGH'].includes(row.riskLevel) &&
    typeof row.selectedMode === 'string' && Object.hasOwn(profiles,row.selectedMode) &&
    (row.algorithmProfile == null || row.algorithmProfile === profiles[row.selectedMode]);
}

export function validSnapshot(source, rows) {
  if (!['events','runs'].includes(source) || !Array.isArray(rows) || rows.length > 100) return false;
  const id = source === 'events' ? 'eventId' : 'executionId';
  const validator = source === 'events' ? validEvent : validExecution;
  const fields = source === 'events' ? eventFields : executionFields;
  return rows.every(row => object(row) && Object.keys(row).every(key => fields.has(key)) && validator(row)) &&
    new Set(rows.map(row => row[id])).size === rows.length;
}
