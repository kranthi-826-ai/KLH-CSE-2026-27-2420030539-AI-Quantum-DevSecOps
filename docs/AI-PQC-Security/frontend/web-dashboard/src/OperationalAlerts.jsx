import React, {useEffect, useRef, useState} from 'react';
import {api} from './api-client.js';
import './operational-alerts.css';

const names = new Set(['AuditOutboxDeadEvents', 'AuditOutboxOldPendingEvents', 'AuditProducerUnavailable', 'AuditOutboxMetricsUnavailable', 'AdaptiveAuditWriteFailure', 'AdaptiveAuditMetricUnavailable']);
const sources = [['alerts', 'Prometheus alert state', '/api/v1/events/operations/alerts'],
  ['auth', 'Authentication audit outbox', '/api/v1/auth/audit-outbox'],
  ['business', 'Business audit outbox', '/api/v1/business/audit-outbox']];
const initial = () => Object.fromEntries(sources.map(([key]) => [key, {data:null, status:'not-loaded', lastSuccess:null, lastAttempt:null, error:''}]));

export function validOperationalSnapshot(key, data) {
  if (!data || typeof data !== 'object') return false;
  if (key === 'alerts') return data.source === 'Prometheus' && Number.isFinite(Date.parse(data.retrievedAt)) && Array.isArray(data.alerts)
    && data.alerts.length <= 1000 && data.alerts.every(alert => alert && names.has(alert.name) && ['pending', 'firing'].includes(alert.state)
      && ['application', 'instance', 'severity', 'summary', 'description', 'activeAt'].every(field => typeof alert[field] === 'string' && alert[field].length <= 1000));
  return ['pending', 'dead', 'delivered', 'oldestPendingEventAgeSeconds'].every(field => Number.isSafeInteger(data[field]) && data[field] >= 0)
    && Array.isArray(data.recentDead) && data.recentDead.length <= 20 && data.recentDead.every(row => row && typeof row.eventId === 'string'
      && row.eventId.length <= 36 && row.status === 'DEAD' && Number.isSafeInteger(row.attempts) && row.attempts >= 0
      && (row.lastErrorCode == null || typeof row.lastErrorCode === 'string' && row.lastErrorCode.length <= 64));
}

function Receipt({source, loading}) {
  const label = {'not-loaded':'Not loaded', current:'Retrieved snapshot', unavailable:'Unavailable — state unknown', stale:'Stale — refresh failed'}[source.status];
  return <div className={`ops-receipt ${source.status}`}>
    <strong>{label}</strong>
    <span>Last successful retrieval: {source.lastSuccess ? <time dateTime={source.lastSuccess}>{new Date(source.lastSuccess).toLocaleString()}</time> : 'Never'}</span>
    {loading && <span>Refresh in progress; previous state shown</span>}
    {source.error && <span>{source.error}</span>}
  </div>;
}

