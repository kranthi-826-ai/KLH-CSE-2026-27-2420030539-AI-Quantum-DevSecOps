import React from 'react';
import {render, screen} from '@testing-library/react';
import {expect, it} from 'vitest';
import {EvidenceOverview} from './EvidenceOverview.jsx';
import {OperationalTelemetry} from './OperationalTelemetry.jsx';

it('excludes rejected and unverified selections from executed protection shares', () => {
  const runs = [
    {decisionId:'a', selectedMode:'CLASSICAL', outcome:'FAILED', roundTripVerified:false},
    {decisionId:'b', selectedMode:'PQC', outcome:'SUCCESS', roundTripVerified:true},
    {decisionId:'c', selectedMode:'HYBRID', outcome:'SUCCESS', roundTripVerified:false}
  ];
  render(<EvidenceOverview runs={runs} events={[]} loadedSources={{events:true,runs:true}}/>);
  expect(screen.getByRole('meter', {name:'Classical share'})).toHaveAttribute('aria-valuenow', '0');
  expect(screen.getByRole('meter', {name:'Hybrid share'})).toHaveAttribute('aria-valuenow', '0');
  expect(screen.getByRole('meter', {name:'Post-quantum share'})).toHaveAttribute('aria-valuenow', '100');
  expect(screen.getByText(/1 completed, verified executions. 2 other records are excluded/)).toBeInTheDocument();
});

it('shows a failed latest decision as selected but not verified protection', () => {
  render(<OperationalTelemetry runs={[{decisionId:'a', selectedMode:'CLASSICAL', riskLevel:'HIGH', outcome:'FAILED', roundTripVerified:false}]} events={[]} loadedSources={{events:true,runs:true}}/>);
  expect(screen.getByText('POLICY-SELECTED MODE')).toBeInTheDocument();
  expect(screen.getByText('Not verified as executed protection. Inspect the recorded outcome.')).toBeInTheDocument();
  expect(screen.queryByText('Execution completed and round trip verified.')).not.toBeInTheDocument();
});
