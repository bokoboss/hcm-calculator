import { useEffect, useMemo, useRef, useState, type ChangeEvent, type ReactElement } from 'react';
import {
  calculateWorkflow,
  exportWorkflow,
  fetchWorkflowStartingValues,
  fetchWorkflowTemplates,
  saveAnalysisToProject,
  validateWorkflow,
} from '../api/client';
import type {
  DisplayedInputs,
  FacilityRow,
  MethodDefinition,
  UnitSystem,
  WorkflowCalculationResponse,
  WorkflowField,
  WorkflowStartingValuesResponse,
  WorkflowTemplatesResponse,
  WorkflowValidationResponse,
} from '../api/types';
import { useI18n } from '../i18n';
import {
  AnalysisHeader,
  CapacityFailurePanel,
  ChoiceGroup,
  DetailsDisclosure,
  EngineeringSection,
  ErrorSummary,
  Field,
  InputWithUnit,
  MetricCard,
  ReadinessBar,
  ResultHero,
  ScopeNotice,
  StatusBadge,
  StaleResultBanner,
} from '../components/primitives';

interface AnalysisWorkflowProps {
  method: MethodDefinition;
  onBack: () => void;
  onProjectSaved?: (project: Record<string, unknown>) => void;
  initialScenario?: ScenarioEditContext;
  onScenarioResultSaved?: (snapshot: WorkflowCalculationResponse) => Promise<void> | void;
}

export interface ScenarioEditContext {
  analysisId: string;
  scenarioId: string;
  templateId: string;
  unitSystem: UnitSystem;
  displayedInputs: DisplayedInputs;
}

function valueForInput(value: unknown): string | number {
  return value === null || value === undefined ? '' : String(value);
}

function parseInput(field: WorkflowField, value: string): unknown {
  if (!value.trim()) return null;
  if (field.kind === 'integer' || field.kind === 'number') return Number(value);
  return value;
}

function unitFor(field: WorkflowField, unitSystem: UnitSystem): string {
  return field.unit ?? (unitSystem === 'metric' ? field.unit_metric : field.unit_imperial) ?? '';
}

function isVisible(field: WorkflowField, inputs: DisplayedInputs): boolean {
  if (!field.required_if) return true;
  return Object.entries(field.required_if).every(([key, value]) => inputs[key] === value);
}

function downloadText(filename: string, content: string, mediaType: string): void {
  const blob = new Blob([content], { type: mediaType });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}

function downloadBase64(filename: string, content: string, mediaType: string): void {
  const binary = window.atob(content);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
  const blob = new Blob([bytes], { type: mediaType });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}

function serializeInputSnapshot(inputs: DisplayedInputs): string {
  return JSON.stringify(inputs);
}