export function OperationalAlerts({token, onLogout}) {
  const [snapshots, setSnapshots] = useState(initial);
  const [loading, setLoading] = useState(false);
  const [locked, setLocked] = useState(false);
  const controller = useRef(null);
  useEffect(() => {
    setSnapshots(initial()); setLocked(false); setLoading(false);
    return () => controller.current?.abort();
  }, [token]);

  const load = async () => {
    controller.current?.abort();
    const request = new AbortController();
    controller.current = request;
    setLoading(true);
    try {
      const fetchSource = async path => {
        try {
          return await api(path, token, {signal:request.signal});
        } catch (failure) {
          // Revoke retained privileged observations as soon as one source denies
          // access. A slow peer must not postpone clearing data or session exit.
          if (!request.signal.aborted && controller.current === request &&
              (failure.status === 401 || failure.status === 403)) {
            request.abort();
            setSnapshots(initial());
            setLoading(false);
            if (failure.status === 401) onLogout();
            else setLocked(true);
          }
          throw failure;
        }
      };
      const results = await Promise.allSettled(sources.map(([, , path]) => fetchSource(path)));
      if (request.signal.aborted) return;
      setLocked(false);
      const at = new Date().toISOString();
      setSnapshots(previous => Object.fromEntries(sources.map(([key], index) => {
        const result = results[index];
        if (result.status === 'fulfilled' && validOperationalSnapshot(key, result.value)) return [key,
          {data:result.value, status:'current', lastSuccess:at, lastAttempt:at, error:''}];
        return [key, {...previous[key], status:previous[key].data ? 'stale' : 'unavailable', lastAttempt:at,
          error:result.status === 'rejected' ? result.reason?.message || 'Source request failed' : 'Unexpected source response; current state is unknown'}];
      })));
    } finally {
      if (!request.signal.aborted) setLoading(false);
      if (controller.current === request) controller.current = null;
    }
  };

  return <section id="operations" className="ops-panel" tabIndex={-1} aria-labelledby="ops-title">
    <header className="ops-heading"><div><span className="eyebrow">ADMINISTRATOR VIEW</span><h2 id="ops-title">Operational alerts</h2>
      <p>Audit delivery reliability, not AI attack detection. Each source is a separate snapshot.</p></div>
      <button className="refresh" onClick={load} disabled={loading}>{loading ? 'Loading operational alerts' : 'Load operational alerts'}</button></header>
    <p className="ops-email" role="note">Email requested · setup pending. Sender/provider and recipient settings are not configured; email delivery has not been verified.</p>
    {locked ? <p className="ops-access" role="status">Administrator access required. Personal event and execution records remain available in the other dashboard sections.</p> : <div className="ops-grid">
      {sources.map(([key, title]) => {
        const source = snapshots[key];
        return <article className="ops-source" key={key} aria-label={title}><h3>{title}</h3><Receipt source={source} loading={loading}/>
          {source.status === 'stale' && <p>Retained snapshot — do not treat these observations as current state.</p>}
          {!source.data ? <p>No saved snapshot. Current state is unknown.</p> : key === 'alerts' ? <>
            <p className="ops-source-caption">Actual pending/firing states returned by Prometheus. Retrieval time is not alert activation time.</p>
            {source.data.alerts.length === 0 ? <p>No pending or firing audit alerts in this retrieved snapshot.</p> : <ul className="ops-alert-list">{source.data.alerts.map((alert, index) =>
              <li key={`${alert.name}-${alert.instance}-${index}`}><span className={`ops-state ${alert.state}`}>{alert.state}</span><h4>{alert.summary || alert.name}</h4>
                <p>{alert.description}</p><dl><dt>Producer / target</dt><dd>{alert.application || 'Not supplied'} / {alert.instance || 'Not supplied'}</dd>
                  <dt>Active since</dt><dd>{alert.activeAt && Number.isFinite(Date.parse(alert.activeAt)) ? new Date(alert.activeAt).toLocaleString() : 'Not supplied'}</dd></dl></li>)}</ul>}
          </> : <>
            <dl className="ops-counts"><div><dt>Pending</dt><dd>{source.data.pending}</dd></div><div><dt>Needs recovery</dt><dd>{source.data.dead}</dd></div><div><dt>Delivered</dt><dd>{source.data.delivered}</dd></div></dl>
            <p>{source.data.dead > 0 ? `${source.data.dead} retained events need operator recovery.` : 'No DEAD events in this retrieved snapshot.'}</p>
            <p>Oldest pending event age: {source.data.oldestPendingEventAgeSeconds}s. This is occurrence age, not queue residence time.</p>
            {source.data.recentDead.length > 0 && <details><summary>Inspect recent DEAD event metadata</summary><ul className="ops-dead-list">{source.data.recentDead.map(row => <li key={row.eventId}>
              <code>{row.eventId}</code><span>{row.attempts} attempts · {row.lastErrorCode || 'No error code recorded'}</span></li>)}</ul></details>}
          </>}
        </article>;
      })}
    </div>}
    <p className="ops-footnote">Read-only view. Outbox observations do not establish a firing alert; Prometheus applies its own scrape intervals and hold times. Recovery requires explicit administrator preview/apply through the recovery API.</p>
  </section>;
}
