import { describe, expect, it } from 'vitest';
import type { MethodDefinition } from '../api/types';
import {
  frontendModuleRegistry,
  getActionableMethods,
  getMethodActionabilityStatus,
  isEngineSupported,
  isFrontendModuleContractCompatible,
  isFrontendModuleDelivered,
  isMethodActionable,
  isMethodRouteEligible,
  type FrontendModuleDefinition,
} from './modules';

const method = (
  methodId: string,
  contract = 'contract',
  engineeringAvailable = true,
): MethodDefinition => ({
  method_id: methodId,
  family: 'highways',
  name_key: 'method.name',
  description_key: 'method.description',
  method_identifier: 'engine.method',
  engine_method_identifier: 'engine.method',
  method_version: 'v1',
  input_contract: contract,
  project_type: 'manual_demo_v1',
  hcm_edition: 'HCM 7.0',
  hcm_chapter: '12',
  chapter_reference: 'HCM 7.0 Chapter 12',
  supported_unit_systems: ['metric', 'imperial'],
  availability: 'qualified_bounded',
  engineering_available: engineeringAvailable,
  capabilities: [],
  scope_summary_keys: [],
  legacy_workflow: null,
});

const module = (
  status: FrontendModuleDefinition['status'],
  moduleContract: string | null,
): FrontendModuleDefinition => ({
  methodId: 'demo',
  status,
  moduleContract,
  route: status === 'delivered' ? '/demo' : null,
});

describe('frontend delivery registry', () => {
  it('registers every delivered Phase 3 method with its backend input contract', () => {
    expect(Object.keys(frontendModuleRegistry)).toHaveLength(7);
    expect(frontendModuleRegistry.two_lane_segment).toMatchObject({ status: 'delivered', moduleContract: 'phase_5_product_integration' });
    expect(frontendModuleRegistry.multilane_segment).toMatchObject({ status: 'delivered', moduleContract: 'phase_8' });
    expect(frontendModuleRegistry.two_lane_facility).toMatchObject({ status: 'delivered', moduleContract: 'phase_5_product_integration' });
    expect(frontendModuleRegistry.basic_freeway_segment).toMatchObject({ status: 'delivered', moduleContract: 'phase_10_product_integration' });
    expect(frontendModuleRegistry.weaving_segment).toMatchObject({ status: 'delivered', moduleContract: 'hcm_7_0_weaving_segment_operational_v1' });
    expect(frontendModuleRegistry.merge_segment).toMatchObject({ status: 'delivered', moduleContract: 'hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational' });
    expect(frontendModuleRegistry.diverge_segment).toMatchObject({ status: 'delivered', moduleContract: 'hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational' });
    expect(Object.values(frontendModuleRegistry).filter((entry) => entry.status === 'not_delivered')).toHaveLength(0);
  });

  it('uses one three-way predicate for actionability and route eligibility', () => {
    const available = method('demo', 'contract');
    const deliveredMatching = module('delivered', 'contract');
    const deliveredMismatch = module('delivered', 'other-contract');
    const notDelivered = module('not_delivered', 'contract');
    const unavailable = method('demo', 'contract', false);

    expect(isEngineSupported(available)).toBe(true);
    expect(isFrontendModuleDelivered(deliveredMatching)).toBe(true);
    expect(isFrontendModuleContractCompatible(available, deliveredMatching)).toBe(true);
    expect(isMethodActionable(available, deliveredMatching)).toBe(true);
    expect(isMethodRouteEligible(available, deliveredMatching)).toBe(true);
    expect(getActionableMethods([available], { demo: deliveredMatching })).toEqual([available]);

    expect(isMethodActionable(available, deliveredMismatch)).toBe(false);
    expect(getMethodActionabilityStatus(available, deliveredMismatch)).toBe('contract_mismatch');
    expect(getActionableMethods([available], { demo: deliveredMismatch })).toEqual([]);

    expect(isMethodActionable(available, notDelivered)).toBe(false);
    expect(getMethodActionabilityStatus(available, notDelivered)).toBe('not_delivered');
    expect(getActionableMethods([available], { demo: notDelivered })).toEqual([]);

    expect(isMethodActionable(unavailable, deliveredMatching)).toBe(false);
    expect(getMethodActionabilityStatus(unavailable, deliveredMatching)).toBe('engineering_unavailable');
    expect(getActionableMethods([unavailable], { demo: deliveredMatching })).toEqual([]);
  });

  it('does not treat a missing or undelivered module as contract-compatible actionability', () => {
    const definition = method('demo', 'contract');
    expect(isFrontendModuleContractCompatible(definition, undefined)).toBe(false);
    expect(getActionableMethods([definition])).toEqual([]);
  });
});
