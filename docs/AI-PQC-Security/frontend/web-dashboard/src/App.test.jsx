import React from 'react';
import {render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {App} from './main.jsx';
import {OperationalTelemetry} from './OperationalTelemetry.jsx';

const response = (body, status = 200) => Promise.resolve({
  ok: status >= 200 && status < 300,
  status,
  json: () => Promise.resolve(body)
});

describe('AI-PQC dashboard', () => {
  beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  it('builds activity telemetry from timestamped events and reports actual outcomes', () => {
    render(<OperationalTelemetry events={[
      {occurredAt:'2026-10-19T08:00:00Z',outcome:'SUCCESS'},
      {occurredAt:'2026-10-19T08:10:00Z',outcome:'DENIED'},
      {occurredAt:'invalid',outcome:'FAILURE'}
    ]} runs={[]} loadedSources={{events:true,runs:true}}/>);
    expect(screen.getByRole('img', {name:'2 timestamped events across 16 time intervals; 1 successful, 1 denied and 1 failed in the full snapshot.'})).toBeInTheDocument();
    expect(screen.getByText('Awaiting decision')).toBeInTheDocument();
  });

  it('shows a clear telemetry empty state when no timestamped evidence exists', () => {
    render(<OperationalTelemetry events={[]} runs={[]} loadedSources={{events:false,runs:false}}/>);
    expect(screen.getByText('Waiting for recorded activity')).toBeInTheDocument();
    expect(screen.queryByRole('img')).not.toBeInTheDocument();
  });

  it('logs in, stores the token for the session, and renders research metrics', async () => {
    fetch
      .mockReturnValueOnce(response({token: 'signed.jwt.value'}))
      .mockReturnValueOnce(response([{eventId:'e1',eventType:'LOGIN_SUCCEEDED',outcome:'SUCCESS',sourceService:'auth-service',username:'researcher',requestPath:'/login',occurredAt:'2026-09-29T10:00:00Z'}]))
      .mockReturnValueOnce(response([{executionId:'x1',decisionId:'d1',riskLevel:'HIGH',riskScore:0.91,selectedMode:'PQC',algorithmProfile:'ML-KEM-768+AES-256-GCM+ML-DSA-65',selectionReason:'High assessed risk and PQC compatibility required post-quantum protection',policyVersion:'1.1.0',modelVersion:'research-model-1',policyLatencyMillis:40,cryptoLatencyMillis:20,totalLatencyMillis:70,roundTripVerified:true,outcome:'SUCCESS'}]));

    const user = userEvent.setup();
    render(<App/>);
    await user.clear(screen.getByLabelText('Username'));
    await user.type(screen.getByLabelText('Username'), 'researcher');
    await user.type(screen.getByLabelText('Password'), 'safe-password');
    await user.click(screen.getByRole('button', {name:'Sign in securely'}));

    expect(await screen.findByText('Adaptive security overview')).toBeInTheDocument();
    expect(screen.getByText(/Access-scoped snapshot: users see only their own records/)).toBeInTheDocument();
    expect(screen.getByRole('region', {name:'Snapshot metrics'})).toBeInTheDocument();
    expect(screen.getAllByText('91%').length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText('ML-KEM-768+AES-256-GCM+ML-DSA-65').length).toBeGreaterThanOrEqual(2);
    expect(screen.getAllByText('High assessed risk and PQC compatibility required post-quantum protection').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('Model score and policy risk are separate')).toBeInTheDocument();
    expect(sessionStorage.getItem('pqcToken')).toBe('signed.jwt.value');
  });

  it('removes an expired token and returns to login after an unauthorized response', async () => {
    sessionStorage.setItem('pqcToken', 'expired.jwt.value');
    fetch.mockReturnValue(response({message:'Token expired'}, 401));
    render(<App/>);

    await waitFor(() => expect(screen.getByRole('button', {name:'Sign in securely'})).toBeInTheDocument());
    expect(sessionStorage.getItem('pqcToken')).toBeNull();
  });

  it('does not invent live health, zero latency, or verified protection when no records exist', async () => {
    sessionStorage.setItem('pqcToken', 'valid.jwt.value');
    fetch.mockReturnValue(response([]));
    render(<App/>);
    expect(await screen.findByText('Research evidence loaded')).toBeInTheDocument();
    expect(screen.getByText('Service health is not verified here')).toBeInTheDocument();
    expect(screen.queryByText('System operational')).not.toBeInTheDocument();
    expect(screen.getByText('No completed timing recorded for this execution.')).toBeInTheDocument();
    expect(screen.getByLabelText('Execution to inspect')).toBeDisabled();
  });

  it('filters event evidence and allows the user to clear the search', async () => {
    sessionStorage.setItem('pqcToken', 'valid.jwt.value');
    fetch
      .mockReturnValueOnce(response([
        {eventId:'e1', eventType:'API_ACCESS_DENIED', outcome:'DENIED', sourceService:'business-service', username:'alice', requestPath:'/secure-data', occurredAt:'2026-09-29T10:00:00Z'},
        {eventId:'e2', eventType:'LOGIN_SUCCEEDED', outcome:'SUCCESS', sourceService:'auth-service', username:'bob', requestPath:'/login', occurredAt:'2026-09-29T10:01:00Z'}
      ]))
      .mockReturnValueOnce(response([]));
    const user = userEvent.setup();
    render(<App/>);
    expect(await screen.findByText('API ACCESS DENIED', {exact:false})).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText('Outcome'), 'DENIED');
    expect(screen.queryByText('LOGIN SUCCEEDED')).not.toBeInTheDocument();
    await user.type(screen.getByLabelText('Search events'), 'nothing-matches');
    expect(screen.getByText('No events match these filters.')).toBeInTheDocument();
    await user.clear(screen.getByLabelText('Search events'));
    expect(screen.getByText('API ACCESS DENIED')).toBeInTheDocument();
  });

  it('keeps execution evidence visible when monitoring is unavailable', async () => {
    sessionStorage.setItem('pqcToken', 'valid.jwt.value');
    fetch.mockReturnValueOnce(response({message:'Monitoring unavailable'}, 503))
      .mockReturnValueOnce(response([{executionId:'partial-x1', decisionId:'d1', riskLevel:'LOW', riskScore:0.2, selectedMode:'CLASSICAL', outcome:'SUCCESS', roundTripVerified:true, policyLatencyMillis:3, cryptoLatencyMillis:2, totalLatencyMillis:5}]));
    render(<App/>);
    expect(await screen.findByText('Partial evidence available · refresh needed')).toBeInTheDocument();
    expect(screen.getByText('Security events: Monitoring unavailable', {exact:false})).toBeInTheDocument();
    expect(screen.getByRole('meter', {name:'Classical share'})).toHaveAttribute('aria-valuenow', '100');
    expect(screen.getByRole('button', {name:'Download evidence JSON'})).toBeEnabled();
  });

  it('exports the available snapshot with source availability and no session token', async () => {
    sessionStorage.setItem('pqcToken', 'private.jwt');
    fetch.mockReturnValue(response([]));
    const createURL = vi.fn(() => 'blob:research-export');
    vi.stubGlobal('URL', Object.assign(class {}, {createObjectURL:createURL, revokeObjectURL:vi.fn()}));
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await user.click(screen.getByRole('button', {name:'Download evidence JSON'}));
    expect(createURL).toHaveBeenCalledOnce();
    expect(click).toHaveBeenCalledOnce();
    const blob = createURL.mock.calls[0][0];
    const reader = new FileReader();
    const content = await new Promise(resolve => {reader.onload = () => resolve(reader.result); reader.readAsText(blob);});
    const exported = JSON.parse(content);
    expect(exported.loadedSources).toEqual({events:true, runs:true});
    expect(exported.executions).toEqual([]);
    expect(content).not.toContain('private.jwt');
    click.mockRestore();
  });
});
