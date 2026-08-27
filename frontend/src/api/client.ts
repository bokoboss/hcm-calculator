import type { HealthResponse, MethodDefinition, MethodsResponse } from './types';

const API_ROOT = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env?.VITE_API_ROOT ?? '';

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    headers: { Accept: 'application/json' },
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/api/v1/health');
}

export async function fetchMethods(): Promise<MethodsResponse> {
  return getJson<MethodsResponse>('/api/v1/methods');
}

export async function fetchMethod(methodId: string): Promise<MethodDefinition> {
  return getJson<MethodDefinition>(`/api/v1/methods/${encodeURIComponent(methodId)}`);
}
