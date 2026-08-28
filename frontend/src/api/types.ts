import type { components } from './openapi';

export type Locale = 'en' | 'th';
export type UnitSystem = 'metric' | 'imperial';

export type HealthResponse = components['schemas']['HealthResponse'];
export type MethodDefinition = components['schemas']['MethodDefinitionResponse'];
export type MethodsResponse = components['schemas']['MethodsResponse'];
export type ApiErrorResponse = components['schemas']['ApiErrorResponse'];

export type DisplayedInputs = Record<string, unknown>;

export interface ValidationIssue {
  code: string;
  field: string | null;
  message: string;
  message_key: string;
}

export interface WorkflowTemplate {
  template_id: string;
  label: string;
  description?: string;
  validation_status?: string;
  starter_kind?: 'example' | 'blank' | 'custom_starter' | 'facility_template' | 'legacy_import' | string;
}

export interface WorkflowField {
  key: string;
  kind: string;
  label_key: string;
  required?: boolean;
  required_if?: Record<string, string>;
  editable?: boolean;
  conditional?: string;
  unit?: string;
  unit_metric?: string;
  unit_imperial?: string;
  options?: string[];
}

export interface WorkflowGroup {
  key: string;
  label_key: string;
  field_keys: string[];
}

export interface WorkflowTemplatesResponse {
  method_id: string;
  unit_systems: UnitSystem[];
  templates: WorkflowTemplate[];
  fields: WorkflowField[];
  groups?: WorkflowGroup[];
  branches?: Record<string, unknown>;
  scope_notes: string[];
  default_template_id?: string;
}

export interface WorkflowStartingValuesResponse {
  method_id: string;
  template_id: string;
  template_label: string;
  template_description?: string;
  validation_status?: string;
  starter_kind?: 'example' | 'blank' | 'custom_starter' | 'facility_template' | 'legacy_import' | string;
  unit_system: UnitSystem;
  displayed_inputs?: DisplayedInputs;
  segments?: FacilityRow[];
  fields: WorkflowField[];
  editable_fields?: string[];
  [key: string]: unknown;
}

export interface FacilityRow {
  segment_id: number;
  segment_name: string;
  segment_type: string;
  segment_length: number;
  posted_speed: number;
  analysis_direction_volume_veh_h: number;
  opposing_direction_volume_veh_h: number | null;
  peak_hour_factor: number;
  heavy_vehicle_percent: number;
  terrain_type: string;
  grade_percent: number;
  horizontal_alignment: string;
  lane_width: number;
  shoulder_width: number;
  access_point_density: number;
  horizontal_alignment_subsegments: unknown[];
  passing_lane_role: string;
  passing_lane: boolean;
  downstream_affected: boolean;
  [key: string]: unknown;
}

export interface CalculationState {
  presentation_state: string;
  calculation_fingerprint?: string | null;
  has_result: boolean;
  warnings: string[];
}

export interface WorkflowValidationResponse {
  method_id: string;
  template_id: string;
  unit_system: UnitSystem;
  valid: boolean;
  ready: boolean;
  validation_status: string;
  errors: ValidationIssue[];
  displayed_inputs: DisplayedInputs;
  normalized_inputs: DisplayedInputs | null;
  calculation_fingerprint?: string | null;
  input_snapshot_fingerprint?: string | null;
  method_identifier?: string | null;
  engine_method_identifier?: string | null;
  method_version?: string | null;
  input_contract?: string | null;
  project_type?: string | null;
  calculation_state: CalculationState;
}

export interface ResultMetric {
  key: string;
  value: number | null;
  unit: string | null;
  available: boolean;
  availability: 'calculated' | 'not_calculated' | 'not_predicted' | 'not_applicable';
  source?: string | null;
}

export interface WorkflowCalculationResponse {
  method_id: string;
  template_id: string;
  unit_system: UnitSystem;
  displayed_inputs: DisplayedInputs;
  normalized_inputs: DisplayedInputs;
  calculation_fingerprint: string;
  input_snapshot_fingerprint: string;
  method_identifier: string;
  engine_method_identifier: string;
  method_version: string;
  input_contract: string;
  project_type: string;
  calculation_state: CalculationState;
  result: {
    method: string;
    outputs: Record<string, unknown>;
    intermediate_values: Array<Record<string, unknown>>;
    assumptions: string[];
    warnings: string[];
    [key: string]: unknown;
  };
  presentation: {
    answer: { key: string; value: string | null; available: boolean; source?: string };
    metrics: ResultMetric[];
    capacity: Record<string, unknown>;
    warning?: string | null;
    handoff?: { reason?: string | null; scope_status?: string | null };
    interpretations: Array<Record<string, unknown>>;
    evidence: Record<string, unknown>;
    [key: string]: unknown;
  };
  audit: Record<string, unknown>;
  method: Record<string, unknown>;
  generated_at: string;
}

export interface WorkflowExportResponse {
  export_format: 'csv' | 'xlsx' | 'markdown' | 'json';
  filename: string;
  content: string | null;
  content_base64: string | null;
  media_type: string;
  calculation_fingerprint: string;
  recalculated: false;
}

export interface WorkflowExportRequest {
  template_id: string;
  unit_system: UnitSystem;
  displayed_inputs: DisplayedInputs;
  calculation_fingerprint: string;
  input_snapshot_fingerprint: string;
  result: Record<string, unknown>;
  export_format: 'csv' | 'xlsx' | 'markdown' | 'json';
}

export interface ProjectResponse {
  project: Record<string, unknown>;
  migrated: boolean;
}

export interface ProjectCompareResponse {
  comparison: Record<string, unknown>;
}
