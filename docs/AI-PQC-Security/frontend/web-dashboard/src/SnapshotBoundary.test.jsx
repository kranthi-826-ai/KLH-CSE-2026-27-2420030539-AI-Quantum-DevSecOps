import React from 'react';
import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, expect, it, vi} from 'vitest';
import {App} from './main.jsx';

const response = data => Promise.resolve({ok:true,status:200,json:async()=>data});
beforeEach(() => {sessionStorage.setItem('pqcToken','fixture.snapshot.token');vi.stubGlobal('fetch',vi.fn());});
afterEach(() => vi.unstubAllGlobals());

it('rejects a null event record without crashing the whole dashboard', async () => {
  fetch.mockImplementation(path => response(path === '/api/v1/events' ? [null] : []));
  render(<App/>);
  expect(await screen.findByText(/Security events: Unexpected API response/)).toBeInTheDocument();
  expect(screen.getByText('Unavailable — no saved snapshot')).toBeInTheDocument();
  expect(screen.getByRole('heading',{name:'Adaptive security overview'})).toBeInTheDocument();
});

it('rejects a string verification flag instead of counting it as verified', async () => {
  fetch.mockImplementation(path => response(path === '/api/v1/business/executions' ? [{
    executionId:'bad-flag',decisionId:'d1',riskLevel:'LOW',riskScore:.2,selectedMode:'CLASSICAL',
    outcome:'SUCCESS',roundTripVerified:'false',policyLatencyMillis:1,cryptoLatencyMillis:1,totalLatencyMillis:2
  }] : []));
  render(<App/>);
  expect(await screen.findByText(/Executions: Unexpected API response/)).toBeInTheDocument();
  expect(screen.queryByText('1/1')).not.toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Inspect decision for execution bad-flag'})).not.toBeInTheDocument();
});

it('keeps the last valid snapshot stale and excludes malformed refresh records from export', async () => {
  const good={eventId:'saved-event',eventType:'LOGIN_SUCCEEDED',outcome:'SUCCESS',sourceService:'auth-service'};
  fetch.mockReturnValueOnce(response([good])).mockReturnValueOnce(response([]))
    .mockReturnValueOnce(response([good,null])).mockReturnValueOnce(response([]));
  const createURL=vi.fn(()=> 'blob:validated-snapshot');
  vi.stubGlobal('URL',Object.assign(class {},{createObjectURL:createURL,revokeObjectURL:vi.fn()}));
  const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
  try {
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await userEvent.click(screen.getByRole('button',{name:'Refresh data'}));
    expect(await screen.findByText('Stale — last refresh failed')).toBeInTheDocument();
    expect(screen.getByText('LOGIN SUCCEEDED')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button',{name:'Download evidence JSON'}));
    const reader=new FileReader();
    const text=await new Promise(resolve=>{reader.onload=()=>resolve(reader.result);reader.readAsText(createURL.mock.calls[0][0]);});
    const report=JSON.parse(text);
    expect(report.events).toEqual([good]);
    expect(report.sourceFreshness.events.status).toBe('stale');
    expect(report.sourceFreshness.events.lastSuccessAt).toBeTruthy();
  } finally {click.mockRestore();}
});

it('does not enable evidence export when both initial snapshots are invalid', async () => {
  fetch.mockReturnValue(response([null]));
  render(<App/>);
  await screen.findByText('Evidence unavailable · check services');
  expect(screen.getAllByText('Unavailable — no saved snapshot')).toHaveLength(2);
  expect(screen.getByRole('button',{name:'Download evidence JSON'})).toBeDisabled();
  expect(within(screen.getByRole('region',{name:'Snapshot metrics'})).queryByText('1/1')).not.toBeInTheDocument();
});

it('shows a post-crypto failed flow without rejecting the snapshot or claiming successful protection', async () => {
  fetch.mockImplementation(path=>response(path==='/api/v1/business/executions' ? [{
    executionId:'post-crypto-x',decisionId:'d1',riskLevel:'LOW',riskScore:.2,selectedMode:'CLASSICAL',
    outcome:'FAILED',roundTripVerified:true,policyLatencyMillis:1,cryptoLatencyMillis:2,totalLatencyMillis:4,
    errorDetail:'Adaptive security operation failed'
  }] : []));
  render(<App/>);
  await screen.findByText('Research evidence loaded');
  expect(screen.getByText('Crypto verified · flow failed')).toBeInTheDocument();
  expect(screen.getByText('CRYPTO VERIFIED · FLOW FAILED')).toBeInTheDocument();
  expect(screen.queryByText('1/1')).not.toBeInTheDocument();
  expect(screen.getByRole('meter',{name:'Classical share'})).toHaveAttribute('aria-valuenow','0');
});
