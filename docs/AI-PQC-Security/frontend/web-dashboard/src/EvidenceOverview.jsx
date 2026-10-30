import React from 'react';

const MODES = [
  {name:'CLASSICAL', title:'Classical', description:'Conventional cryptography selected by the policy.', tone:'classical'},
  {name:'HYBRID', title:'Hybrid', description:'Classical and post-quantum mechanisms combined.', tone:'hybrid'},
  {name:'PQC', title:'Post-quantum', description:'Post-quantum mechanisms in the recorded profile.', tone:'pqc'}
];

export function EvidenceOverview({runs, events, updatedAt, loadedSources, sourceFreshness}) {
  const decisions = runs.filter(run => run.decisionId && run.selectedMode && run.outcome === 'SUCCESS' && run.roundTripVerified === true);
  const unverifiedCount = runs.length - decisions.length;
  const services = [...new Set(events.map(event => event.sourceService).filter(Boolean))].sort();
  const exportEvidence = () => {
    const report = {
      schemaVersion:2, exportedAt:new Date().toISOString(),
      snapshotAt:updatedAt?.toISOString() || null,
      snapshotTimeMeaning:'Latest successful source retrieval; sources may have different ages. Consult sourceFreshness.',
      scope:'Latest API snapshot; not lifetime totals or an ML benchmark',
      loadedSources, sourceFreshness, executions:runs, events
    };
    const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
    const link = document.createElement('a');
    link.href = url;
    link.download = `ai-pqc-evidence-${new Date().toISOString().slice(0,10)}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return <section className="evidence-overview" aria-label="Protection and service evidence">
    <article className="panel protection-summary">
      <div className="summary-heading"><div><span className="eyebrow">PROTECTION DISTRIBUTION</span><h2>How requests were protected</h2></div></div>
      <p className="summary-description">Modes across {decisions.length} completed, verified executions. {unverifiedCount} other records are excluded; a policy selection alone is not executed protection.</p>
      <div className="mode-summary-grid">{MODES.map(mode => {
        const count = decisions.filter(run => run.selectedMode === mode.name).length;
        const percentage = decisions.length ? Math.round(count / decisions.length * 100) : 0;
        return <div key={mode.name} className={`mode-summary ${mode.tone}`}>
          <div><span>{mode.title}</span><strong>{loadedSources.runs ? count : '—'}</strong></div>
          <div className="mode-track" role="meter" aria-label={`${mode.title} share`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percentage}><i style={{width:`${percentage}%`}}/></div>
          <small>{decisions.length ? `${percentage}% of verified executions` : 'Awaiting verified executions'}</small><p>{mode.description}</p>
        </div>;
      })}</div>
      <p className="evidence-note">Encryption protects data. Blocking malicious requests requires a separate enforcement decision.</p>
    </article>
    <article className="panel evidence-summary">
      <div className="summary-heading"><div><span className="eyebrow">AUDIT WORKSPACE</span><h2>Evidence you can trace</h2></div></div>
      <p className="summary-description">Services represented in the returned audit records. Presence here indicates recorded activity, not current service health.</p>
      <div className="service-evidence">{services.length ? services.map(service => <div key={service}><span>{service}</span><strong>{events.filter(event => event.sourceService === service).length}<small> events</small></strong></div>) : <p>{loadedSources.events ? 'No service activity recorded yet.' : 'Monitoring data has not loaded yet.'}</p>}</div>
      <button type="button" className="export-evidence" disabled={!updatedAt} onClick={exportEvidence}>Download evidence JSON</button>
      <small className="export-caption">Includes available execution records, audit events and snapshot time. Handle exported audit data with care.</small>
    </article>
  </section>;
}
