import { fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import * as apiClient from '../api/client';
import type { MethodDefinition } from '../api/types';
import { I18nProvider, useI18n } from '../i18n';
import { App, MethodCard, ReferencePage } from './App';

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

const chapter18Method: MethodDefinition = {
  ...method,
  method_id: 'urban_street_segment',
  family: 'urban_streets',
  name_key: 'method.urban_street_segment.name',
  description_key: 'method.urban_street_segment.description',
  method_identifier: 'hcm7_urban_street_segment',
  engine_method_identifier: 'urban_street_segment_ch18_v0_1',
  input_contract: 'hcm7_ch18_bounded_signalized_15min_rht_reference_v1',
  hcm_chapter: '18',
  chapter_reference: 'HCM 7.0 Chapter 18; Chapter 30 Example Problem 1',
  scope_summary_keys: [
    'method.urban_street_segment.scope.bounded_signalized_15min',
    'method.urban_street_segment.scope.rht_reference',
  ],
};

const chapter18LhtMethod: MethodDefinition = {
  ...chapter18Method,
  method_id: 'urban_street_segment_th_lht',
  name_key: 'method.urban_street_segment_th_lht.name',
  description_key: 'method.urban_street_segment_th_lht.description',
  method_identifier: 'hcm7_urban_street_segment_th_lht',
  input_contract: 'hcm7_ch18_bounded_signalized_15min_th_lht_semantic_v1',
  project_type: 'manual_urban_street_segment_th_lht_v1',
  chapter_reference: 'HCM 7.0 Chapter 18; Chapter 30 Example Problem 1; Thailand/LHT semantic qualification',
  scope_summary_keys: [
    'method.urban_street_segment_th_lht.scope.bounded_signalized_15min',
    'method.urban_street_segment_th_lht.scope.th_lht_reference',
  ],
};

const multilaneMethod: MethodDefinition = {
  ...method,
  method_id: 'multilane_segment',
  input_contract: 'phase_8',
  engine_method_identifier: 'hcm7_multilane_los',
  legacy_workflow: 'manual_multilane_v0',
};

beforeEach(() => {
  window.localStorage.setItem('hcmcalc.locale', 'en');
  window.history.replaceState({}, '', '/');
  Object.defineProperty(HTMLElement.prototype, 'scrollTo', { configurable: true, value: () => undefined });
});
afterEach(() => vi.restoreAllMocks());

describe('direct analysis route containment', () => {
  it('replaces an ineligible Chapter 18 URL with the reference-only chooser', async () => {
    window.history.replaceState({ hcmHistoryIndex: 4, methodId: 'urban_street_segment' }, '', '/analysis/urban_street_segment');
    vi.spyOn(apiClient, 'fetchMethods').mockResolvedValue({ registry_version: 'test', methods: [chapter18Method] });

    render(<I18nProvider><App /></I18nProvider>);

    expect(await screen.findByRole('heading', { name: 'New Analysis' })).toBeVisible();
    expect(await screen.findByTestId('method-card-urban_street_segment')).toBeVisible();
    expect(window.location.pathname).toBe('/new-analysis');
    expect(screen.queryByTestId('workflow-urban_street_segment')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Calculate' })).not.toBeInTheDocument();
    expect(screen.getByTestId('method-card-urban_street_segment')).toHaveTextContent('Reference only');
  });

  it('opens the delivered Thailand/LHT direct route', async () => {
    window.history.replaceState({ hcmHistoryIndex: 4, methodId: 'urban_street_segment_th_lht' }, '', '/analysis/urban_street_segment_th_lht');
    vi.spyOn(apiClient, 'fetchMethods').mockResolvedValue({ registry_version: 'test', methods: [chapter18LhtMethod] });

    render(<I18nProvider><App /></I18nProvider>);

    expect(await screen.findByTestId('workflow-urban_street_segment_th_lht')).toBeVisible();
    expect(window.location.pathname).toBe('/analysis/urban_street_segment_th_lht');
  });

  it('enters the LHT worksheet from restored scenario-edit history', async () => {
    window.history.replaceState({
      hcmHistoryIndex: 6,
      methodId: 'urban_street_segment_th_lht',
      scenarioEdit: {
        analysisId: 'analysis-lht',
        scenarioId: 'scenario-lht',
        templateId: 'USS-TH-LHT-CH30-EP1',
        unitSystem: 'metric',
        displayedInputs: {},
      },
    }, '', '/project/analysis/analysis-lht/scenarios/scenario-lht');
    vi.spyOn(apiClient, 'fetchMethods').mockResolvedValue({ registry_version: 'test', methods: [chapter18LhtMethod] });

    render(<I18nProvider><App /></I18nProvider>);

    expect(await screen.findByTestId('workflow-urban_street_segment_th_lht')).toBeVisible();
    expect(window.location.pathname).toBe('/project/analysis/analysis-lht/scenarios/scenario-lht');
  });

  it('continues rendering a directly addressed delivered method workflow', async () => {
    window.history.replaceState({ hcmHistoryIndex: 2, methodId: 'multilane_segment' }, '', '/analysis/multilane_segment');
    vi.spyOn(apiClient, 'fetchMethods').mockResolvedValue({ registry_version: 'test', methods: [multilaneMethod] });

    render(<I18nProvider><App /></I18nProvider>);

    expect(await screen.findByTestId('workflow-multilane_segment')).toBeVisible();
    expect(window.location.pathname).toBe('/analysis/multilane_segment');
  });

  it('contains restored scenario-edit state for an undelivered method', async () => {
    window.history.replaceState({
      hcmHistoryIndex: 6,
      methodId: 'urban_street_segment',
      scenarioEdit: {
        analysisId: 'analysis-1',
        scenarioId: 'scenario-1',
        templateId: 'USS-CH30-EP1',
        unitSystem: 'metric',
        displayedInputs: {},
      },
    }, '', '/project/analysis/analysis-1/scenarios/scenario-1');
    vi.spyOn(apiClient, 'fetchMethods').mockResolvedValue({ registry_version: 'test', methods: [chapter18Method] });

    render(<I18nProvider><App /></I18nProvider>);

    expect(await screen.findByTestId('method-card-urban_street_segment')).toBeVisible();
    expect(window.location.pathname).toBe('/new-analysis');
    expect(screen.queryByTestId('workflow-urban_street_segment')).not.toBeInTheDocument();
  });
});

function LocaleButtons() {
  const { setLocale } = useI18n();
  return <><button onClick={() => setLocale('en')}>Switch to English</button><button onClick={() => setLocale('th')}>Switch to Thai</button></>;
}

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

  it('keeps Chapter 18 reference-only and hides its missing method guide action', () => {
    render(
      <I18nProvider>
        <MethodCard method={chapter18Method} onReference={() => undefined} onSelect={() => undefined} />
      </I18nProvider>,
    );

    const card = screen.getByTestId('method-card-urban_street_segment');
    expect(within(card).getByRole('button', { name: 'Start analysis' })).toBeDisabled();
    expect(within(card).queryByRole('button', { name: 'Analysis guide' })).not.toBeInTheDocument();
  });

  it('keeps method guides available for supported methods', () => {
    const supportedMethod = { ...method, method_id: 'two_lane_segment' };
    const onReference = vi.fn();
    render(
      <I18nProvider>
        <MethodCard method={supportedMethod} onReference={onReference} onSelect={() => undefined} />
      </I18nProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Analysis guide' }));
    expect(onReference).toHaveBeenCalledWith('two_lane_segment');
  });

  it('renders localized Chapter 18 reference metadata without raw keys in English and Thai', () => {
    render(
      <I18nProvider>
        <LocaleButtons />
        <MethodCard method={chapter18Method} onReference={() => undefined} onSelect={() => undefined} />
      </I18nProvider>,
    );
    const card = screen.getByTestId('method-card-urban_street_segment');

    fireEvent.click(screen.getByRole('button', { name: 'Switch to English' }));
    expect(within(card).getByText('Urban Street Segment')).toBeInTheDocument();
    expect(card.textContent).not.toContain('method.urban_street_segment.name');
    expect(card.textContent).not.toContain('method.urban_streets');
    expect(card.textContent).toContain('15-minute');
    expect(card.textContent).toContain('RHT');

    fireEvent.click(screen.getByRole('button', { name: 'Switch to Thai' }));
    expect(within(card).getByText('ช่วงถนนเขตเมือง')).toBeInTheDocument();
    expect(card.textContent).not.toContain('method.urban_street_segment.name');
    expect(card.textContent).not.toContain('method.urban_streets');
    expect(card.textContent).toContain('15 นาที');
    expect(card.textContent).toContain('RHT');
    expect(card.textContent).toContain('LHT');
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

  it.each(['urban_street_segment', 'unknown_method'])(
    'does not fall back to another guide for selected unguided method %s',
    (selectedMethodId) => {
      render(
        <I18nProvider>
          <ReferencePage
            methods={[{ ...method, method_id: 'two_lane_segment' }, chapter18Method]}
            loading={false}
            selectedMethodId={selectedMethodId}
            onReferenceSelect={() => undefined}
            onSelect={() => undefined}
          />
        </I18nProvider>,
      );

      expect(screen.queryByTestId('reference-two_lane_segment')).not.toBeInTheDocument();
      expect(screen.queryByTestId('reference-urban_street_segment')).not.toBeInTheDocument();
    },
  );
});