function ResultPanel({
  result,
  onExport,
  onSave,
  saveLabel,
}: {
  result: WorkflowCalculationResponse;
  onExport: (format: 'csv' | 'xlsx' | 'markdown' | 'json') => void;
  onSave: () => void;
  saveLabel?: string;
}): ReactElement {
  const { t } = useI18n();
  const capacityFailure = Boolean(result.presentation.capacity.failure);
  const answer = result.presentation.answer;
  return (
    <div className="workflow-results" data-testid="workflow-results">
      <EngineeringSection title={t('result.section_title')} description={t('result.section_description')}>
        <ResultHero
          label={t('result.level_of_service')}
          value={answer.available && answer.value ? answer.value : t('result.not_calculated')}
          state={capacityFailure ? 'capacity' : 'current'}
          supporting={answer.source}
        />
        {capacityFailure ? <CapacityFailurePanel /> : null}
        <div className="metric-grid">
          {result.presentation.metrics.map((metric) => (
            <MetricCard
              key={metric.key}
              label={t(`result.metric.${metric.key}`)}
              value={metric.available && metric.value !== null ? metric.value.toFixed(1) : t('result.not_calculated')}
              unit={metric.unit ?? undefined}
            />
          ))}
        </div>
        <div className="result-actions">
          <button className="button button-secondary" type="button" onClick={() => onExport('json')}>{t('action.export_json')}</button>
          <button className="button button-secondary" type="button" onClick={() => onExport('markdown')}>{t('action.export_markdown')}</button>
          <button className="button button-secondary" type="button" onClick={() => onExport('xlsx')}>{t('action.export_xlsx')}</button>
          <button className="button button-primary" type="button" onClick={onSave}>{saveLabel ?? t('action.save_project')}</button>
        </div>
      </EngineeringSection>
      <DetailsDisclosure title={t('result.evidence_title')}>
        <div className="evidence-grid">
          <div><span className="section-label">{t('result.assumptions')}</span><ul>{result.result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><span className="section-label">{t('result.warnings')}</span><ul>{result.result.warnings.length ? result.result.warnings.map((item) => <li key={item}>{item}</li>) : <li>{t('result.no_warnings')}</li>}</ul></div>
          <div><span className="section-label">{t('result.fingerprint')}</span><code>{result.calculation_fingerprint}</code></div>
        </div>
      </DetailsDisclosure>
    </div>
  );
}

function MultilaneForm({
  templates,
  starting,
  inputs,
  unitSystem,
  onUnitSystem,
  onTemplate,
  onChange,
}: {
  templates: WorkflowTemplatesResponse;
  starting: WorkflowStartingValuesResponse;
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onUnitSystem: (unit: UnitSystem) => void;
  onTemplate: (templateId: string) => void;
  onChange: (key: string, value: unknown) => void;
}): ReactElement {
  const { t } = useI18n();
  const grouped = [
    { key: 'traffic', title: t('multilane.section_traffic'), fields: ['number_of_lanes', 'segment_length', 'demand_volume_veh_h', 'peak_hour_factor', 'heavy_vehicle_percent'] },
    { key: 'ffs', title: t('multilane.section_ffs'), fields: ['ffs_source', 'free_flow_speed', 'posted_speed_limit', 'lane_width', 'roadside_lateral_clearance', 'median_type', 'left_side_lateral_clearance', 'access_point_density'] },
    { key: 'heavy', title: t('multilane.section_heavy'), fields: ['heavy_vehicle_adjustment_method', 'terrain_type', 'grade_percent', 'truck_mix', 'passenger_car_equivalent'] },
  ];
  const fieldsByKey = new Map(starting.fields.map((field) => [field.key, field]));
  return (
    <div className="workflow-form" data-testid="multilane-form">
      <div className="workflow-controls">
        <Field id="multilane-template" label={t('workflow.template')} required>
          <select id="multilane-template" value={starting.template_id} onChange={(event) => onTemplate(event.target.value)}>
            {templates.templates.map((template) => <option value={template.template_id} key={template.template_id}>{template.label}</option>)}
          </select>
        </Field>
        <Field id="multilane-unit-system" label={t('workflow.unit_system')} required>
          <select id="multilane-unit-system" value={unitSystem} onChange={(event) => onUnitSystem(event.target.value as UnitSystem)}>
            <option value="metric">{t('locale.metric')}</option>
            <option value="imperial">{t('locale.imperial')}</option>
          </select>
        </Field>
      </div>
      {grouped.map((group) => (
        <EngineeringSection title={group.title} key={group.key}>
          <div className="form-grid">
            {group.fields.map((key) => {
              const field = fieldsByKey.get(key);
              if (!field || !isVisible(field, inputs)) return null;
              if (field.kind === 'choice') {
                return (
                  <ChoiceGroup
                    key={field.key}
                    legend={t(field.label_key)}
                    name={`multilane-${field.key}`}
                    value={String(inputs[field.key] ?? '')}
                    options={(field.options ?? []).map((option) => ({ value: option, label: t(`multilane.option.${option}`) }))}
                    onChange={(value) => onChange(field.key, value)}
                  />
                );
              }
              return (
                <Field key={field.key} id={`multilane-${field.key}`} label={t(field.label_key)} required={Boolean(field.required || field.required_if)}>
                  {(controlProps) => <InputWithUnit {...controlProps} type={field.kind === 'text' ? 'text' : 'number'} unit={unitFor(field, unitSystem)} value={valueForInput(inputs[field.key])} onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(field.key, parseInput(field, event.target.value))} />}
                </Field>
              );
            })}
          </div>
        </EngineeringSection>
      ))}
    </div>
  );
}

