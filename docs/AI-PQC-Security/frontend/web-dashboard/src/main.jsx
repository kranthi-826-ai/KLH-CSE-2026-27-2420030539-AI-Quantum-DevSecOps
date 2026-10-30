import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import './styles.css';
import './execution.css';
import {EvidenceOverview} from './EvidenceOverview.jsx';
import './overview.css';
import {OperationalTelemetry} from './OperationalTelemetry.jsx';
import {OperationalAlerts} from './OperationalAlerts.jsx';
import './console.css';
import './accessibility.css';
import './quiet-ui.css';
import {SourceFreshness, initialFreshness, nextFreshness} from './SourceFreshness.jsx';

import {api} from './api-client.js';
import {validSnapshot} from './snapshot-contract.js';
export {api} from './api-client.js';

const labelize = value => value ? value.replaceAll('_', ' ').replace(/\b\w/g, letter => letter.toUpperCase()) : 'Not available';
const riskTone = value => value?.toLowerCase() || 'neutral';

function Login({onLogin}) {
  const usernameInput = useRef(null);
  const loginRequest = useRef(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  useEffect(() => {
    usernameInput.current?.focus();
    return () => loginRequest.current?.abort();
  }, []);

  const submit = async event => {
    event.preventDefault();
    if (loginRequest.current) return;
    const request = new AbortController();
    loginRequest.current = request;
    setError('');
    setSubmitting(true);
    try {
      const result = await api('/api/v1/auth/login', '', {
        method: 'POST', body: JSON.stringify({username, password}), signal:request.signal
      });
      if (request.signal.aborted) return;
      // Structural validation only; JWT authenticity/authorization remains server-side.
      if (typeof result?.token !== 'string' || result.token.length > 8192 ||
          !/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(result.token)) {
        throw new Error('Sign-in response did not contain a valid session token. Please retry.');
      }
      sessionStorage.setItem('pqcToken', result.token);
      onLogin(result.token);
    } catch (requestError) {
      if (!request.signal.aborted) setError(requestError.message);
    } finally {
      if (!request.signal.aborted) setSubmitting(false);
      if (loginRequest.current === request) loginRequest.current = null;
    }
  };

  return <main className="login-page">
    <section className="login-story" aria-label="Platform overview">
      <div className="brand brand-large"><span>AI-PQC Shield</span></div>
      <div className="login-copy">
        <span className="eyebrow">ADAPTIVE SECURITY RESEARCH PLATFORM</span>
        <h1>Inspect every adaptive-security decision.</h1>
        <p>For each submitted flow, see the model score, effective policy risk, selected protection mode and saved execution evidence.</p>
      </div>
      <div className="login-flow">
        <FlowPoint title="Submit" text="Request and flow features"/>
        <FlowPoint title="Decide" text="AI risk and policy"/>
        <FlowPoint title="Execute" text="Classical, hybrid or PQC"/>
      </div>
      <p className="research-note">Research prototype using UNSW-NB15 and NIST-standardized PQC algorithms.</p>
    </section>
    <section className="login-panel">
      <form onSubmit={submit} aria-busy={submitting}>
        <div className="mobile-brand brand"><span>AI-PQC Shield</span></div>
        <span className="eyebrow">SECURE ACCESS</span>
        <h2>Welcome back</h2>
        <p>Sign in to view the adaptive security control plane.</p>
        <label>Username<input ref={usernameInput} name="username" required maxLength={50} autoComplete="username" aria-describedby={error ? 'login-error' : undefined} value={username} onChange={event => setUsername(event.target.value)} /></label>
        <label>Password<input name="password" required autoComplete="current-password" type="password" aria-describedby={error ? 'login-error' : undefined} value={password} onChange={event => setPassword(event.target.value)} /></label>
        {error && <div id="login-error" className="error" role="alert">{error}</div>}
        <button className="primary-button" disabled={submitting}>{submitting ? 'Verifying…' : 'Sign in securely'}</button>
        <div className="trust-row"><span>Research dashboard · Sign in with an existing account</span></div>
      </form>
    </section>
  </main>;
}

function FlowPoint({title, text}) {
  return <div><section><strong>{title}</strong><small>{text}</small></section></div>;
}

function Dashboard({token, onLogout}) {
  const overview = useRef(null);
  const snapshotRequest = useRef(null);
  const [events, setEvents] = useState([]);
  const [runs, setRuns] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [runQuery, setRunQuery] = useState('');
  const [eventQuery, setEventQuery] = useState('');
  const [eventOutcome, setEventOutcome] = useState('ALL');
  const [eventCorrelation, setEventCorrelation] = useState('');
  const [activeSection, setActiveSection] = useState('overview');
  const [loadedSources, setLoadedSources] = useState({events:false, runs:false});
  const [sourceFreshness, setSourceFreshness] = useState(initialFreshness);
  const updatedAt = useMemo(() => {
    const times = Object.values(sourceFreshness).map(source => Date.parse(source.lastSuccessAt)).filter(Number.isFinite);
    return times.length ? new Date(Math.max(...times)) : null;
  }, [sourceFreshness]);
  const sectionIds = ['overview', 'decision', 'executions', 'events', 'operations'];
  const focusSection = id => {
    const target = document.getElementById(id);
    target?.focus({preventScroll:true});
    target?.scrollIntoView?.({behavior:'instant', block:'start'});
    setActiveSection(id);
  };
  const navigate = id => {
    window.location.hash = id;
    focusSection(id);
  };
  const followSection = (event, id) => {
    // Preserve native open-in-new-tab behavior for modified link activation.
    if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
    event.preventDefault();
    navigate(id);
  };
  useEffect(() => {
    const followHash = () => {
      const id = window.location.hash.slice(1);
      if (sectionIds.includes(id)) focusSection(id);
    };
    if (sectionIds.includes(window.location.hash.slice(1))) followHash();
    else overview.current?.focus({preventScroll:true});
    window.addEventListener('hashchange', followHash);
    return () => window.removeEventListener('hashchange', followHash);
  }, []);

  const load = async () => {
    snapshotRequest.current?.abort();
    const request = new AbortController();
    snapshotRequest.current = request;
    setLoading(true);
    setError('');
    const fetchSnapshot = async (name, path, setter) => {
      try {
        return await api(path, token, {signal:request.signal});
      } catch (failure) {
        if (!request.signal.aborted && failure.status === 401) {
          request.abort();
          onLogout();
        } else if (!request.signal.aborted && failure.status === 403) {
          // A denied source is no longer safe to retain, even while another request is slow.
          setter([]);
          setLoadedSources(previous => ({...previous, [name]:false}));
          setSourceFreshness(previous => ({...previous, [name]:{
            status:'forbidden', lastSuccessAt:null, lastAttemptAt:new Date().toISOString()
          }}));
          if (name === 'runs') { setSelectedId(null); setEventCorrelation(''); }
        }
        throw failure;
      }
    };
    try {
      const [eventResult, runResult] = await Promise.allSettled([
        fetchSnapshot('events', '/api/v1/events', setEvents),
        fetchSnapshot('runs', '/api/v1/business/executions', setRuns)
      ]);
      if (request.signal.aborted) return;
      const results = [eventResult, runResult];
      if (results.some(result => result.status === 'rejected' && result.reason.status === 401)) { onLogout(); return; }
      const failures = [];
      const completedAt = new Date().toISOString();
      for (const [name, result, setter] of [['events', eventResult, setEvents], ['runs', runResult, setRuns]]) {
        if (result.status === 'rejected' && result.reason?.status === 403) {
          failures.push(`${name === 'events' ? 'Security events' : 'Executions'}: Access denied; previous records cleared`);
          continue;
        }
        const succeeded = result.status === 'fulfilled' && validSnapshot(name, result.value);
        setSourceFreshness(previous => ({...previous, [name]:nextFreshness(previous[name], succeeded, completedAt)}));
        if (succeeded) {
          setter(result.value);
          setLoadedSources(previous => ({...previous, [name]:true}));
        } else failures.push(`${name === 'events' ? 'Security events' : 'Executions'}: ${result.status === 'rejected' ? result.reason.message : 'Unexpected API response'}`);
      }
      if (failures.length) setError(failures.join(' · '));
    } catch (requestError) {
      if (request.signal.aborted) return;
      if (requestError.status === 401) { onLogout(); return; }
      setError(requestError.message);
    } finally {
      if (!request.signal.aborted) setLoading(false);
    }
  };

  useEffect(() => {
    load();
    return () => snapshotRequest.current?.abort();
  }, [token]);

  const stats = useMemo(() => {
    const completed = runs.filter(run => run.outcome === 'SUCCESS');
    const verified = completed.filter(run => run.roundTripVerified).length;
    const denied = events.filter(event => event.outcome === 'DENIED' || event.outcome === 'FAILURE').length;
    return {
      events: events.length,
      runs: runs.length,
      denied,
      verified: completed.length ? `${verified}/${completed.length}` : '—',
      latency: completed.length ? `${Math.round(completed.reduce((sum, run) => sum + run.totalLatencyMillis, 0) / completed.length)} ms` : '—'
    };
  }, [events, runs]);

  const latest = runs.find(run => run.executionId === selectedId) || runs[0];
  const relatedEvents = latest?.correlationId ? events.filter(event => event.correlationId === latest.correlationId) : [];
  const latestEvent = relatedEvents[0];
  const decisionReason = latest?.selectionReason || 'No recorded selection reason for this execution.';
  const hasDecision = Boolean(latest?.decisionId && latest?.riskLevel);
  const hasCompleted = latest?.outcome === 'SUCCESS';
  const cryptoVerified = latest?.roundTripVerified === true;

  return <div className="app-shell">
    <a className="skip-link" href="#overview" onClick={event => followSection(event, 'overview')}>Skip to dashboard content</a>
    <aside className="sidebar">
      <div className="brand"><span>AI-PQC Shield</span></div>
      <div className="workspace-switch"><div><strong>Security workspace</strong><small>Development environment</small></div></div>
      <span className="workspace-label">CONTROL CENTER</span>
      <nav aria-label="Dashboard sections">
        {[['overview', 'Overview'], ['decision', 'Decision journey'], ['executions', 'Crypto executions'], ['events', 'Security events'], ['operations', 'Operational alerts']].map(([id, title]) => <a key={id} className={activeSection === id ? 'active' : ''} aria-current={activeSection === id ? 'location' : undefined} href={`#${id}`} onClick={event => followSection(event, id)}><span>{title}</span></a>)}
      </nav>
      <div className="system-card"><div><strong>{error ? 'Refresh failed' : updatedAt ? 'Snapshot loaded' : 'Loading snapshot'}</strong><small>Service health is not verified here</small></div></div>
      <button className="logout" onClick={onLogout}>Sign out</button>
    </aside>

    <main className="dashboard" id="overview" ref={overview} tabIndex={-1} aria-labelledby="dashboard-title">
      <header className="topbar">
        <div><div className="console-breadcrumb"><span>Workspace</span><span>Overview</span><span className="environment-chip">DEVELOPMENT</span></div><h1 id="dashboard-title">Adaptive security overview</h1><p>Threat intelligence. Policy decisions. Cryptographic evidence.</p></div>
        <div className="header-actions"><span className="updated">{updatedAt ? `Latest source retrieval ${updatedAt.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}` : loading ? 'Connecting…' : 'No source retrieved'}</span><button className="refresh" onClick={load} disabled={loading}>{loading ? 'Refreshing' : 'Refresh data'}</button></div>
      </header>

      {error && <div className="error" role="alert">Unable to refresh dashboard: {error}</div>}
      <section className={`status-strip ${error ? 'snapshot-warning' : ''}`} role="status"><div><strong>{error ? updatedAt ? 'Partial evidence available · refresh needed' : 'Evidence unavailable · check services' : updatedAt ? 'Research evidence loaded' : 'Loading research evidence'}</strong><span>Execution records show model score, effective policy decision, cryptography and audit evidence.</span></div><span className="status-badge">SNAPSHOT</span></section>

      <p className="research-note" role="note">Access-scoped snapshot: users see only their own records; administrators can review global records. Each source returns up to 100 recent records, not a complete system history.</p>

      <section className="metric-grid" aria-label="Snapshot metrics">
        <Metric label="Observed events" value={loadedSources.events ? stats.events : '—'} detail={loadedSources.events ? `${stats.denied} denied or failed` : 'Waiting for monitoring data'}/>
        <Metric label="Execution records" value={loadedSources.runs ? stats.runs : '—'} detail={loadedSources.runs ? 'Latest returned records' : 'Waiting for business data'}/>
        <Metric label="Round trips verified" value={stats.verified} detail="Among completed executions"/>
        <Metric label="Mean recorded time" value={stats.latency} detail="Completed flows only"/>
      </section>

      <OperationalTelemetry events={events} runs={runs} loadedSources={loadedSources}/>
      <SourceFreshness sources={sourceFreshness} refreshing={loading}/>
      <OperationalAlerts token={token} onLogout={onLogout}/>
      <EvidenceOverview runs={runs} events={events} updatedAt={updatedAt} loadedSources={loadedSources} sourceFreshness={sourceFreshness}/>

      <section className="section-heading" id="decision" tabIndex={-1} aria-labelledby="decision-title"><div><span className="section-number">01</span><div><h2 id="decision-title">Why this protection was selected</h2><p>Inspect one saved execution. Model score and effective policy risk can differ.</p></div></div><RiskLegend/></section>
      <div className="run-selector"><label htmlFor="selected-run">Execution to inspect</label><select id="selected-run" disabled={!runs.length} value={latest?.executionId || ''} onChange={event => setSelectedId(event.target.value)}><option value="" disabled>Select an execution</option>{runs.map(run => <option key={run.executionId} value={run.executionId}>{run.executionId} · {run.outcome || 'Unknown outcome'}</option>)}</select>{latest?.correlationId && <button type="button" onClick={() => { setEventCorrelation(latest.correlationId); navigate('events'); }}>View related audit events</button>}</div>
      {latest && !hasCompleted && <p className="error" role="note">Flow did not complete successfully. {latest.errorDetail || latest.outcome || 'No completed outcome recorded'}. {cryptoVerified ? 'Cryptographic check passed, but the overall request failed. This is not a successful protected request.' : 'A selected mode alone is not proof that cryptography executed.'}</p>}

      <section className="decision-journey">
        <JourneyStep number="1" title="Request recorded" badge={latest ? labelize(latest.outcome) : 'No data'}>
          <p>{latest ? `Execution ${latest.executionId} was recorded${latest.username ? ` for ${latest.username}` : ''}.` : 'No adaptive execution has been collected yet.'}</p>
          <small>{latestEvent ? `Related audit: ${labelize(latestEvent.eventType)}` : 'No matching audit event in this snapshot.'}</small>
        </JourneyStep>
        <JourneyStep number="2" title="Model score" badge={hasDecision ? `${Math.round(latest.riskScore * 100)}% attack probability` : 'No decision'} tone={riskTone(latest?.riskLevel)}>
          <p>{hasDecision ? 'A model scored the submitted network-flow features. This is not model accuracy or proof of an attack.' : 'No recorded model decision for this execution.'}</p>
          <small>Model version: {latest?.modelVersion || 'Not available'}</small>
        </JourneyStep>
        <JourneyStep number="3" title="Effective policy risk" badge={hasDecision ? `${latest.riskLevel} · ${latest.selectedMode || 'No mode'}` : 'No decision'} tone={riskTone(latest?.riskLevel)}>
          <p>{decisionReason}</p>
          <small>Policy version: {latest?.policyVersion || 'Not available'}</small>
        </JourneyStep>
        <JourneyStep number="4" title="Seal/open check" badge={hasCompleted ? cryptoVerified ? 'VERIFIED' : 'NOT VERIFIED' : cryptoVerified ? 'CRYPTO VERIFIED · FLOW FAILED' : 'NOT COMPLETED'} tone={hasCompleted && cryptoVerified ? 'success' : 'neutral'}>
          <p>{latest?.algorithmProfile || 'No cryptographic profile recorded.'}</p>
          <small>{hasCompleted || cryptoVerified ? `${latest.cryptoLatencyMillis} ms cryptography · ${latest.totalLatencyMillis} ms recorded` : 'No completed execution timing recorded'}</small>
        </JourneyStep>
      </section>

      <section className="explanation-grid">
        <article className="panel risk-panel">
          <div className="panel-heading"><div><div><h3>Model assessment</h3><p>Attack probability for the submitted network-flow features</p></div></div><span className={`risk-chip ${riskTone(latest?.riskLevel)}`}>Policy: {hasDecision ? latest.riskLevel : 'NO DATA'}</span></div>
          <div className="risk-content"><div className={`risk-gauge ${riskTone(latest?.riskLevel)}`} style={{'--score': `${hasDecision ? Math.round(latest.riskScore * 100) : 0}%`}}><div><strong>{hasDecision ? `${Math.round(latest.riskScore * 100)}%` : '—'}</strong><span>model score</span></div></div><div className="risk-copy"><h4>{riskHeadline(latest)}</h4><p>{riskDescription(latest)}</p><div className="thresholds"><span><i className="low"/>Model low &lt;35%</span><span><i className="medium"/>Model medium 35–&lt;70%</span><span><i className="high"/>Model high ≥70%</span></div></div></div>
        </article>
        <article className="panel rationale-panel">
          <div className="panel-heading"><div><div><h3>Policy rationale</h3><p>Explainable mapping from risk to cryptography</p></div></div></div>
          <div className="mode-callout"><span className="mode-label">SELECTED MODE</span><strong>{latest?.selectedMode || 'Awaiting decision'}</strong><code>{latest?.algorithmProfile || 'No algorithm profile selected'}</code></div>
          <p className="reason">{decisionReason}</p><p className="policy-note">Effective risk can be raised by data sensitivity. The saved explanation is the authoritative reason; this view does not expose every policy input.</p>
        </article>
      </section>

      <LatencyPanel latest={latest}/>
      <ExecutionTable runs={runs} query={runQuery} onQuery={setRunQuery} onInspect={run => { setSelectedId(run.executionId); navigate('decision'); }}/>
      <EventTable events={events} query={eventQuery} onQuery={setEventQuery} outcome={eventOutcome} onOutcome={setEventOutcome} correlation={eventCorrelation} onClearCorrelation={() => setEventCorrelation('')}/>

      <footer><span>AI-PQC Shield research prototype</span><i/> <span>Evidence is auditable by correlation ID, model version and policy version.</span></footer>
    </main>
  </div>;
}

function riskDescription(run) {
  if (!run?.decisionId) return 'Submit an adaptive request to see a recorded model and policy decision.';
  return 'The percentage is the model attack score. The policy may raise effective risk based on data sensitivity and compatibility. It does not independently prove an attack.';
}

function riskHeadline(run) {
  return run?.decisionId ? 'Model score and policy risk are separate' : 'Awaiting a network-flow evaluation';
}

function Metric({label, value, detail}) {
  return <article className="metric-card"><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div></article>;
}

function RiskLegend() {
  return <div className="legend"><span><i className="low"/>Low</span><span><i className="medium"/>Medium</span><span><i className="high"/>High</span></div>;
}

function JourneyStep({number, title, badge, tone = 'neutral', children}) {
  return <article className="journey-step"><div className="step-top"><span className="step-number">{number}</span></div><h3>{title}</h3><span className={`journey-badge ${tone}`}>{badge}</span>{children}</article>;
}

function LatencyPanel({latest}) {
  const completed = latest?.outcome === 'SUCCESS';
  const recordedCrypto = completed || latest?.roundTripVerified === true;
  return <article className="panel latency-panel">
    <div className="panel-heading"><div><div><h3>Recorded execution time</h3><p>Policy-service call and cryptographic work; excludes some persistence and response work</p></div></div><strong className="total-latency">{recordedCrypto ? `${latest.totalLatencyMillis} ms` : '—'} <small>recorded</small></strong></div>
    {!completed && recordedCrypto && <p>Crypto check passed within a failed flow. These timings do not establish successful request completion.</p>}
    {recordedCrypto ? <div className="latency-bars"><Bar name="Policy service call" value={latest.policyLatencyMillis} total={latest.totalLatencyMillis}/><Bar name="Cryptographic execution" value={latest.cryptoLatencyMillis} total={latest.totalLatencyMillis}/><Bar name="Other recorded work" value={Math.max(0, latest.totalLatencyMillis - latest.policyLatencyMillis - latest.cryptoLatencyMillis)} total={latest.totalLatencyMillis}/></div> : <p className="no-timing">No completed timing recorded for this execution.</p>}
  </article>;
}

function ExecutionTable({runs, query, onQuery, onInspect}) {
  const filtered = runs.filter(run => [run.username, run.executionId, run.correlationId, run.riskLevel, run.selectedMode, run.outcome].some(value => String(value || '').toLowerCase().includes(query.toLowerCase())));
  return <article className="panel data-panel" id="executions" tabIndex={-1} aria-labelledby="executions-title">
    <div className="panel-heading table-heading"><div><div><h3 id="executions-title">Adaptive crypto executions</h3><p>Saved outcomes and policy explanations; latest returned records</p></div></div><span className="record-count" role="status" aria-label="Execution result count">{filtered.length} of {runs.length}</span></div>
    <div className="list-controls"><label>Search executions<input value={query} onChange={event => onQuery(event.target.value)} placeholder="User, mode, risk, ID or outcome"/></label></div>
    <div className="execution-table" role="table" aria-label="Recorded cryptographic executions" aria-colcount={5}>
      <div className="table-header" role="row">{['Risk', 'Protection mode', 'Recorded reason', 'Verification', 'Time / action'].map(title => <span role="columnheader" key={title}>{title}</span>)}</div>
      {filtered.map(run => <div className="table-record" role="row" key={run.executionId}>
        <span role="cell" data-label="Risk"><i aria-hidden="true" className={`risk-dot ${riskTone(run.riskLevel)}`}/><b>{run.decisionId ? run.riskLevel : 'No decision'}</b><small>{run.decisionId ? `${Math.round(run.riskScore * 100)}% model` : ''}</small></span>
        <span role="cell" data-label="Mode"><b>{run.selectedMode || 'Not selected'}</b><small>{run.algorithmProfile || 'No profile'}</small></span>
        <span role="cell" data-label="Reason" className="reason-cell">{run.selectionReason || 'Not recorded'}</span>
        <span role="cell" data-label="Verification" className={`verification ${run.roundTripVerified && run.outcome === 'SUCCESS' ? 'success' : 'neutral'}`}>{run.roundTripVerified ? run.outcome === 'SUCCESS' ? 'Verified' : 'Crypto verified · flow failed' : run.outcome === 'SUCCESS' ? 'Not verified' : 'Not completed'}</span>
        <span role="cell" data-label="Action" className="record-action">{run.outcome === 'SUCCESS' ? `${run.totalLatencyMillis} ms` : run.outcome || 'Unknown'}<button type="button" aria-label={`Inspect decision for execution ${run.executionId}`} onClick={() => onInspect(run)}>Inspect decision</button></span>
      </div>)}
    </div>
    {!filtered.length && <Empty message={runs.length ? 'No executions match this search.' : 'No execution records yet.'}
      hint={runs.length ? 'Clear or broaden the search to see existing executions.' : 'Submit an adaptive request, then refresh this dashboard.'}/>}
  </article>;
}

function EventTable({events, query, onQuery, outcome, onOutcome, correlation, onClearCorrelation}) {
  const filtered = events.filter(event => (outcome === 'ALL' || event.outcome === outcome) && (!correlation || event.correlationId === correlation) && [event.eventType, event.sourceService, event.username, event.requestPath, event.correlationId].some(value => String(value || '').toLowerCase().includes(query.toLowerCase())));
  return <article className="panel data-panel" id="events" tabIndex={-1} aria-labelledby="events-title">
    <div className="panel-heading table-heading"><div><div><h3 id="events-title">Security event timeline</h3><p>Authentication, authorization and protected API activity</p></div></div><span className="record-count" role="status" aria-label="Event result count">{filtered.length} of {events.length}</span></div>
    <div className="list-controls"><label>Search events<input value={query} onChange={event => onQuery(event.target.value)} placeholder="Type, service, user, path or correlation"/></label><label>Outcome<select value={outcome} onChange={event => onOutcome(event.target.value)}><option>ALL</option><option>SUCCESS</option><option>DENIED</option><option>FAILURE</option></select></label>{correlation && <button type="button" onClick={onClearCorrelation}>Clear related-event filter</button>}</div>
    {correlation && <p className="filter-note">Showing correlation ID {correlation}. A correlation ID can be reused; matching does not prove causality.</p>}
    <div className="event-list" role="list" aria-label="Recorded security events">{filtered.map(event => <div className="event-record" role="listitem" key={event.eventId}>
      <div><strong>{labelize(event.eventType)}</strong><small>{event.sourceService} · {event.username || 'Not recorded'}</small></div><code>{event.requestMethod} {event.requestPath}</code><span className={`outcome ${event.outcome?.toLowerCase() || 'neutral'}`}>{event.outcome}</span><time dateTime={Number.isFinite(Date.parse(event.occurredAt)) ? event.occurredAt : undefined}>{Number.isFinite(Date.parse(event.occurredAt)) ? new Date(event.occurredAt).toLocaleString() : 'Time unavailable'}</time>
    </div>)}</div>
    {!filtered.length && <Empty message={events.length ? 'No events match these filters.' : 'No security events yet.'}
      hint={events.length ? 'Clear or broaden the search, outcome or related-event filters.' : 'Complete an authentication or protected API request, then refresh this dashboard.'}/>}
  </article>;
}

function Bar({name, value, total}) {
  const percent = Math.max(value ? 3 : 0, value / Math.max(total, 1) * 100);
  return <div className="latency-row"><div><span>{name}</span><b>{value} ms</b></div><div className="track"><i style={{width: `${percent}%`}}/></div></div>;
}

function Empty({message, hint}) { return <div className="empty"><div><strong>{message}</strong><span>{hint}</span></div></div>; }

export function App() {
  const [token, setToken] = useState(sessionStorage.getItem('pqcToken'));
  return token ? <Dashboard key={token} token={token} onLogout={() => { sessionStorage.removeItem('pqcToken'); setToken(null); }}/> : <Login onLogin={setToken}/>;
}

const rootElement = document.getElementById('root');
if (rootElement) {
  const root = import.meta.hot?.data.root || createRoot(rootElement);
  if (import.meta.hot) import.meta.hot.data.root = root;
  root.render(<App/>);
}
