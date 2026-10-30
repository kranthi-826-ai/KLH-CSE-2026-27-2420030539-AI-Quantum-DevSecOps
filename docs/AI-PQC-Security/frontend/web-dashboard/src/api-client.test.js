import {afterEach, expect, it, vi} from 'vitest';
import {api, REQUEST_TIMEOUT_MS} from './api-client.js';

afterEach(() => {vi.useRealTimers(); vi.unstubAllGlobals();});

it('aborts a stalled request and gives a recoverable error without including credentials', async () => {
  vi.useFakeTimers();
  let requestSignal;
  vi.stubGlobal('fetch', vi.fn((_, {signal}) => new Promise((_, reject) => {
    requestSignal = signal;
    signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
  })));
  const request = api('/api/v1/events', 'private-token');
  const check = expect(request).rejects.toThrow('Request timed out after 15 seconds');
  await vi.advanceTimersByTimeAsync(REQUEST_TIMEOUT_MS);
  await check;
  expect(requestSignal.aborted).toBe(true);
  expect(vi.getTimerCount()).toBe(0);
});

it('cleans up the deadline after success and preserves extra headers', async () => {
  vi.useFakeTimers();
  vi.stubGlobal('fetch', vi.fn(async () => ({ok:true, json:async () => []})));
  expect(await api('/api/v1/events', 'token', {headers:{'X-Correlation-ID':'ui-check'}})).toEqual([]);
  const headers = fetch.mock.calls[0][1].headers;
  expect(headers.get('Authorization')).toBe('Bearer token');
  expect(headers.get('X-Correlation-ID')).toBe('ui-check');
  expect(vi.getTimerCount()).toBe(0);
});

it('preserves unauthorized status so the UI can clear an expired session', async () => {
  vi.stubGlobal('fetch', vi.fn(async () => ({ok:false, status:401, json:async () => ({message:'Expired'})})));
  await expect(api('/api/v1/events', 'expired')).rejects.toMatchObject({status:401, message:'Expired'});
});

it('propagates caller cancellation without calling it a timeout', async () => {
  const caller = new AbortController();
  vi.stubGlobal('fetch', vi.fn((_, {signal}) => new Promise((_, reject) => {
    signal.addEventListener('abort', () => reject(new DOMException('Caller cancelled', 'AbortError')));
  })));
  const request = api('/api/v1/events', '', {signal:caller.signal});
  caller.abort();
  await expect(request).rejects.toMatchObject({name:'AbortError'});
});
