import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { MethodDefinition } from '../api/types';
import { I18nProvider } from '../i18n';
import { MethodCard, ReferencePage } from './App';

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
  it('keeps Start analysis disabled for a delivered module with an incompatible contract', () => {
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

    expect(screen.getByRole('button', { name: 'Start analysis' })).toBeDisabled();
    expect(screen.getByText('Engineering support unavailable')).toBeInTheDocument();
  });
});


describe('ReferencePage analysis handbook', () => {
  it('renders one substantive method article instead of a stacked method directory', () => {
    const twoLaneMethod: MethodDefinition = {
      ...method,
      method_id: 'two_lane_segment',
      input_contract: 'phase_5_product_integration',
    };
    const basicFreewayMethod: MethodDefinition = {
      ...method,
      method_id: 'basic_freeway_segment',
      family: 'freeways',
      name_key: 'method.basic_freeway_segment.name',
      description_key: 'method.basic_freeway_segment.description',
      method_identifier: 'hcm7_basic_freeway_segment',
      engine_method_identifier: 'hcm7_basic_freeway_segment',
      input_contract: 'phase_10_product_integration',
      hcm_chapter: '12',
      chapter_reference: 'HCM 7th Edition Chapter 12',
    };
    const onReferenceSelect = vi.fn();

    render(
      <I18nProvider>
        <ReferencePage
          methods={[twoLaneMethod, basicFreewayMethod]}
          loading={false}
          selectedMethodId="two_lane_segment"
          onReferenceSelect={onReferenceSelect}
          onSelect={() => undefined}
        />
      </I18nProvider>,
    );

    expect(screen.getByRole('heading', { name: 'HCM Analysis Handbook' })).toBeInTheDocument();
    expect(screen.getByTestId('reference-two_lane_segment')).toBeVisible();
    expect(screen.queryByTestId('reference-basic_freeway_segment')).not.toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Key inputs and concepts' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'How the method works' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Read the results' })).toBeInTheDocument();
    expect(screen.getByText('Follower density')).toBeInTheDocument();
    expect(screen.getByText(/Convert observed directional volumes to analysis flow rates/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Basic Freeway Segment/ }));
    expect(onReferenceSelect).toHaveBeenCalledWith('basic_freeway_segment');
  });
});
