import type { MethodDefinition } from '../api/types';

export type FrontendModuleStatus = 'delivered' | 'not_delivered';

export interface FrontendModuleDefinition {
  methodId: string;
  status: FrontendModuleStatus;
  moduleContract: string | null;
  route: string | null;
}

export type FrontendModuleRegistry = Readonly<Record<string, FrontendModuleDefinition>>;
export type MethodActionabilityStatus =
  | 'actionable'
  | 'engineering_unavailable'
  | 'not_delivered'
  | 'contract_mismatch';

/**
 * R1 deliberately registers migration status for every current method while
 * delivering no calculation workflow.  R2 modules become actionable only
 * after their own contract/browser gate is accepted.
 */
export const frontendModuleRegistry: FrontendModuleRegistry = {
  two_lane_segment: { methodId: 'two_lane_segment', status: 'not_delivered', moduleContract: null, route: null },
  two_lane_facility: { methodId: 'two_lane_facility', status: 'not_delivered', moduleContract: null, route: null },
  multilane_segment: { methodId: 'multilane_segment', status: 'not_delivered', moduleContract: null, route: null },
  basic_freeway_segment: { methodId: 'basic_freeway_segment', status: 'not_delivered', moduleContract: null, route: null },
  weaving_segment: { methodId: 'weaving_segment', status: 'not_delivered', moduleContract: null, route: null },
  merge_segment: { methodId: 'merge_segment', status: 'not_delivered', moduleContract: null, route: null },
  diverge_segment: { methodId: 'diverge_segment', status: 'not_delivered', moduleContract: null, route: null },
};

export function getFrontendModule(
  methodId: string,
  registry: FrontendModuleRegistry = frontendModuleRegistry,
): FrontendModuleDefinition | undefined {
  return registry[methodId];
}

export function isEngineSupported(method: MethodDefinition): boolean {
  return method.engineering_available;
}

export function isFrontendModuleDelivered(module: FrontendModuleDefinition | undefined): boolean {
  return module?.status === 'delivered';
}

export function isFrontendModuleContractCompatible(
  method: MethodDefinition,
  module: FrontendModuleDefinition | undefined,
): boolean {
  return Boolean(
    module?.methodId === method.method_id
      && module.moduleContract
      && module.moduleContract === method.input_contract,
  );
}

/**
 * The single normal-user actionability predicate for the rebuilt frontend.
 * Engine support, module delivery, and contract compatibility are separate
 * checks so a delivered module can never mask a contract mismatch.
 */
export function isMethodActionable(
  method: MethodDefinition,
  module: FrontendModuleDefinition | undefined = getFrontendModule(method.method_id),
): boolean {
  return isEngineSupported(method)
    && isFrontendModuleDelivered(module)
    && module?.methodId === method.method_id
    && isFrontendModuleContractCompatible(method, module);
}

export function isMethodRouteEligible(
  method: MethodDefinition,
  module: FrontendModuleDefinition | undefined = getFrontendModule(method.method_id),
): boolean {
  return isMethodActionable(method, module);
}

export function getMethodActionabilityStatus(
  method: MethodDefinition,
  module: FrontendModuleDefinition | undefined = getFrontendModule(method.method_id),
): MethodActionabilityStatus {
  if (isMethodActionable(method, module)) return 'actionable';
  if (!isEngineSupported(method)) return 'engineering_unavailable';
  if (!isFrontendModuleDelivered(module) || module?.methodId !== method.method_id) return 'not_delivered';
  return 'contract_mismatch';
}

export function getActionableMethods(
  methods: MethodDefinition[],
  registry: FrontendModuleRegistry = frontendModuleRegistry,
): MethodDefinition[] {
  return methods.filter((method) => isMethodActionable(method, getFrontendModule(method.method_id, registry)));
}
