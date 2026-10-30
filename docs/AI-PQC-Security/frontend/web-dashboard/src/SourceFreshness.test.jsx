import React from 'react';
import {render, screen, within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, expect, it, vi} from 'vitest';
import {App} from './main.jsx';
import {initialFreshness, nextFreshness} from './SourceFreshness.jsx';

const response = (body, status=200) => Promise.resolve({ok:status===200, status, json:async () => body});
afterEach(() => vi.unstubAllGlobals());

it('retains successful retrieval time on failure and replaces it only on recovery', () => {
  const initial = initialFreshness().events;
  const unavailable = nextFreshness(initial, false, '2026-10-20T10:00:00Z');
  expect(unavailable.status).toBe('unavailable');
  expect(unavailable.lastSuccessAt).toBeNull();
  const success = nextFreshness(unavailable, true, '2026-10-20T10:01:00Z');
  const failed = nextFreshness(success, false, '2026-10-20T10:02:00Z');
  expect(failed).toEqual({status:'stale', lastSuccessAt:success.lastSuccessAt, lastAttemptAt:'2026-10-20T10:02:00Z'});
  expect(nextFreshness(failed, true, '2026-10-20T10:03:00Z').status).toBe('current');
});

it('marks retained records stale after a partial refresh, then recovers', async () => {
  sessionStorage.setItem('pqcToken', 'test-only');
  const fetchMock = vi.fn()
    .mockReturnValueOnce(response([{eventId:'one', eventType:'LOGIN_SUCCEEDED', outcome:'SUCCESS', sourceService:'auth-service'}]))
    .mockReturnValueOnce(response([]))
    .mockReturnValueOnce(response({message:'offline'}, 503))
    .mockReturnValueOnce(response([]))
    .mockReturnValueOnce(response([]))
    .mockReturnValueOnce(response([]));
  vi.stubGlobal('fetch', fetchMock);
  const user = userEvent.setup();
  render(<App/>);
  await screen.findByText('Research evidence loaded');
  const freshness = within(screen.getByRole('region', {name:'Evidence source freshness'}));
  expect(freshness.getAllByText('Retrieved')).toHaveLength(2);
  await user.click(screen.getByRole('button', {name:'Refresh data'}));
  await freshness.findByText('Stale — last refresh failed');
  expect(screen.getByText('LOGIN SUCCEEDED')).toBeInTheDocument();
  expect(freshness.getAllByText('Retrieved')).toHaveLength(1);
  await user.click(screen.getByRole('button', {name:'Refresh data'}));
  await screen.findByText('Research evidence loaded');
  expect(freshness.queryByText('Stale — last refresh failed')).not.toBeInTheDocument();
  expect(screen.queryByText('LOGIN SUCCEEDED')).not.toBeInTheDocument();
});

it('distinguishes initial complete failure from empty retrieved data', async () => {
  sessionStorage.setItem('pqcToken', 'test-only');
  vi.stubGlobal('fetch', vi.fn().mockReturnValue(response({message:'offline'}, 503)));
  render(<App/>);
  await screen.findByText('Evidence unavailable · check services');
  expect(screen.getAllByText('Unavailable — no saved snapshot')).toHaveLength(2);
  expect(screen.getByText('No source retrieved')).toBeInTheDocument();
  expect(screen.getByRole('button', {name:'Download evidence JSON'})).toBeDisabled();
});

it('exports stale-source provenance without a token after refresh failure', async () => {
  sessionStorage.setItem('pqcToken', 'private-test-token');
  vi.stubGlobal('fetch', vi.fn().mockReturnValueOnce(response([])).mockReturnValueOnce(response([]))
    .mockReturnValueOnce(response({message:'offline'}, 503)).mockReturnValueOnce(response([])));
  const createURL = vi.fn(() => 'blob:source-export');
  vi.stubGlobal('URL', Object.assign(class {}, {createObjectURL:createURL, revokeObjectURL:vi.fn()}));
  const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  try {
    const user = userEvent.setup();
    render(<App/>);
    await screen.findByText('Research evidence loaded');
    await user.click(screen.getByRole('button', {name:'Refresh data'}));
    await screen.findByText('Stale — last refresh failed');
    await user.click(screen.getByRole('button', {name:'Download evidence JSON'}));
    const reader = new FileReader();
    const text = await new Promise(resolve => {reader.onload = () => resolve(reader.result); reader.readAsText(createURL.mock.calls[0][0]);});
    const report = JSON.parse(text);
    expect(report.schemaVersion).toBe(2);
    expect(report.sourceFreshness.events.status).toBe('stale');
    expect(report.sourceFreshness.runs.status).toBe('current');
    expect(report.sourceFreshness.events.lastSuccessAt).toBeTruthy();
    expect(report.snapshotTimeMeaning).toContain('different ages');
    expect(text).not.toContain('private-test-token');
  } finally {anchorClick.mockRestore();}
});
