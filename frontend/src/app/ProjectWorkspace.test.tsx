import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
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

describe('ProjectWorkspace method actionability', () => {
  it('keeps migrated reference-only methods viewable while disabling Calculate and Edit', () => {
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
    expect(screen.getByText('Reference-only method')).toBeInTheDocument();
    expect(screen.getByText(/Existing results and project data remain viewable/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Calculate scenario' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Edit scenario' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Duplicate scenario' })).not.toBeDisabled();
  });
});
