import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { WorkflowCalculationResponse } from '../api/types';
import { AppShell } from '../components/primitives';
import { I18nProvider } from '../i18n';
import { ResultPanel } from './AnalysisWorkflow';

const capacityFailureResult: WorkflowCalculationResponse = {
  method_id: 'multilane_segment',
  template_id: 'MLH-CH26-004-EB',
  unit_system: 'imperial',
  displayed_inputs: {},
  normalized_inputs: {},
  calculation_fingerprint: 'fingerprint-capacity',
  input_snapshot_fingerprint: 'snapshot-capacity',
  method_identifier: 'hcm7_multilane_los',
  engine_method_identifier: 'hcm7_multilane_los',
  method_version: 'phase_8',
  input_contract: 'phase_8',
  project_type: 'manual_multilane_v0',
  calculation_state: {
    presentation_state: 'capacity_failure',
    calculation_fingerprint: 'fingerprint-capacity',
    has_result: true,
    warnings: [],
  },
  result: {
    method: 'hcm7_multilane_los',
    outputs: {},
    intermediate_values: [],
    assumptions: ['Capacity guard is active.'],
    warnings: [],
  },
  presentation: {
    answer: { key: 'level_of_service', value: 'F', available: true, source: 'HCM capacity check' },
    metrics: [
      { key: 'density', value: null, unit: 'pc/mi/ln', available: false, availability: 'not_predicted' },
      { key: 'speed_used_for_density', value: null, unit: 'mph', available: false, availability: 'not_predicted' },
      { key: 'adjusted_free_flow_speed', value: 65.0, unit: 'mph', available: true, availability: 'calculated' },
      { key: 'demand_flow_rate', value: 4200.0, unit: 'pc/h/ln', available: true, availability: 'calculated' },
      { key: 'base_free_flow_speed', value: null, unit: 'mph', available: false, availability: 'not_calculated' },
    ],
    capacity: { failure: true },
    interpretations: [],
    evidence: {},
  },
  audit: {},
  method: {},
  generated_at: '2026-01-01T00:00:00+00:00',
};

describe('result metric availability', () => {
  it('renders not-predicted separately from not-calculated and localizes it', () => {
    render(
      <I18nProvider>
        <AppShell activePage="new-analysis" onNavigate={() => undefined} apiConnected>
          <ResultPanel result={capacityFailureResult} onExport={() => undefined} onSave={() => undefined} />
        </AppShell>
      </I18nProvider>,
    );

    expect(screen.getAllByText('Not predicted in this state')).toHaveLength(2);
    expect(screen.getByText('Demand flow rate')).toBeInTheDocument();
    expect(screen.queryByText('Not calculated')).not.toBeInTheDocument();
    expect(screen.getByText('Speed and density are not predicted in this state.')).toBeInTheDocument();
    expect(screen.queryByText('0.0')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Thai' }));

    expect(screen.getAllByText('ไม่คาดการณ์ในสถานะนี้')).toHaveLength(2);
    expect(screen.getByText('ในสถานะนี้จะไม่คาดการณ์ความเร็วและความหนาแน่น')).toBeInTheDocument();
  });
});
