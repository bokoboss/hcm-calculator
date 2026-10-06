import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest';
import * as api from '../api/client';
import type { MethodDefinition, WorkflowStartingValuesResponse, WorkflowTemplatesResponse } from '../api/types';
import { AppHeader } from '../components/primitives';
import { I18nProvider } from '../i18n';
import { translate } from '../i18n/catalog';
import { AnalysisWorkflow, ResultPanel, workflowOptionLabel } from './AnalysisWorkflow';
import type { WorkflowCalculationResponse } from '../api/types';
import baseline from '../../../tests/fixtures/urban_street_lht_application_baseline.json';
import { MethodCard } from './App';
import fixture from './lhtWorkflowFixture.json';

const id = 'urban_street_segment_th_lht';
const method = { method_id: id, name_key: `method.${id}.name`, description_key: `method.${id}.description`, family: 'urban_streets', engineering_available: true, input_contract: 'hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1', supported_unit_systems: ['metric', 'imperial'], scope_summary_keys: [] } as unknown as MethodDefinition;
const templates = fixture.templates as WorkflowTemplatesResponse;
const starting = fixture.starting as WorkflowStartingValuesResponse;

beforeEach(() => {
  localStorage.setItem('hcmcalc.locale', 'en');
  vi.spyOn(api, 'fetchWorkflowTemplates').mockResolvedValue(templates);
  vi.spyOn(api, 'fetchWorkflowStartingValues').mockResolvedValue(starting);
  vi.spyOn(api, 'validateWorkflow').mockImplementation(async (_id, _template, _unit, inputs) => ({ method_id: id, template_id: starting.template_id, unit_system: 'metric', valid: true, ready: true, validation_status: 'valid', errors: [], displayed_inputs: inputs, normalized_inputs: {}, calculation_state: { presentation_state: 'ready', has_result: false, warnings: [] } }));
});
afterEach(() => vi.restoreAllMocks());

async function worksheet() {
  render(<I18nProvider><AppHeader /><AnalysisWorkflow method={method} onBack={() => undefined} /></I18nProvider>);
  await screen.findByLabelText(/Segment length/);
}

