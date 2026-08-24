import type { MethodDefinition } from '../api/types';

export type FrontendModuleStatus = 'delivered' | 'not_delivered';

export interface FrontendModuleDefinition {
  methodId: string;
  status: FrontendModuleStatus;
  moduleContract: string | null;
  route: string | null;
}

/**
 * R1 deliberately registers migration status for every current method while
 * delivering no calculation workflow.  R2 modules become actionable only
 * after their own contract/browser gate is accepted.
 */
export const frontendModuleRegistry: Readonly<Record<string, FrontendModuleDefinition>> = {
  two_lane_segment: { methodId: 'two_lane_segment', status: 'not_delivered', moduleContract: null, route: null },
  two_lane_facility: { methodId: 'two_lane_facility', status: 'not_delivered', moduleContract: null, route: null },
  multilane_segment: { methodId: 'multilane_segment', status: 'not_delivered', moduleContract: null, route: null },
  basic_freeway_segment: { methodId: 'basic_freeway_segment', status: 'not_delivered', moduleContract: null, route: null },
  weaving_segment: { methodId: 'weaving_segment', status: 'not_delivered', moduleContract: null, route: null },
  merge_segment: { methodId: 'merge_segment', status: 'not_delivered', moduleContract: null, route: null },
  diverge_segment: { methodId: 'diverge_segment', status: 'not_delivered', moduleContract: null, route: null },
};

export function getFrontendModule(methodId: string): FrontendModuleDefinition | undefined {
  return frontendModuleRegistry[methodId];
}

export function isFrontendModuleContractCompatible(
  method: MethodDefinition,
  module: FrontendModuleDefinition | undefined,
): boolean {
  return Boolean(
    module &&
      module.status === 'delivered' &&
      module.moduleContract &&
      module.moduleContract === method.input_contract,
  );
}

export function getActionableMethods(methods: MethodDefinition[]): MethodDefinition[] {
  return methods.filter((method) =>
    method.engineering_available &&
    isFrontendModuleContractCompatible(method, getFrontendModule(method.method_id)),
  );
}
