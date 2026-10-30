export const REQUEST_TIMEOUT_MS = 15000;

export async function api(path, token, options = {}) {
  const controller = new AbortController();
  const externalSignal = options.signal;
  const onAbort = () => controller.abort(externalSignal.reason);
  let timedOut = false;
  if (externalSignal?.aborted) onAbort();
  else externalSignal?.addEventListener('abort', onAbort, {once:true});
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, REQUEST_TIMEOUT_MS);
  try {
    const headers = new Headers(options.headers);
    headers.set('Content-Type', 'application/json');
    if (token) headers.set('Authorization', `Bearer ${token}`);
    const response = await fetch(path, {...options, headers, signal:controller.signal});
    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      const error = new Error(typeof body?.message === 'string' ? body.message : `Request failed: ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return await response.json();
  } catch (error) {
    if (timedOut) throw new Error('Request timed out after 15 seconds. Check services and retry.');
    throw error;
  } finally {
    clearTimeout(timer);
    externalSignal?.removeEventListener('abort', onAbort);
  }
}
