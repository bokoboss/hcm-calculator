import { describe, expect, it } from 'vitest';
import type { MethodDefinition } from '../api/types';
import { frontendModuleRegistry, getActionableMethods, isFrontendModuleContractCompatible } from './modules';

const method = (methodId: string, contract = 'contract'): MethodDefinition => ({
  method_id: methodId,
  family: 'highways',
  name_key: 'method.name',
  description_key: 'method.description',
  method_identifier: 'engine.method',
  method_version: 'v1',
  input_contract: contract,
  hcm_edition: 'HCM 7.0',
  hcm_chapter: '12',
  chapter_reference: 'HCM 7.0 Chapter 12',
  supported_unit_systems: ['metric', 'imperial'],
  availability: 'qualified_bounded',
  engineering_available: true,
  capabilities: [],
  scope_summary_keys: [],
  legacy_workflow: null,
});

describe('frontend delivery registry', () => {
  it('registers migration status for all seven backend method IDs', () => {
    expect(Object.keys(frontendModuleRegistry)).toHaveLength(7);
    expect(Object.values(frontendModuleRegistry).every((entry) => entry.status === 'not_delivered')).toBe(true);
  });

  it('requires delivered status and matching input contract before actionability', () => {
    const definition = method('demo', 'contract');
    expect(isFrontendModuleContractCompatible(definition, undefined)).toBe(false);
    expect(getActionableMethods([definition])).toEqual([]);
  });
});
