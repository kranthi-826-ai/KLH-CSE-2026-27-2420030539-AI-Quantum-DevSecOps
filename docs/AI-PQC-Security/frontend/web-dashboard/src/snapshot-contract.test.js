import {expect, it} from 'vitest';
import {validSnapshot} from './snapshot-contract.js';

const run = {executionId:'execution-1',decisionId:'decision-1',riskLevel:'MEDIUM',riskScore:.56,
  selectedMode:'HYBRID',algorithmProfile:'X-Wing+AES-256-GCM+ML-DSA-65',roundTripVerified:true,
  outcome:'SUCCESS',policyLatencyMillis:2,cryptoLatencyMillis:3,totalLatencyMillis:7};
const event = {eventId:'event-1',eventType:'LOGIN_SUCCEEDED',outcome:'SUCCESS',sourceService:'auth-service'};

it('accepts empty bounded snapshots and valid recorded success/failure/started states', () => {
  expect(validSnapshot('events',[])).toBe(true);
  expect(validSnapshot('runs',[])).toBe(true);
  expect(validSnapshot('events',[event])).toBe(true);
  expect(validSnapshot('runs',[run])).toBe(true);
  expect(validSnapshot('runs',[{...run,outcome:'FAILED',roundTripVerified:false}])).toBe(true);
  expect(validSnapshot('runs',[{...run,outcome:'FAILED',roundTripVerified:true}])).toBe(true);
  for (const outcome of ['FAILED','STARTED']) expect(validSnapshot('runs',[{...run,decisionId:null,
    riskLevel:null,selectedMode:null,algorithmProfile:null,riskScore:0,outcome,roundTripVerified:false}])).toBe(true);
});

it.each([null,{},'record',42,true,[null],[[]],[false]])('rejects wrong container/record shapes: %j', value => {
  expect(validSnapshot('events',value)).toBe(false);
  expect(validSnapshot('runs',value)).toBe(false);
});

it.each([
  {riskScore:null},{riskScore:'0.56'},{riskScore:-.1},{riskScore:1.1},{riskScore:NaN},{riskScore:Infinity},
  {roundTripVerified:'false'},{roundTripVerified:1},{roundTripVerified:undefined},
  {cryptoLatencyMillis:-1},{totalLatencyMillis:'7'},{policyLatencyMillis:1.5},
  {totalLatencyMillis:1},{totalLatencyMillis:Number.MAX_SAFE_INTEGER+1},
  {riskLevel:'UNREVIEWED'},{selectedMode:{toString:null}},{selectedMode:'UNKNOWN'},
  {algorithmProfile:'wrong-profile'},{outcome:'STARTED'},
  {decisionId:null},{executionId:''},{selectionReason:{}},{errorDetail:'x'.repeat(4097)},
  {password:'must-not-export'},{token:'must-not-export'}
])('rejects invalid execution display/evidence fields: %j', change => {
  expect(validSnapshot('runs',[{...run,...change}])).toBe(false);
});

it.each([{eventId:''},{eventType:7},{sourceService:{}},{outcome:'UNKNOWN'},
  {username:{}},{detail:['not text']},{occurredAt:17},{privateKey:'must-not-export'}])(
  'rejects invalid event fields: %j', change => expect(validSnapshot('events',[{...event,...change}])).toBe(false));

it('retains explicit unknown timestamp strings for the Time unavailable renderer', () => {
  expect(validSnapshot('events',[{...event,occurredAt:'invalid'}])).toBe(true);
});

it('rejects duplicates and mixed-invalid lists instead of changing reported denominators', () => {
  expect(validSnapshot('events',[event,event])).toBe(false);
  expect(validSnapshot('runs',[run,run])).toBe(false);
  expect(validSnapshot('events',[event,null])).toBe(false);
  expect(validSnapshot('runs',[run,{...run,executionId:'other',roundTripVerified:'false'}])).toBe(false);
  const full = Array.from({length:100},(_,i)=>({...event,eventId:`event-${i}`}));
  expect(validSnapshot('events',full)).toBe(true);
  expect(validSnapshot('events',[...full,{...event,eventId:'overflow'}])).toBe(false);
  expect(validSnapshot('unknown',[event])).toBe(false);
});
