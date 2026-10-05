import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { MethodDefinition } from '../api/types';
import { I18nProvider } from '../i18n';
import { ProjectWorkspace } from './ProjectWorkspace';

const referenceOnlyMethod: MethodDefinition = {
  method_id: 'two_lane_segment',
  family: 'highways',
  name_key: 'method.two_lane_segment.name',
  description_key: 'method.two_lane_segment.description',
  method_identifier: 'hcm7_two_lane_highway_segment',
  engine_method_identifier: 'hcm7_two_lane_highway_segment',
  method_version: 'hcm7.0',
  input_contract: 'phase_5_product_integration',
  project_type: 'manual_single_segment',
  hcm_edition: 'HCM 7.0',
  hcm_chapter: '15',
  chapter_reference: 'HCM 7th Edition Chapter 15',
  supported_unit_systems: ['metric', 'imperial'],
  availability: 'qualified_bounded',
  engineering_available: true,
  capabilities: [],
  scope_summary_keys: [],
  legacy_workflow: 'manual_single_segment',
};

const migratedReferenceOnlyProject: Record<string, unknown> = {
  project_id: 'project_reference_only',
  project_name: 'Migrated study',
  schema_version: '2.0',
  updated_at: '2026-01-01T00:00:00+00:00',
  analyses: [
    {
      analysis_id: 'analysis_reference_only',
      analysis_name: 'Migrated legacy Base',
      method_id: 'two_lane_segment',
      method_identifier: 'hcm7_two_lane_highway_segment',
      input_contract: 'phase_5_product_integration',
      scenarios: [
        {
          scenario_id: 'scenario_reference_only',
          scenario_name: 'Migrated legacy Base',
          kind: 'base',
          result_status: 'not_calculated',
          calculation_fingerprint: 'fingerprint-reference-only',
          unit_system: 'metric',
          template_id: 'legacy_import',
          displayed_inputs: {},
          result: null,
        },
      ],
    },
  ],
};

const chapter18Method: MethodDefinition = {
  ...referenceOnlyMethod,
  method_id: 'urban_street_segment',
  family: 'urban_streets',
  name_key: 'method.urban_street_segment.name',
  description_key: 'method.urban_street_segment.description',
  method_identifier: 'hcm7_urban_street_segment',
  engine_method_identifier: 'urban_street_segment_ch18_v0_1',
  input_contract: 'hcm7_ch18_bounded_signalized_15min_rht_reference_v1',
  project_type: 'manual_urban_street_segment_v1',
  hcm_chapter: '18',
  chapter_reference: 'HCM 7.0 Chapter 18; Chapter 30 Example Problem 1',
};

const chapter18ComparisonProject: Record<string, unknown> = {
  project_id: 'project_chapter18',
  project_name: 'Chapter 18 study',
  schema_version: '2.0',
  updated_at: '2026-01-01T00:00:00+00:00',
  analyses: [{
    analysis_id: 'analysis_chapter18',
    analysis_name: 'Urban street',
    method_id: 'urban_street_segment',
    method_identifier: 'hcm7_urban_street_segment',
    input_contract: 'hcm7_ch18_bounded_signalized_15min_rht_reference_v1',
    scenarios: ['a', 'b'].map((suffix) => ({
      scenario_id: `scenario_${suffix}`,
      scenario_name: `Scenario ${suffix.toUpperCase()}`,
      kind: suffix === 'a' ? 'base' : 'duplicate',
      result_status: 'current',
      calculation_fingerprint: `fingerprint_${suffix}`,
      unit_system: 'imperial',
      template_id: 'USS-CH30-EP1',
      displayed_inputs: {},
      result: { engine_result: { outputs: { level_of_service: 'C' } } },
    })),
  }],
};

afterEach(() => vi.unstubAllGlobals());

describe('ProjectWorkspace method actionability', () => {
  it('keeps migrated delivered methods actionable for Calculate and Edit', () => {
    render(
      <I18nProvider>
        <ProjectWorkspace
          project={migratedReferenceOnlyProject}
          methods={[referenceOnlyMethod]}
          onProjectChange={() => undefined}
          onNewAnalysis={() => undefined}
          onEditScenario={() => undefined}
        />
      </I18nProvider>,
    );

    expect(screen.getAllByText('Migrated legacy Base')).toHaveLength(2);
    expect(screen.queryByText('Reference-only method')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Calculate scenario' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Edit scenario' })).toBeEnabled();
    expect(screen.getByRole('button', { name: 'Duplicate scenario' })).not.toBeDisabled();
  });
});

describe('ProjectWorkspace Chapter 18 comparison vocabulary', () => {
  it('renders canonical Chapter 18 metric labels and units returned by the generic comparison API', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        comparison: {
          los_grade_transition: { from: 'C', to: 'C', changed: false },
          recalculated: false,
          numeric_deltas: [
            { key: 'travel_speed_mph', left: 23, right: 24, delta: 1 },
            { key: 'running_speed_mph', left: 36, right: 37, delta: 1 },
            { key: 'through_v_c', left: 0.52, right: 0.53, delta: 0.01 },
            { key: 'running_time_s', left: 33, right: 32, delta: -1 },
            { key: 'total_travel_time_s', left: 51, right: 50, delta: -1 },
          ],
        },
      }),
    }));
    render(
      <I18nProvider>
        <ProjectWorkspace
          project={chapter18ComparisonProject}
          methods={[chapter18Method]}
          onProjectChange={() => undefined}
          onNewAnalysis={() => undefined}
          onEditScenario={() => undefined}
        />
      </I18nProvider>,
    );

    fireEvent.change(screen.getByLabelText('Left scenario'), { target: { value: 'scenario_a' } });
    fireEvent.change(screen.getByLabelText('Right scenario'), { target: { value: 'scenario_b' } });
    fireEvent.click(screen.getByRole('button', { name: 'Compare' }));

    const result = await screen.findByTestId('comparison-result');
    await waitFor(() => expect(result.querySelectorAll('tbody tr')).toHaveLength(5));
    expect(result).toHaveTextContent('C → C');
    expect(result).toHaveTextContent('Travel speed');
    expect(result).toHaveTextContent('Running speed');
    expect(result).toHaveTextContent('Through v/c');
    expect(result).toHaveTextContent('Running time');
    expect(result).toHaveTextContent('Total travel time');
    expect(result).toHaveTextContent('mi/h');
    expect(result).toHaveTextContent('ratio');
    expect(result).toHaveTextContent('s');
  });
});
