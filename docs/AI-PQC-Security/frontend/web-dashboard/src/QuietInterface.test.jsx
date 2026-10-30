import React from 'react';
import {render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {App} from './main.jsx';

beforeEach(()=>vi.stubGlobal('fetch',vi.fn()));
afterEach(()=>vi.unstubAllGlobals());
const response=value=>Promise.resolve({ok:true,status:200,json:async()=>value});

it('keeps sign-in text-led without decorative icons or loading spinners',async()=>{
  let finish;
  fetch.mockReturnValue(new Promise(resolve=>{finish=resolve;}));
  const {container}=render(<App/>);
  expect(container.querySelector('svg,.brand-mark,.icon-box,.step-icon')).toBeNull();
  await userEvent.type(screen.getByLabelText('Username'),'fixture');
  await userEvent.type(screen.getByLabelText('Password'),'synthetic');
  await userEvent.click(screen.getByRole('button',{name:'Sign in securely'}));
  expect(screen.getByRole('button',{name:'Verifying…'})).toBeDisabled();
  expect(container.querySelector('svg,.spin')).toBeNull();
  // Release the pending fixture without creating an authenticated session.
  finish({ok:false,status:401,json:async()=>({message:'Synthetic fixture finished'})});
  await screen.findByRole('button',{name:'Sign in securely'});
});

it('retains charts,ordered decision steps and working navigation with no icon chrome',async()=>{
  sessionStorage.setItem('pqcToken','quiet.fixture.token');
  fetch.mockImplementation(path=>response(path==='/api/v1/events' ? [{eventId:'quiet-e',eventType:'LOGIN_SUCCEEDED',
    outcome:'SUCCESS',sourceService:'auth-service',occurredAt:'2026-10-20T12:00:00Z'}] : [{
    executionId:'quiet-x',decisionId:'d1',riskLevel:'LOW',riskScore:.2,selectedMode:'CLASSICAL',
    outcome:'SUCCESS',roundTripVerified:true,policyLatencyMillis:1,cryptoLatencyMillis:2,totalLatencyMillis:4
  }]));
  const {container}=render(<App/>);
  await screen.findByText('Research evidence loaded');
  expect(container.querySelector('svg,.brand-mark,.icon-box,.metric-icon,.step-icon,.spotlight-emblem,.event-icon')).toBeNull();
  expect(screen.getByRole('img',{name:/1 timestamped events/})).toBeInTheDocument();
  expect(screen.getAllByRole('meter')).toHaveLength(3);
  expect([...container.querySelectorAll('.step-number')].map(node=>node.textContent)).toEqual(['1','2','3','4']);
  await userEvent.click(screen.getByRole('link',{name:'Decision journey',exact:true}));
  expect(document.getElementById('decision')).toHaveFocus();
  expect(screen.getByRole('button',{name:'Download evidence JSON'})).toBeEnabled();
});
