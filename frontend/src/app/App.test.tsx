import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import type { MethodDefinition } from '../api/types';
import { I18nProvider } from '../i18n';
import { MethodCard } from './App';

const method: MethodDefinition = {
  method_id: 'demo',
  family: 'highways',
  name_key: 'method.two_lane_segment.name',
  description_key: 'method.two_lane_segment.description',
  method_identifier: 'hcm7_two_lane_highway_segment',
  engine_method_identifier: 'hcm7_ch15_two_lane_motorized',
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

describe('MethodCard actionability boundary', () => {
  it('keeps Select method disabled for a delivered module with an incompatible contract', () => {
    render(
      <I18nProvider>
        <MethodCard
          method={method}
          frontendModule={{
            methodId: 'demo',
            status: 'delivered',
            moduleContract: 'different_contract',
            route: '/demo',
          }}
          onReference={() => undefined}
          onSelect={() => undefined}
        />
      </I18nProvider>,
    );

    expect(screen.getByRole('button', { name: 'Select method' })).toBeDisabled();
    expect(screen.getByText('Contract mismatch')).toBeInTheDocument();
  });
});
