import React from 'react';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {OperationalAlerts} from './OperationalAlerts.jsx';
import {App} from './main.jsx';

const response = (body, status=200) => ({ok:status>=200 && status<300,status,json:async()=>body});
const outbox = {pending:0,dead:0,delivered:7,oldestPendingEventAgeSeconds:0,recentDead:[]};
const alerts = {source:'Prometheus',retrievedAt:'2026-10-20T12:00:00Z',alerts:[{
  name:'AuditOutboxDeadEvents',state:'firing',application:'auth-service',instance:'fixture:8081',
  severity:'critical',summary:'RESTRICTED_OPERATIONAL_MARKER',description:'Synthetic privileged observation',activeAt:''
}]};
const deferred = () => {
  let resolve;
  const promise = new Promise(done => {resolve=done;});
  return {promise,resolve};
};
const healthyBatch = () => fetch.mockResolvedValueOnce(response(alerts))
  .mockResolvedValueOnce(response(outbox)).mockResolvedValueOnce(response(outbox));

describe('Operational snapshot access/session boundaries', () => {
  beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
  afterEach(() => vi.unstubAllGlobals());

  async function initialView(logout=vi.fn()) {
    healthyBatch();
    const user = userEvent.setup();
    const view = render(<OperationalAlerts token="old.fixture.token" onLogout={logout}/>);
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    await screen.findByText('RESTRICTED_OPERATIONAL_MARKER');
    return {user,view};
  }

  it('clears privileged snapshots immediately on403 without waiting for a slow peer', async () => {
    const {user} = await initialView();
    const slowA=deferred(), slowB=deferred();
    fetch.mockResolvedValueOnce(response({message:'Denied'},403))
      .mockReturnValueOnce(slowA.promise).mockReturnValueOnce(slowB.promise);
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    expect(await screen.findByText(/Administrator access required/)).toBeInTheDocument();
    expect(screen.queryByText('RESTRICTED_OPERATIONAL_MARKER')).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(6);
    expect(fetch.mock.calls.slice(4).every(([,options]) => options.signal.aborted)).toBe(true);
    expect(screen.getByRole('button',{name:'Load operational alerts'})).toBeEnabled();
    await act(async () => {slowA.resolve(response(outbox));slowB.resolve(response(outbox));});
    expect(screen.getByText(/Administrator access required/)).toBeInTheDocument();
    expect(screen.queryByText('RESTRICTED_OPERATIONAL_MARKER')).not.toBeInTheDocument();
  });

  it('logs out immediately on401 and cancels peers even if they ignore cancellation', async () => {
    const logout=vi.fn();
    const {user}=await initialView(logout);
    const slow=deferred();
    fetch.mockResolvedValueOnce(response({message:'Expired'},401))
      .mockReturnValueOnce(slow.promise).mockReturnValueOnce(slow.promise);
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    await waitFor(() => expect(logout).toHaveBeenCalledOnce());
    expect(screen.queryByText('RESTRICTED_OPERATIONAL_MARKER')).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledTimes(6);
    expect(fetch.mock.calls.slice(4).every(([,options]) => options.signal.aborted)).toBe(true);
    await act(async () => slow.resolve(response(outbox)));
    expect(logout).toHaveBeenCalledOnce();
  });

  it.each([401,403])('ignores late old-session%s and old snapshots after token replacement', async status => {
    const logout=vi.fn();
    const {user,view}=await initialView(logout);
    const old=deferred();
    fetch.mockReturnValueOnce(old.promise).mockReturnValueOnce(old.promise).mockReturnValueOnce(old.promise);
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    view.rerender(<OperationalAlerts token="new.fixture.token" onLogout={logout}/>);
    expect(screen.queryByText('RESTRICTED_OPERATIONAL_MARKER')).not.toBeInTheDocument();
    healthyBatch();
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    await screen.findByText('RESTRICTED_OPERATIONAL_MARKER');
    await act(async () => old.resolve(response({message:'Old session'},status)));
    expect(logout).not.toHaveBeenCalled();
    expect(screen.getByText('RESTRICTED_OPERATIONAL_MARKER')).toBeInTheDocument();
  });

  it('allows a fresh load after403 while ignored old successes cannot repopulate it', async () => {
    const {user}=await initialView();
    const stale=deferred();
    fetch.mockResolvedValueOnce(response({},403)).mockReturnValueOnce(stale.promise).mockReturnValueOnce(stale.promise);
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    await screen.findByText(/Administrator access required/);
    fetch.mockResolvedValueOnce(response({...alerts,alerts:[]}))
      .mockResolvedValueOnce(response(outbox)).mockResolvedValueOnce(response(outbox));
    await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
    await screen.findByText('No pending or firing audit alerts in this retrieved snapshot.');
    await act(async () => stale.resolve(response(outbox)));
    expect(screen.queryByText('RESTRICTED_OPERATIONAL_MARKER')).not.toBeInTheDocument();
    expect(screen.queryByText(/Administrator access required/)).not.toBeInTheDocument();
    expect(screen.getAllByText('Retrieved snapshot')).toHaveLength(3);
  });

  it.each([401,403])('enforces operational%s in the complete dashboard while outbox peers remain slow', async status => {
    const slow=deferred();
    fetch.mockImplementation(path => {
      if (path === '/api/v1/events' || path === '/api/v1/business/executions') return Promise.resolve(response([]));
      if (path === '/api/v1/events/operations/alerts') return Promise.resolve(response({},status));
      return slow.promise;
    });
    sessionStorage.setItem('pqcToken','integration.fixture.token');
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
    if (status === 401) {
      expect(await screen.findByRole('button',{name:'Sign in securely'})).toBeInTheDocument();
      expect(sessionStorage.getItem('pqcToken')).toBeNull();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    } else {
      expect(await screen.findByText(/Administrator access required/)).toBeInTheDocument();
      expect(sessionStorage.getItem('pqcToken')).toBe('integration.fixture.token');
      expect(screen.getByRole('table',{name:'Recorded cryptographic executions'})).toBeInTheDocument();
    }
    const peers=fetch.mock.calls.filter(([path]) => path.endsWith('/audit-outbox'));
    expect(peers).toHaveLength(2);
    expect(peers.every(([,options]) => options.signal.aborted)).toBe(true);
    await act(async () => slow.resolve(response(outbox)));
    if (status === 401) expect(screen.getByLabelText('Username')).toHaveFocus();
    else expect(screen.getByText(/Administrator access required/)).toBeInTheDocument();
  });
});
