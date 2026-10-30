import React from 'react';
import {render, screen, within, fireEvent, waitFor} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import {App} from './main.jsx';

const response = value => Promise.resolve({ok:true, status:200, json:async () => value});
const executions = [{executionId:'keyboard-x1', decisionId:'d1', correlationId:'keyboard-c1',
  riskLevel:'LOW',riskScore:.2,selectedMode:'CLASSICAL',outcome:'SUCCESS',roundTripVerified:true,
  policyLatencyMillis:2, cryptoLatencyMillis:3, totalLatencyMillis:5}];

describe('Dashboard keyboard and semantic contracts', () => {
  beforeEach(() => {
    window.history.replaceState({}, '', '/');
    vi.stubGlobal('fetch', vi.fn().mockImplementation(path => response(
      path === '/api/v1/business/executions' ? executions : [{eventId:'keyboard-e1',
        eventType:'API_ACCESS_GRANTED',outcome:'SUCCESS',sourceService:'business-service',
        correlationId:'keyboard-c1',occurredAt:'invalid'}])));
  });
  afterEach(() => vi.unstubAllGlobals());

  async function dashboard() {
    sessionStorage.setItem('pqcToken', 'synthetic.keyboard.token');
    render(<App/>);
    await screen.findByText('Research evidence loaded');
  }

  it('focuses sign-in and rejects an empty form without a network request', async () => {
    const user = userEvent.setup();
    render(<App/>);
    expect(screen.getByLabelText('Username')).toHaveFocus();
    await user.tab();
    expect(screen.getByLabelText('Password')).toHaveFocus();
    await user.tab();
    await user.keyboard('{Enter}');
    expect(fetch).not.toHaveBeenCalled();
    expect(screen.getByLabelText('Username')).toBeRequired();
    expect(screen.getByLabelText('Password')).toBeRequired();
  });

  it('provides a working skip link and keyboard links to every section', async () => {
    const user = userEvent.setup();
    await dashboard();
    expect(screen.getByRole('main', {name:'Adaptive security overview'})).toHaveFocus();
    const skip = screen.getByRole('link', {name:'Skip to dashboard content'});
    skip.focus();
    await user.keyboard('{Enter}');
    expect(document.getElementById('overview')).toHaveFocus();
    const nav = screen.getByRole('navigation', {name:'Dashboard sections'});
    for (const [name,id] of [['Decision journey','decision'],['Crypto executions','executions'],
      ['Security events','events'],['Operational alerts','operations'],['Overview','overview']]) {
      const link = within(nav).getByRole('link', {name});
      link.focus();
      await user.keyboard('{Enter}');
      expect(document.getElementById(id)).toHaveFocus();
      expect(link).toHaveAttribute('aria-current','location');
      expect(window.location.hash).toBe('#' + id);
    }
  });

  it('updates section focus on browser fragment navigation', async () => {
    await dashboard();
    window.history.replaceState({}, '', '/#events');
    fireEvent(window, new HashChangeEvent('hashchange'));
    expect(document.getElementById('events')).toHaveFocus();
    expect(screen.getByRole('link', {name:'Security events'})).toHaveAttribute('aria-current','location');
  });

  it('moves focus for inspect/related actions and exposes execution column relationships', async () => {
    const user = userEvent.setup();
    await dashboard();
    const table = screen.getByRole('table', {name:'Recorded cryptographic executions'});
    expect(within(table).getAllByRole('columnheader')).toHaveLength(5);
    const rows = within(table).getAllByRole('row');
    expect(rows).toHaveLength(2);
    expect(within(rows[1]).getAllByRole('cell')).toHaveLength(5);
    const inspect = screen.getByRole('button', {name:'Inspect decision for execution keyboard-x1'});
    inspect.focus();
    await user.keyboard('{Enter}');
    expect(document.getElementById('decision')).toHaveFocus();
    const related = screen.getByRole('button', {name:'View related audit events'});
    related.focus();
    await user.keyboard('{Enter}');
    expect(document.getElementById('events')).toHaveFocus();
    expect(screen.getByRole('button', {name:'Clear related-event filter'})).toBeInTheDocument();
    expect(within(screen.getByRole('list', {name:'Recorded security events'})).getAllByRole('listitem')).toHaveLength(1);
    expect(screen.getByText('Time unavailable')).toBeInTheDocument();
    expect(screen.queryByText('Invalid Date')).not.toBeInTheDocument();
  });

  it('announces filtered counts and returns focus to sign-in after keyboard logout', async () => {
    const user = userEvent.setup();
    await dashboard();
    await user.type(screen.getByLabelText('Search executions'), 'not-present');
    expect(screen.getByRole('status', {name:'Execution result count'})).toHaveTextContent('0 of 1');
    expect(screen.getByText('Clear or broaden the search to see existing executions.')).toBeInTheDocument();
    await user.clear(screen.getByLabelText('Search executions'));
    expect(screen.getByRole('status', {name:'Execution result count'})).toHaveTextContent('1 of 1');
    screen.getByRole('button', {name:'Sign out'}).focus();
    await user.keyboard('{Enter}');
    await waitFor(() => expect(screen.getByLabelText('Username')).toHaveFocus());
    expect(sessionStorage.getItem('pqcToken')).toBeNull();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('explains how to recover an empty event filter without asking for new traffic', async () => {
    const user = userEvent.setup();
    await dashboard();
    await user.type(screen.getByLabelText('Search events'), 'not-present');
    expect(screen.getByText('No events match these filters.')).toBeInTheDocument();
    expect(screen.getByText('Clear or broaden the search, outcome or related-event filters.')).toBeInTheDocument();
    await user.clear(screen.getByLabelText('Search events'));
    expect(screen.queryByText('No events match these filters.')).not.toBeInTheDocument();
    expect(screen.getByRole('status', {name:'Event result count'})).toHaveTextContent('1 of 1');
  });
});
