import React from 'react';
import {act, render, screen, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {App} from './main.jsx';

const response = (body, status=200) => ({ok:status>=200 && status<300, status, json:async () => body});
const event = {eventId:'restricted-e1',eventType:'RESTRICTED_AUDIT_MARKER',outcome:'SUCCESS',sourceService:'auth-service'};
const run = {executionId:'restricted-x1',decisionId:'d1',username:'restricted-owner',riskLevel:'LOW',riskScore:.2,
  selectedMode:'CLASSICAL',outcome:'SUCCESS',roundTripVerified:true,policyLatencyMillis:1,cryptoLatencyMillis:2,totalLatencyMillis:3};
const deferred = () => {
  let resolve;
  const promise = new Promise(done => { resolve=done; });
  return {promise, resolve};
};

describe('Evidence session/access boundaries', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it('clears a denied source before a slow peer finishes and excludes its data from exports', async () => {
    sessionStorage.setItem('pqcToken', 'private.test.token');
    const slow = deferred();
    fetch.mockResolvedValueOnce(response([event])).mockResolvedValueOnce(response([run]))
      .mockResolvedValueOnce(response({message:'Denied'},403)).mockReturnValueOnce(slow.promise);
    const createURL = vi.fn(() => 'blob:access-boundary');
    vi.stubGlobal('URL', Object.assign(class {}, {createObjectURL:createURL,revokeObjectURL:vi.fn()}));
    vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(() => {});
    const user = userEvent.setup();
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await user.click(screen.getByRole('button', {name:'Refresh data'}));
    await screen.findByText('Access denied — previous records cleared');
    expect(screen.queryByText('RESTRICTED AUDIT MARKER')).not.toBeInTheDocument();
    expect(screen.getByRole('button', {name:'Refreshing'})).toBeDisabled();
    expect(screen.getByRole('button', {name:'Inspect decision for execution restricted-x1'})).toBeInTheDocument();
    await user.click(screen.getByRole('button', {name:'Download evidence JSON'}));
    const reader = new FileReader();
    const text = await new Promise(resolve => {reader.onload=()=>resolve(reader.result);reader.readAsText(createURL.mock.calls[0][0]);});
    const report = JSON.parse(text);
    expect(report.events).toEqual([]);
    expect(report.loadedSources.events).toBe(false);
    expect(report.sourceFreshness.events).toMatchObject({status:'forbidden',lastSuccessAt:null});
    expect(report.executions).toHaveLength(1);
    expect(text).not.toContain('restricted-e1');
    expect(text).not.toContain('private.test.token');
    await act(async () => slow.resolve(response([run])));
    await screen.findByText('Partial evidence available · refresh needed');
  });

  it('clears both denied sources, selected decision and export eligibility without inventing empty retrievals', async () => {
    sessionStorage.setItem('pqcToken','synthetic.test.token');
    fetch.mockResolvedValueOnce(response([event])).mockResolvedValueOnce(response([run]))
      .mockResolvedValueOnce(response({},403)).mockResolvedValueOnce(response({},403));
    const user = userEvent.setup();
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await user.click(screen.getByRole('button', {name:'Refresh data'}));
    await screen.findByText('Evidence unavailable · check services');
    expect(screen.getAllByText('Access denied — previous records cleared')).toHaveLength(2);
    expect(screen.getByText('No source retrieved')).toBeInTheDocument();
    expect(screen.getByRole('button', {name:'Download evidence JSON'})).toBeDisabled();
    expect(screen.getByLabelText('Execution to inspect')).toBeDisabled();
    expect(screen.queryByRole('button', {name:/Inspect decision for execution/})).not.toBeInTheDocument();
    expect(screen.queryByText('RESTRICTED AUDIT MARKER')).not.toBeInTheDocument();
  });

  it('logs out immediately on401 even while another source is unresolved', async () => {
    sessionStorage.setItem('pqcToken','expired.test.token');
    const slow = deferred();
    fetch.mockResolvedValueOnce(response({},401)).mockReturnValueOnce(slow.promise);
    render(<App/>);
    await screen.findByRole('button', {name:'Sign in securely'});
    expect(sessionStorage.getItem('pqcToken')).toBeNull();
    expect(fetch.mock.calls[1][1].signal.aborted).toBe(true);
    await act(async () => slow.resolve(response([run])));
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('cancels logout requests and ignores late old-session401s after a new sign-in', async () => {
    sessionStorage.setItem('pqcToken','old.test.token');
    const first = deferred(), second = deferred();
    fetch.mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise)
      .mockResolvedValueOnce(response({token:'new.test.token'}))
      .mockResolvedValueOnce(response([])).mockResolvedValueOnce(response([]));
    const user = userEvent.setup();
    render(<App/>);
    await user.click(screen.getByRole('button', {name:'Sign out'}));
    expect(fetch.mock.calls[0][1].signal.aborted).toBe(true);
    expect(fetch.mock.calls[1][1].signal.aborted).toBe(true);
    await user.type(screen.getByLabelText('Username'),'next-user');
    await user.type(screen.getByLabelText('Password'),'test-only-password');
    await user.click(screen.getByRole('button', {name:'Sign in securely'}));
    await screen.findByText('Research evidence loaded');
    // Deliberately ignore fetch cancellation to exercise application-level generation guards.
    await act(async () => {first.resolve(response({},401));second.resolve(response([run]));});
    expect(sessionStorage.getItem('pqcToken')).toBe('new.test.token');
    expect(screen.getByText('Adaptive security overview')).toBeInTheDocument();
    expect(screen.queryByRole('button', {name:'Inspect decision for execution restricted-x1'})).not.toBeInTheDocument();
  });

  it('does not persist a late sign-in response after the login screen is unmounted', async () => {
    const pending = deferred();
    fetch.mockReturnValueOnce(pending.promise);
    const user = userEvent.setup();
    const page = render(<App/>);
    await user.type(screen.getByLabelText('Username'),'test-user');
    await user.type(screen.getByLabelText('Password'),'test-only-password');
    await user.click(screen.getByRole('button', {name:'Sign in securely'}));
    page.unmount();
    expect(fetch.mock.calls[0][1].signal.aborted).toBe(true);
    await act(async () => pending.resolve(response({token:'late.test.token'})));
    expect(sessionStorage.getItem('pqcToken')).toBeNull();
  });

  it.each([{},null,{token:''},{token:42},{token:'not a token'},{token:'a.b.c\n'},{token:'a.b.'+'c'.repeat(8192)}])(
    'rejects malformed sign-in response %# without storing a session', async body => {
      fetch.mockResolvedValueOnce(response(body));
      const user = userEvent.setup();
      render(<App/>);
      await user.type(screen.getByLabelText('Username'),'test-user');
      await user.type(screen.getByLabelText('Password'),'test-only-password');
      await user.click(screen.getByRole('button', {name:'Sign in securely'}));
      expect(await screen.findByRole('alert')).toHaveTextContent('Sign-in response did not contain a valid session token');
      expect(sessionStorage.getItem('pqcToken')).toBeNull();
      expect(fetch).toHaveBeenCalledTimes(1);
      expect(screen.getByRole('button', {name:'Sign in securely'})).toBeEnabled();
    });
});
