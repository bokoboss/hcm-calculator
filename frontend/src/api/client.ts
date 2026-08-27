import type {
  DisplayedInputs,
  HealthResponse,
  MethodDefinition,
  MethodsResponse,
  ProjectCompareResponse,
  ProjectResponse,
  UnitSystem,
  WorkflowCalculationResponse,
  WorkflowExportResponse,
  WorkflowExportRequest,
  WorkflowStartingValuesResponse,
  WorkflowTemplatesResponse,
  WorkflowValidationResponse,
} from './types';

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

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    method: 'POST',
    headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as {
      detail?: { message?: string; details?: { message?: string } };
    } | null;
    throw new Error(
      payload?.detail?.message
      ?? payload?.detail?.details?.message
      ?? `API request failed: ${response.status}`,
    );
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

export function fetchWorkflowTemplates(methodId: string): Promise<WorkflowTemplatesResponse> {
  return getJson<WorkflowTemplatesResponse>(`/api/v1/analyses/${encodeURIComponent(methodId)}/templates`);
}

export function fetchWorkflowStartingValues(
  methodId: string,
  templateId: string,
  unitSystem: UnitSystem,
): Promise<WorkflowStartingValuesResponse> {
  const query = new URLSearchParams({ template_id: templateId, unit_system: unitSystem });
  return getJson<WorkflowStartingValuesResponse>(`/api/v1/analyses/${encodeURIComponent(methodId)}/starting-values?${query.toString()}`);
}

export function validateWorkflow(
  methodId: string,
  templateId: string,
  unitSystem: UnitSystem,
  displayedInputs: DisplayedInputs,
): Promise<WorkflowValidationResponse> {
  return postJson<WorkflowValidationResponse>(`/api/v1/analyses/${encodeURIComponent(methodId)}/validate`, {
    template_id: templateId,
    unit_system: unitSystem,
    displayed_inputs: displayedInputs,
  });
}

export function calculateWorkflow(
  methodId: string,
  templateId: string,
  unitSystem: UnitSystem,
  displayedInputs: DisplayedInputs,
): Promise<WorkflowCalculationResponse> {
  return postJson<WorkflowCalculationResponse>(`/api/v1/analyses/${encodeURIComponent(methodId)}/calculate`, {
    template_id: templateId,
    unit_system: unitSystem,
    displayed_inputs: displayedInputs,
  });
}

export function exportWorkflow(
  methodId: string,
  request: WorkflowExportRequest,
): Promise<WorkflowExportResponse> {
  return postJson<WorkflowExportResponse>(`/api/v1/analyses/${encodeURIComponent(methodId)}/export`, request);
}

export function saveAnalysisToProject(
  analysisSnapshot: WorkflowCalculationResponse,
  projectName: string,
): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/from-analysis', {
    project_name: projectName,
    analysis_snapshot: analysisSnapshot,
  });
}

export function compareProjectScenarios(
  project: Record<string, unknown>,
  analysisId: string,
  leftScenarioId: string,
  rightScenarioId: string,
): Promise<ProjectCompareResponse> {
  return postJson<ProjectCompareResponse>('/api/v1/projects/compare', {
    project,
    analysis_id: analysisId,
    left_scenario_id: leftScenarioId,
    right_scenario_id: rightScenarioId,
  });
}

export function validateProject(project: Record<string, unknown>): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/validate', { project });
}

export function duplicateProjectScenario(
  project: Record<string, unknown>,
  analysisId: string,
  scenarioId: string,
  scenarioName: string,
): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/duplicate-scenario', {
    project,
    analysis_id: analysisId,
    scenario_id: scenarioId,
    scenario_name: scenarioName,
  });
}

export function renameProjectScenario(
  project: Record<string, unknown>,
  analysisId: string,
  scenarioId: string,
  scenarioName: string,
): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/rename-scenario', {
    project,
    analysis_id: analysisId,
    scenario_id: scenarioId,
    scenario_name: scenarioName,
  });
}

export function recordProjectResult(
  project: Record<string, unknown>,
  analysisId: string,
  scenarioId: string,
  snapshot: WorkflowCalculationResponse,
): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/record-result', {
    project,
    analysis_id: analysisId,
    scenario_id: scenarioId,
    analysis_snapshot: snapshot,
  });
}

export function updateProjectScenarioInputs(
  project: Record<string, unknown>,
  analysisId: string,
  scenarioId: string,
  snapshot: WorkflowCalculationResponse,
): Promise<ProjectResponse> {
  return postJson<ProjectResponse>('/api/v1/projects/update-scenario', {
    project,
    analysis_id: analysisId,
    scenario_id: scenarioId,
    analysis_snapshot: snapshot,
  });
}
