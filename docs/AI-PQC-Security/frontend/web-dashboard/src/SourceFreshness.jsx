import React from 'react';
import './source-freshness.css';

export const initialFreshness = () => ({
  events: {status:'not-loaded', lastSuccessAt:null, lastAttemptAt:null},
  runs: {status:'not-loaded', lastSuccessAt:null, lastAttemptAt:null}
});

export function nextFreshness(previous, succeeded, at) {
  return {
    status:succeeded ? 'current' : previous.lastSuccessAt ? 'stale' : 'unavailable',
    lastSuccessAt:succeeded ? at : previous.lastSuccessAt,
    lastAttemptAt:at
  };
}

export function SourceFreshness({sources, refreshing}) {
  return <section className="source-freshness" aria-label="Evidence source freshness">
    <p>Each source has its own retrieval time. Retained records may be stale; retrieval time is not event time or proof of service health.</p>
    <dl>{[['events', 'Security events'], ['runs', 'Crypto executions']].map(([key, name]) => {
      const source = sources[key];
      const status = {'not-loaded':'Not loaded', current:'Retrieved', stale:'Stale — last refresh failed', unavailable:'Unavailable — no saved snapshot', forbidden:'Access denied — previous records cleared'}[source.status];
      return <div key={key} className={`source-state ${source.status}`}>
        <dt>{name}</dt><dd><strong>{status}</strong>
          {refreshing && <span>Refresh in progress; showing previous retrieval state</span>}
          <span>Last successful retrieval: {source.lastSuccessAt ? <time dateTime={source.lastSuccessAt}>{new Date(source.lastSuccessAt).toLocaleString()}</time> : 'Never'}</span>
          {source.lastAttemptAt && <span>Last completed attempt: <time dateTime={source.lastAttemptAt}>{new Date(source.lastAttemptAt).toLocaleString()}</time></span>}
        </dd>
      </div>;
    })}</dl>
  </section>;
}
