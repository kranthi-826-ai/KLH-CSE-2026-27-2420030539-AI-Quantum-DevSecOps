import React from 'react';

export function OperationalTelemetry({events, runs, loadedSources}) {
  const dated = events.map(event => ({...event, time:Date.parse(event.occurredAt)}))
    .filter(event => Number.isFinite(event.time)).sort((a,b) => a.time-b.time);
  const start = dated[0]?.time;
  const end = dated.at(-1)?.time;
  const span = Math.max((end || 0)-(start || 0), 60_000);
  const buckets = Array.from({length:16}, () => ({success:0, other:0}));
  dated.forEach(event => {
    const index = Math.min(15, Math.floor((event.time-start)/span*16));
    buckets[index][event.outcome === 'SUCCESS' ? 'success' : 'other']++;
  });
  const peak = Math.max(1,...buckets.map(bucket => bucket.success+bucket.other));
  const denied = events.filter(event => event.outcome === 'DENIED').length;
  const failed = events.filter(event => event.outcome === 'FAILURE').length;
  const success = events.filter(event => event.outcome === 'SUCCESS').length;
  const latest = runs.find(run => run.decisionId);
  const latestVerified = latest?.outcome === 'SUCCESS' && latest.roundTripVerified === true;
  const verificationNote = latestVerified ? 'Execution completed and round trip verified.'
    : latest?.roundTripVerified === true ? 'Cryptographic check passed, but the overall request failed. Not a successful protected request.'
    : 'Not verified as executed protection. Inspect the recorded outcome.';
  const formatTime = value => new Date(value).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});
  return <section className="telemetry-grid" aria-label="Recorded security telemetry">
    <article className="panel activity-panel">
      <div className="telemetry-heading"><div><span className="eyebrow">OBSERVABILITY</span><h2>Security activity</h2></div><span className="data-tag">Recorded events</span></div>
      <div className="activity-total"><strong>{loadedSources.events ? events.length.toLocaleString() : '—'}</strong><span>events in this snapshot</span><div className="chart-legend"><span><i/>Success</span><span><i/>Other outcomes</span></div></div>
      {dated.length ? <><div className="activity-chart" role="img" aria-label={`${dated.length} timestamped events across 16 time intervals; ${success} successful, ${denied} denied and ${failed} failed in the full snapshot.`}>{buckets.map((bucket,i) => <div key={i} className="activity-column" title={`Interval ${i+1}: ${bucket.success} successful, ${bucket.other} other outcomes`}><div style={{height:`${(bucket.success+bucket.other)/peak*100}%`}}><i className="chart-other" style={{flex:bucket.other}}/><i className="chart-success" style={{flex:bucket.success}}/></div></div>)}</div><div className="chart-axis"><span>{formatTime(start)}</span><span>{formatTime(end)}</span></div></> : <div className="chart-empty"><strong>Waiting for recorded activity</strong><span>Timestamped audit events will populate this chart.</span></div>}
      <div className="activity-outcomes"><div><i className="outcome-mark success"/><span>Successful</span><strong>{loadedSources.events ? success : '—'}</strong></div><div><i className="outcome-mark denied"/><span>Denied</span><strong>{loadedSources.events ? denied : '—'}</strong></div><div><i className="outcome-mark failure"/><span>Failed</span><strong>{loadedSources.events ? failed : '—'}</strong></div></div>
    </article>
    <article className="panel decision-spotlight">
      <div className="telemetry-heading"><div><span className="eyebrow">LATEST POLICY DECISION</span><h2>Protection intelligence</h2></div></div>
      <div className="spotlight-mode"><div><small>POLICY-SELECTED MODE</small><strong>{latest?.selectedMode || 'Awaiting decision'}</strong><span>{latest ? `${latest.riskLevel} effective risk` : 'No recorded policy decision'}</span></div></div>
      {latest && <p>{verificationNote}</p>}
      <p>{latest?.selectionReason || 'The next saved execution will show the policy rationale and selected cryptographic profile here.'}</p>
      <div className="spotlight-meta"><div><small>MODEL SCORE</small><strong>{Number.isFinite(latest?.riskScore) ? `${Math.round(latest.riskScore*100)}%` : '—'}</strong></div><div><small>POLICY VERSION</small><strong>{latest?.policyVersion || '—'}</strong></div></div>
      <a href="#decision" className="inspect-link">Explore decision journey</a>
    </article>
  </section>;
}
