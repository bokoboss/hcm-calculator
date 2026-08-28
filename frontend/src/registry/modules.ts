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
 * Phase 3 registers one qualified rebuilt workflow for every delivered
 * method.  Actionability still requires the backend identity handshake.
 */
export const frontendModuleRegistry: FrontendModuleRegistry = {
  two_lane_segment: { methodId: 'two_lane_segment', status: 'delivered', moduleContract: 'phase_5_product_integration', route: '/analysis/two_lane_segment' },
  two_lane_facility: { methodId: 'two_lane_facility', status: 'delivered', moduleContract: 'phase_5_product_integration', route: '/analysis/two_lane_facility' },
  multilane_segment: { methodId: 'multilane_segment', status: 'delivered', moduleContract: 'phase_8', route: '/analysis/multilane_segment' },
  basic_freeway_segment: { methodId: 'basic_freeway_segment', status: 'delivered', moduleContract: 'phase_10_product_integration', route: '/analysis/basic_freeway_segment' },
  weaving_segment: { methodId: 'weaving_segment', status: 'delivered', moduleContract: 'hcm_7_0_weaving_segment_operational_v1', route: '/analysis/weaving_segment' },
  merge_segment: { methodId: 'merge_segment', status: 'delivered', moduleContract: 'hcm7_v70_chapter_14_isolated_right_side_one_lane_merge_operational', route: '/analysis/merge_segment' },
  diverge_segment: { methodId: 'diverge_segment', status: 'delivered', moduleContract: 'hcm7_v70_chapter_14_isolated_right_side_one_lane_diverge_operational', route: '/analysis/diverge_segment' },
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