function FacilityForm({
  templates,
  starting,
  inputs,
  unitSystem,
  onUnitSystem,
  onTemplate,
  onChange,
}: {
  templates: WorkflowTemplatesResponse;
  starting: WorkflowStartingValuesResponse;
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onUnitSystem: (unit: UnitSystem) => void;
  onTemplate: (templateId: string) => void;
  onChange: (rows: FacilityRow[]) => void;
}): ReactElement {
  const { t } = useI18n();
  const rows = Array.isArray(inputs.rows) ? inputs.rows as FacilityRow[] : starting.segments ?? [];
  const editable = new Set(starting.editable_fields ?? []);
  const updateRow = (rowIndex: number, field: string, value: string) => {
    const fieldDefinition = starting.fields.find((candidate) => candidate.key === field);
    const next = rows.map((row, index) => {
      if (index !== rowIndex) return row;
      const parsed = fieldDefinition?.kind === 'text' ? value : parseInput(fieldDefinition ?? { key: field, kind: 'number', label_key: field }, value);
      return { ...row, [field]: parsed };
    });
    onChange(next);
  };
  const columns = ['segment_id', 'segment_name', 'segment_type', 'segment_length', 'posted_speed', 'analysis_direction_volume_veh_h', 'opposing_direction_volume_veh_h', 'peak_hour_factor', 'heavy_vehicle_percent', 'terrain_type', 'grade_percent', 'horizontal_alignment', 'lane_width', 'shoulder_width', 'access_point_density', 'passing_lane_role'];
  return (
    <div className="workflow-form" data-testid="facility-form">
      <div className="workflow-controls">
        <Field id="facility-template" label={t('workflow.template')} required>
          <select id="facility-template" value={starting.template_id} onChange={(event) => onTemplate(event.target.value)}>
            {templates.templates.map((template) => <option value={template.template_id} key={template.template_id}>{template.label}</option>)}
          </select>
        </Field>
        <Field id="facility-unit-system" label={t('workflow.unit_system')} required>
          <select id="facility-unit-system" value={unitSystem} onChange={(event) => onUnitSystem(event.target.value as UnitSystem)}>
            <option value="metric">{t('locale.metric')}</option>
            <option value="imperial">{t('locale.imperial')}</option>
          </select>
        </Field>
      </div>
      <ScopeNotice title={t('facility.template_boundary')}>{t('facility.template_boundary_supporting')}</ScopeNotice>
      <div className="table-scroll" role="region" aria-label={t('facility.table_label')} tabIndex={0}>
        <table className="facility-table">
          <thead><tr>{columns.map((column) => <th scope="col" key={column}>{t(`facility.col.${column}`)}</th>)}</tr></thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr key={row.segment_id} data-testid={`facility-row-${row.segment_id}`}>
                {columns.map((column) => {
                  const isEditable = editable.has(column) && (column !== 'opposing_direction_volume_veh_h' || row.segment_type === 'passing_zone');
                  if (column === 'opposing_direction_volume_veh_h' && row.segment_type !== 'passing_zone') {
                    return <td key={column}><span className="locked-cell" aria-label={`${t(`facility.col.${column}`)} — ${t('facility.not_applicable')}`}>—</span></td>;
                  }
                  if (column === 'segment_type' || column === 'terrain_type' || column === 'passing_lane_role' || column === 'segment_id') {
                    return <td key={column}><span className="locked-cell">{String(row[column] ?? '—')}</span></td>;
                  }
                  return (
                    <td key={column}>
                      <input
                        data-testid={`facility-input-${row.segment_id}-${column}`}
                        type={column === 'segment_name' ? 'text' : 'number'}
                        value={valueForInput(row[column])}
                        readOnly={!isEditable}
                        aria-readonly={!isEditable}
                        aria-label={`${t(`facility.col.${column}`)} ${row.segment_id}`}
                        onChange={(event) => updateRow(rowIndex, column, event.target.value)}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="table-caption">{t('facility.table_caption', { unit: unitSystem === 'metric' ? 'metric' : 'imperial' })}</p>
    </div>
  );
}

function FacilityResultPanel({
  result,
  onExport,
  onSave,
  saveLabel,
}: {
  result: WorkflowCalculationResponse;
  onExport: (format: 'csv' | 'xlsx' | 'markdown' | 'json') => void;
  onSave: () => void;
  saveLabel?: string;
}): ReactElement {
  const { t } = useI18n();
  const capacityFailure = Boolean(result.presentation.capacity.failure);
  const answer = result.presentation.answer;
  const segments = Array.isArray(result.presentation.segments) ? result.presentation.segments as Array<Record<string, unknown>> : [];
  return (
    <div className="workflow-results" data-testid="workflow-results">
      <EngineeringSection title={t('result.facility_section_title')} description={t('result.facility_section_description')}>
        <ResultHero label={t('result.facility_level_of_service')} value={answer.available && answer.value ? answer.value : t('result.not_calculated')} state={capacityFailure ? 'capacity' : 'current'} supporting={answer.source} />
        {capacityFailure ? <CapacityFailurePanel /> : null}
        <div className="metric-grid">
          {result.presentation.metrics.map((metric) => <MetricCard key={metric.key} label={t(`result.metric.${metric.key}`)} value={metric.available && metric.value !== null ? metric.value.toFixed(1) : t('result.not_calculated')} unit={metric.unit ?? undefined} />)}
        </div>
        <div className="critical-callout"><strong>{t('result.critical_segment')}</strong><span>{String(result.presentation.capacity.critical_segment_id ?? t('result.not_calculated'))}</span></div>
        <div className="table-scroll" role="region" aria-label={t('result.segment_results')} tabIndex={0}>
          <table className="result-table"><thead><tr><th>{t('facility.col.segment_id')}</th><th>{t('facility.col.segment_type')}</th><th>{t('result.segment_speed')}</th><th>{t('result.segment_density')}</th><th>{t('result.level_of_service')}</th></tr></thead><tbody>
            {segments.map((segment) => <tr key={String(segment.segment_id)}><td>{String(segment.segment_id)}</td><td>{String(segment.segment_type)}</td><td>{segment.average_speed === null || segment.average_speed === undefined ? t('result.not_calculated') : `${Number(segment.average_speed).toFixed(1)} ${String(segment.average_speed_unit)}`}</td><td>{segment.follower_density === null || segment.follower_density === undefined ? t('result.not_calculated') : `${Number(segment.follower_density).toFixed(1)} ${String(segment.follower_density_unit)}`}</td><td><StatusBadge tone={segment.level_of_service === 'F' ? 'capacity' : 'current'}>{String(segment.level_of_service ?? t('result.not_calculated'))}</StatusBadge></td></tr>)}
          </tbody></table>
        </div>
        <div className="result-actions">
          <button className="button button-secondary" type="button" onClick={() => onExport('json')}>{t('action.export_json')}</button>
          <button className="button button-secondary" type="button" onClick={() => onExport('markdown')}>{t('action.export_markdown')}</button>
          <button className="button button-secondary" type="button" onClick={() => onExport('xlsx')}>{t('action.export_xlsx')}</button>
          <button className="button button-primary" type="button" onClick={onSave}>{saveLabel ?? t('action.save_project')}</button>
        </div>
      </EngineeringSection>
      <DetailsDisclosure title={t('result.evidence_title')}>
        <div className="evidence-grid"><div><span className="section-label">{t('result.assumptions')}</span><ul>{result.result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span className="section-label">{t('result.warnings')}</span><ul>{result.result.warnings.length ? result.result.warnings.map((item) => <li key={item}>{item}</li>) : <li>{t('result.no_warnings')}</li>}</ul></div><div><span className="section-label">{t('result.fingerprint')}</span><code>{result.calculation_fingerprint}</code></div></div>
      </DetailsDisclosure>
    </div>
  );
}

export function AnalysisWorkflow({ method, onBack, onProjectSaved, initialScenario, onScenarioResultSaved }: AnalysisWorkflowProps): ReactElement {
  const { t } = useI18n();
  const [templates, setTemplates] = useState<WorkflowTemplatesResponse | null>(null);
  const [starting, setStarting] = useState<WorkflowStartingValuesResponse | null>(null);
  const [templateId, setTemplateId] = useState(initialScenario?.templateId ?? '');
  const [unitSystem, setUnitSystem] = useState<UnitSystem>(initialScenario?.unitSystem ?? 'metric');
  const [inputs, setInputs] = useState<DisplayedInputs>({});
  const [validation, setValidation] = useState<WorkflowValidationResponse | null>(null);
  const [result, setResult] = useState<WorkflowCalculationResponse | null>(null);
  const [dirty, setDirty] = useState(false);
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const initialScenarioRef = useRef(initialScenario);
  const initialScenarioAppliedRef = useRef(false);

  const isFacility = method.method_id === 'two_lane_facility';
  const serializedInputs = useMemo(() => serializeInputSnapshot(inputs), [inputs]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setTemplates(null);
    setStarting(null);
    setTemplateId('');
    setUnitSystem(initialScenario?.unitSystem ?? 'metric');
    setInputs({});
    setValidation(null);
    setResult(null);
    setDirty(false);
    initialScenarioRef.current = initialScenario;
    initialScenarioAppliedRef.current = false;
    fetchWorkflowTemplates(method.method_id)
      .then((response) => {
        if (!active) return;
        setTemplates(response);
        const preferred = initialScenarioRef.current?.templateId;
        const first = response.templates[0]?.template_id ?? '';
        setTemplateId(response.templates.some((template) => template.template_id === preferred) ? preferred ?? first : first);
      })
      .catch((reason: Error) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [method.method_id]);

  useEffect(() => {
    if (!templateId) return;
    let active = true;
    setWorking(true);
    setError(null);
    setResult(null);
    setValidation(null);
    fetchWorkflowStartingValues(method.method_id, templateId, unitSystem)
      .then((response) => {
        if (!active) return;
        setStarting(response);
        const scenario = initialScenarioRef.current;
        const canRestoreScenario = !initialScenarioAppliedRef.current
          && scenario
          && scenario.templateId === templateId
          && scenario.unitSystem === unitSystem;
        setInputs(canRestoreScenario ? scenario.displayedInputs : (isFacility ? { rows: response.segments ?? [] } : response.displayed_inputs ?? {}));
        initialScenarioAppliedRef.current = true;
        setDirty(false);
      })
      .catch((reason: Error) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setWorking(false); });
    return () => { active = false; };
  }, [method.method_id, templateId, unitSystem, isFacility]);

  useEffect(() => {
    if (!starting || !templateId || !Object.keys(inputs).length) return;
    const timer = window.setTimeout(() => {
      validateWorkflow(method.method_id, templateId, unitSystem, inputs)
        .then(setValidation)
        .catch((reason: Error) => setError(reason.message));
    }, 180);
    return () => window.clearTimeout(timer);
  }, [method.method_id, templateId, unitSystem, serializedInputs, starting, inputs]);

  const updateInputs = (next: DisplayedInputs) => {
    setInputs(next);
    setDirty(true);
    setNotice(null);
  };

  const handleCalculate = () => {
    if (!templateId || !validation?.valid) return;
    setWorking(true);
    setError(null);
    calculateWorkflow(method.method_id, templateId, unitSystem, inputs)
      .then((response) => {
        setResult(response);
        setDirty(false);
        setValidation({
          ...validation,
          valid: true,
          ready: true,
          calculation_fingerprint: response.calculation_fingerprint,
          input_snapshot_fingerprint: response.input_snapshot_fingerprint,
          calculation_state: response.calculation_state,
        });
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  const handleExport = (format: 'csv' | 'xlsx' | 'markdown' | 'json') => {
    if (!result || dirty) return;
    setWorking(true);
    exportWorkflow(method.method_id, {
      template_id: templateId,
      unit_system: unitSystem,
      displayed_inputs: inputs,
      calculation_fingerprint: result.calculation_fingerprint,
      input_snapshot_fingerprint: result.input_snapshot_fingerprint,
      result: result.result,
      export_format: format,
    })
      .then((response) => {
        if (response.content !== null) downloadText(response.filename, response.content, response.media_type);
        if (response.content_base64 !== null) downloadBase64(response.filename, response.content_base64, response.media_type);
        setNotice(t('result.exported', { filename: response.filename }));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  const handleSave = () => {
    if (!result || dirty) return;
    setWorking(true);
    if (onScenarioResultSaved) {
      Promise.resolve(onScenarioResultSaved(result))
        .catch((reason: Error) => setError(reason.message))
        .finally(() => setWorking(false));
      return;
    }
    saveAnalysisToProject(result, `${t(method.name_key)} study`)
      .then((response) => {
        onProjectSaved?.(response.project);
        downloadText(`${method.method_id}-project-v2.json`, JSON.stringify(response.project, null, 2), 'application/json');
        setNotice(t('project.saved'));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  const status = dirty ? t('state.stale_title') : result ? t('status.current') : validation?.valid ? t('status.ready_to_calculate') : t('status.items_required');
  const targetIdForIssue = (field: string | null): string | undefined => {
    if (!field) return undefined;
    const rowMatch = field.match(/^rows\[(\d+)\]\.(.+)$/);
    if (rowMatch) {
      const row = Array.isArray(inputs.rows) ? inputs.rows[Number(rowMatch[1])] as Record<string, unknown> | undefined : undefined;
      const rowId = row?.segment_id ?? Number(rowMatch[1]) + 1;
      return `facility-input-${String(rowId)}-${rowMatch[2]}`;
    }
    return isFacility ? undefined : `multilane-${field}`;
  };
  const errors = validation?.errors.map((issue) => ({ message: issue.message, targetId: targetIdForIssue(issue.field) })) ?? [];
  return (
    <div className="page-stack workflow-page" data-testid={`workflow-${method.method_id}`}>
      <div className="workflow-toolbar"><button className="button button-quiet" type="button" onClick={onBack}>← {t('action.back_to_methods')}</button><StatusBadge tone={dirty ? 'stale' : result ? 'current' : 'neutral'}>{status}</StatusBadge></div>
      <AnalysisHeader title={t(method.name_key)} method={`${method.chapter_reference} · ${method.input_contract}`} status={status} />
      {loading ? <ScopeNotice title={t('status.loading')}>{t('workflow.loading')}</ScopeNotice> : null}
      {error ? <ScopeNotice title={t('workflow.error_title')} tone="warning">{error}</ScopeNotice> : null}
      {notice ? <ScopeNotice title={t('workflow.notice_title')}>{notice}</ScopeNotice> : null}
      {templates && starting ? (isFacility ? <FacilityForm templates={templates} starting={starting} inputs={inputs} unitSystem={unitSystem} onUnitSystem={setUnitSystem} onTemplate={setTemplateId} onChange={(rows) => updateInputs({ rows })} /> : <MultilaneForm templates={templates} starting={starting} inputs={inputs} unitSystem={unitSystem} onUnitSystem={setUnitSystem} onTemplate={setTemplateId} onChange={(key, value) => updateInputs({ ...inputs, [key]: value })} />) : null}
      <ErrorSummary errors={errors} />
      {dirty && result ? <StaleResultBanner onRecalculate={handleCalculate} /> : null}
      <ReadinessBar ready={Boolean(validation?.valid) && !working} actionLabel={result && !dirty ? t('action.recalculate') : t('action.calculate')} onAction={handleCalculate} />
      {result && !dirty ? (isFacility ? <FacilityResultPanel result={result} onExport={handleExport} onSave={handleSave} saveLabel={onScenarioResultSaved ? t('action.save_scenario') : undefined} /> : <ResultPanel result={result} onExport={handleExport} onSave={handleSave} saveLabel={onScenarioResultSaved ? t('action.save_scenario') : undefined} />) : null}
      {working ? <p className="muted" role="status">{t('status.working')}</p> : null}
    </div>
  );
}