describe('LHT production controls', () => {
  it('edits an ordered numeric delay list with decimal values and item units', async () => {
    await worksheet();
    const list = screen.getByRole('group', { name: /Access-point delays/ });
    expect(within(list).getAllByRole('spinbutton').length).toBeGreaterThan(0);
    expect(list).toHaveTextContent('s/veh');
    const old = within(list).getAllByRole('spinbutton').length;
    fireEvent.click(within(list).getByRole('button', { name: /Add item/ }));
    const items = within(list).getAllByRole('spinbutton');
    expect(items).toHaveLength(old + 1);
    fireEvent.change(items[old], { target: { value: '1.234567' } });
    await waitFor(() => expect(vi.mocked(api.validateWorkflow).mock.lastCall?.[3].access_point_delays_s_veh).toEqual([...(starting.displayed_inputs?.access_point_delays_s_veh as number[]), 1.234567]));
    fireEvent.click(within(list).getByRole('button', { name: `Remove item ${old + 1} — Access-point delays` }));
    expect(within(list).getAllByRole('spinbutton')).toHaveLength(old);
  });

  it('offers localized boolean choices and sends both true and false as booleans', async () => {
    await worksheet();
    const group = screen.getByRole('group', { name: 'Demand is balanced' });
    fireEvent.click(within(group).getByRole('radio', { name: 'No' }));
    await waitFor(() => expect(vi.mocked(api.validateWorkflow).mock.lastCall?.[3].demand_balanced).toBe(false));
    fireEvent.click(within(group).getByRole('radio', { name: 'Yes' }));
    await waitFor(() => expect(vi.mocked(api.validateWorkflow).mock.lastCall?.[3].demand_balanced).toBe(true));
    fireEvent.click(screen.getByRole('button', { name: 'Thai' }));
    expect(within(screen.getByRole('group', { name: 'ปรับสมดุลความต้องการเดินทางแล้ว' })).getByRole('radio', { name: 'ใช่' })).toBeChecked();
  });

  it('resolves field-aware calibration choices through the production form', async () => {
    await worksheet();
    const disclosure = screen.queryByRole('button', { name: 'Calibration' });
    if (disclosure) fireEvent.click(disclosure);
    expect(screen.getByRole('radio', { name: 'HCM reference — not locally calibrated' })).toBeVisible();
    expect(screen.getByRole('radio', { name: 'User local calibration' })).toBeVisible();
    expect(screen.getAllByRole('radio', { name: 'Signalized' })).toHaveLength(2);
  });

  it('reveals the local source conditionally and preserves hidden values', async () => {
    await worksheet();
    fireEvent.click(screen.getByRole('button', { name: 'Calibration' }));
    expect(screen.queryByLabelText(/Calibration source note/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('radio', { name: 'User local calibration' }));
    fireEvent.change(screen.getByLabelText(/Calibration source note/), { target: { value: 'Local study' } });
    fireEvent.change(screen.getByLabelText(/Calibration speed adjustment/), { target: { value: '2.5' } });
    fireEvent.click(screen.getByRole('radio', { name: 'HCM reference — not locally calibrated' }));
    expect(screen.queryByLabelText(/Calibration source note/)).not.toBeInTheDocument();
    expect(screen.getByLabelText(/Calibration speed adjustment/)).toHaveValue(2.5);
    await waitFor(() => expect(vi.mocked(api.validateWorkflow).mock.lastCall?.[3].calibration_source_note).toBe('Local study'));
    fireEvent.click(screen.getByRole('radio', { name: 'User local calibration' }));
    expect(screen.getByLabelText(/Calibration source note/)).toHaveValue('Local study');
  });

  it('localizes every Chapter 18 result metric', () => {
    for (const locale of ['en', 'th'] as const) for (const metric of ['travel_speed', 'running_speed', 'through_v_c', 'running_time', 'total_travel_time', 'free_flow_speed', 'base_free_flow_speed']) {
      const key = `result.metric.${metric}`;
      expect(translate(locale, key)).not.toBe(key);
    }
  });

  it('exposes the production Handbook from the LHT method card', () => {
    const open = vi.fn();
    render(<I18nProvider><MethodCard method={method} onSelect={() => undefined} onReference={open} /></I18nProvider>);
    fireEvent.click(screen.getByRole('button', { name: 'Analysis guide' }));
    expect(open).toHaveBeenCalledWith(id);
  });

  it('orders the result decision metrics independently of backend array order', () => {
    const result = baseline as unknown as WorkflowCalculationResponse;
    render(<I18nProvider><ResultPanel result={result} onExport={() => undefined} onSave={() => undefined} /></I18nProvider>);
    expect(Array.from(document.querySelectorAll('.metric-grid [data-slot="metric-card"] p')).map((node) => node.textContent)).toEqual(['Travel speed', 'Through v/c', 'Running speed', 'Total travel time', 'Running time']);
  });

  it('offers all four current LHT exports', () => {
    render(<I18nProvider><ResultPanel result={baseline as unknown as WorkflowCalculationResponse} onExport={() => undefined} onSave={() => undefined} /></I18nProvider>);
    fireEvent.click(screen.getByRole('button', { name: /^Export/ }));
    expect(screen.getByRole('menuitem', { name: 'Export CSV' })).toBeVisible();
  });

  it('preserves legacy method options while avoiding ramp fallback for unknown methods', () => {
    const field = { key: 'configuration', kind: 'choice', label_key: '' };
    for (const [methodId, namespace, option] of [
      ['two_lane_segment', 'two_lane_segment', 'passing_constrained'],
      ['basic_freeway_segment', 'basic_freeway', 'estimated'],
      ['weaving_segment', 'weaving', 'two_sided'],
      ['merge_segment', 'ramp', 'level'], ['diverge_segment', 'ramp', 'level'],
    ]) {
      for (const locale of ['en', 'th'] as const) expect(workflowOptionLabel(methodId, field, option, (key) => translate(locale, key))).toBe(translate(locale, `${namespace}.option.${option}`));
    }
    expect(workflowOptionLabel('unknown', field, 'custom_choice', (key) => key)).toBe('custom choice');
    expect(workflowOptionLabel(id, { ...field, key: 'calibration_status' }, 'user_local_calibration', (key) => translate('th', key))).toBe('การสอบเทียบในพื้นที่โดยผู้ใช้');
  });
});
