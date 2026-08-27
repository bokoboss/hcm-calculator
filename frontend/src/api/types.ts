import type { components } from './openapi';

export type Locale = 'en' | 'th';
export type UnitSystem = 'metric' | 'imperial';

export type HealthResponse = components['schemas']['HealthResponse'];
export type MethodDefinition = components['schemas']['MethodDefinitionResponse'];
export type MethodsResponse = components['schemas']['MethodsResponse'];
export type ApiErrorResponse = components['schemas']['ApiErrorResponse'];
