import React from 'react';
import {render, screen, within, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, expect, it, vi} from 'vitest';
import {OperationalAlerts, validOperationalSnapshot} from './OperationalAlerts.jsx';

const snapshot = {source:'Prometheus', retrievedAt:'2026-10-20T12:00:00Z', alerts:[{
  name:'AuditOutboxDeadEvents', state:'firing', application:'auth-service', instance:'auth-service:8081',
  severity:'critical', summary:'Audit events require recovery', description:'Inspect receiver availability.', activeAt:'2026-10-20T11:59:00Z'
}]};
const outbox = {pending:1, dead:1, delivered:3, oldestPendingEventAgeSeconds:200,
  recentDead:[{eventId:'00000000-0000-4000-8000-000000000001',status:'DEAD',attempts:20,lastErrorCode:'DELIVERY_UNAVAILABLE'}]};
const response = (body, status=200) => Promise.resolve({ok:status>=200 && status<300,status,json:async()=>body});
const batch = () => fetch.mockReturnValueOnce(response(snapshot)).mockReturnValueOnce(response(outbox)).mockReturnValueOnce(response({...outbox,dead:0,recentDead:[]}));
beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
afterEach(() => vi.unstubAllGlobals());

it.each(['AdaptiveAuditWriteFailure','AdaptiveAuditMetricUnavailable'])('displays the reviewed audit-persistence alert %s', async name => {
  fetch.mockReturnValueOnce(response({...snapshot,alerts:[{...snapshot.alerts[0],name,
    application:'business-service',instance:'business-service:8082',summary:'Audit persistence requires review'}]}))
    .mockReturnValue(response(outbox));
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
  expect(await screen.findByText('Audit persistence requires review')).toBeInTheDocument();
  expect(screen.getByText('firing')).toBeInTheDocument();
  expect(validOperationalSnapshot('alerts',{...snapshot,alerts:[{...snapshot.alerts[0],name}]})).toBe(true);
});

it('does not invent alerts or fetch privileged sources before explicit loading', () => {
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  expect(fetch).not.toHaveBeenCalled();
  expect(screen.getAllByText('No saved snapshot. Current state is unknown.')).toHaveLength(3);
  expect(screen.queryByText(/No pending or firing/)).not.toBeInTheDocument();
  expect(screen.getByText(/Email requested · setup pending/)).toBeInTheDocument();
});

it('loads actual alert states separately from outbox observations and expands metadata', async () => {
  batch(); const user=userEvent.setup();
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
  expect(await screen.findByText('Audit events require recovery')).toBeInTheDocument();
  expect(screen.getByText('firing')).toBeInTheDocument();
  expect(screen.getByText('1 retained events need operator recovery.')).toBeInTheDocument();
  expect(screen.getAllByText('Retrieved snapshot')).toHaveLength(3);
  const metadata=screen.getByText('Inspect recent DEAD event metadata');
  await user.click(metadata);
  expect(metadata.closest('details')).toHaveAttribute('open');
  expect(screen.getByText(outbox.recentDead[0].eventId)).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:/send email|replay/i})).not.toBeInTheDocument();
});

it('keeps stale alert evidence but allows other sources to refresh independently', async () => {
  batch(); const user=userEvent.setup();
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
  await screen.findByText('Audit events require recovery');
  fetch.mockReturnValueOnce(response({message:'Alert source unavailable'},503)).mockReturnValue(response(outbox));
  await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
  const source=screen.getByRole('article',{name:'Prometheus alert state'});
  expect(await within(source).findByText('Stale — refresh failed')).toBeInTheDocument();
  expect(within(source).getByText('Audit events require recovery')).toBeInTheDocument();
  expect(within(source).getByText(/Retained snapshot/)).toBeInTheDocument();
  expect(screen.getAllByText('Retrieved snapshot')).toHaveLength(2);
});

it('an unavailable initial source is unknown, not an empty successful alert list', async () => {
  fetch.mockReturnValueOnce(response({message:'Unavailable'},503)).mockReturnValue(response(outbox));
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
  expect(await screen.findByText('Unavailable — state unknown')).toBeInTheDocument();
  expect(screen.queryByText(/No pending or firing/)).not.toBeInTheDocument();
});

it('clears retained privileged data when access is denied', async () => {
  batch(); const user=userEvent.setup();
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
  await screen.findByText('Audit events require recovery');
  fetch.mockReturnValue(response({message:'Administrator required'},403));
  await user.click(screen.getByRole('button',{name:'Load operational alerts'}));
  expect(await screen.findByText(/Administrator access required/)).toBeInTheDocument();
  expect(screen.queryByText('Audit events require recovery')).not.toBeInTheDocument();
});

it('clears data and logs out on an expired token', async () => {
  const logout=vi.fn(); fetch.mockReturnValue(response({message:'Expired'},401));
  render(<OperationalAlerts token="fixture" onLogout={logout}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
  await waitFor(()=>expect(logout).toHaveBeenCalledOnce());
});

it('treats invalid response shapes as unavailable and validates counts', async () => {
  fetch.mockReturnValue(response({alerts:[], pending:-1}));
  render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
  await waitFor(()=>expect(screen.getAllByText('Unavailable — state unknown')).toHaveLength(3));
  expect(validOperationalSnapshot('alerts',snapshot)).toBe(true);
  expect(validOperationalSnapshot('alerts',{...snapshot,alerts:[{...snapshot.alerts[0],state:'healthy'}]})).toBe(false);
  expect(validOperationalSnapshot('auth',{...outbox,dead:-1})).toBe(false);
});

it('aborts all pending source requests on unmount', async () => {
  fetch.mockImplementation((url, options)=>new Promise((resolve,reject)=>options.signal.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')))));
  const view=render(<OperationalAlerts token="fixture" onLogout={vi.fn()}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load operational alerts'}));
  expect(fetch).toHaveBeenCalledTimes(3);
  const signals=fetch.mock.calls.map(([,options])=>options.signal);
  view.unmount();
  expect(signals.every(signal=>signal.aborted)).toBe(true);
});
