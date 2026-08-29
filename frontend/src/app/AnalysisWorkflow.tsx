import { useEffect, useId, useMemo, useRef, useState, type ChangeEvent, type ReactElement } from 'react';
import { createPortal } from 'react-dom';
import {
  calculateWorkflow,
  engineeringAssetUrl,
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
  ResultMetric,
  UnitSystem,
  WorkflowCalculationResponse,
  WorkflowField,
  WorkflowGroup,
  WorkflowStartingValuesResponse,
  WorkflowTemplatesResponse,
  WorkflowValidationResponse,
} from '../api/types';
import { useI18n } from '../i18n';
import {
  ActionToast,
  AnalysisHeader,
  CapacityFailurePanel,
  ChoiceGroup,
  DetailsDisclosure,
  EngineeringSection,
  ErrorSummary,
  Field,
  InputWithUnit,
  HandoffPanel,
  MetricCard,
  ReadinessBar,
  ResultHero,
  ScopeNotice,
  StaleResultPanel,
  StatusBadge,
  WarningPanel,
} from '../components/primitives';

interface AnalysisWorkflowProps {
  method: MethodDefinition;
  onBack: () => void;
  onDirtyChange?: (dirty: boolean) => void;
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
  if (field.kind === 'boolean') return value === 'true';
  if (field.kind === 'json') {
    try {
      return JSON.parse(value) as unknown;
    } catch {
      return value;
    }
  }
  return value;
}

function valueForField(field: WorkflowField, value: unknown): string | number {
  if (field.kind === 'json') return value === null || value === undefined ? '' : JSON.stringify(value, null, 2);
  if (field.kind === 'boolean') return value === true ? 'true' : value === false ? 'false' : '';
  return valueForInput(value);
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
  anchor.style.display = 'none';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1_000);
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
  anchor.style.display = 'none';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(url), 1_000);
}

function serializeInputSnapshot(inputs: DisplayedInputs): string {
  return JSON.stringify(inputs);
}

function metricDisplayValue(metric: ResultMetric, translate: (key: string) => string): string {
  if (metric.availability === 'not_predicted') return translate('result.not_predicted');
  if (metric.availability === 'not_applicable') return translate('result.not_applicable');
  if (metric.available && metric.value !== null) return metric.value.toFixed(1);
  return translate('result.not_calculated');
}

export function ResultPanel({
  result,
  onExport,
  onSave,
  saveLabel,
  onRecalculate,
  stale = false,
  exampleResult = false,
  workingAction,
}: {
  result: WorkflowCalculationResponse;
  onExport: (format: 'csv' | 'xlsx' | 'markdown' | 'json') => void;
  onSave: () => void;
  saveLabel?: string;
  onRecalculate?: () => void;
  stale?: boolean;
  exampleResult?: boolean;
  workingAction?: 'calculate' | 'save' | 'export' | null;
}): ReactElement {
  const { t } = useI18n();
  const capacityFailure = Boolean(result.presentation.capacity.failure);
  const handoff = result.calculation_state.presentation_state === 'hcm_stopping_or_handoff'
    || Boolean(result.presentation.handoff);
  const resultWarning = result.calculation_state.presentation_state === 'valid_current_result_with_warning';
  const showWarning = resultWarning && !stale;
  const metricsUnavailable = result.presentation.metrics.some((metric) => metric.availability === 'not_predicted');
  const answer = result.presentation.answer;
  const keyMetrics = selectKeyMetrics(result.method_id, result.presentation.metrics);
  return (
    <section className="workflow-results result-inspector-surface" data-testid="workflow-results" aria-labelledby="result-inspector-title">
      <div className="result-inspector-heading">
        <div><span className="section-label">{t('result.inspector_label')}</span><h2 id="result-inspector-title" tabIndex={-1}>{t('result.section_title')}</h2></div>
        {exampleResult ? <StatusBadge tone="neutral">{t('workflow.example_result')}</StatusBadge> : null}
      </div>
        <ResultHero
          label={t('result.level_of_service')}
          value={answer.available && answer.value ? answer.value : handoff ? t('state.handoff_title') : t('result.not_calculated')}
          state={stale ? 'stale' : handoff ? 'handoff' : capacityFailure ? 'capacity' : showWarning ? 'warning' : 'current'}
          supporting={answer.source}
        />
        {stale ? <StaleResultPanel /> : handoff ? <HandoffPanel /> : capacityFailure ? <CapacityFailurePanel metricsUnavailable={metricsUnavailable} /> : showWarning ? <WarningPanel message={result.presentation.warning} /> : null}
        {handoff && result.presentation.handoff?.reason ? <p className="handoff-reason">{String(result.presentation.handoff.reason)}</p> : null}
        <div className="metric-grid">
          {keyMetrics.map((metric) => (
            <MetricCard
              key={metric.key}
              label={t(`result.metric.${metric.key}`)}
              value={metricDisplayValue(metric, t)}
              unit={metric.unit ?? undefined}
            />
          ))}
        </div>
        <div className="result-actions">
          {stale ? <button className="button button-primary" type="button" disabled={workingAction === 'calculate'} aria-busy={workingAction === 'calculate' || undefined} onClick={onRecalculate}>{workingAction === 'calculate' ? t('status.calculating') : t('action.recalculate')}</button> : <>
            <button className="button button-primary" type="button" disabled={workingAction === 'save'} aria-busy={workingAction === 'save' || undefined} onClick={onSave}>{workingAction === 'save' ? t('status.saving') : saveLabel ?? t('action.save_project')}</button>
            <ExportMenu busy={workingAction === 'export'} stale={false} onExport={onExport} />
          </>}
        </div>
    </section>
  );
}

function scopeFor(method: MethodDefinition, translate: (key: string) => string): string {
  const scopeKey = method.name_key.replace(/\.name$/, '.scope');
  const translated = translate(scopeKey);
  return translated === scopeKey ? translate(method.description_key) : translated;
}

function selectKeyMetrics(methodId: string, metrics: ResultMetric[]): ResultMetric[] {
  const preferred: Record<string, string[]> = {
    two_lane_segment: ['follower_density', 'average_speed', 'percent_followers'],
    multilane_segment: ['density', 'speed_used_for_density', 'demand_flow_rate', 'adjusted_capacity'],
    basic_freeway_segment: ['density', 'speed_used_for_density', 'demand_flow_rate', 'adjusted_capacity'],
    weaving_segment: ['density', 'mean_speed', 'capacity', 'demand'],
    merge_segment: ['density', 'ramp_influence_speed', 'governing_vc', 'governing_capacity'],
    diverge_segment: ['density', 'ramp_influence_speed', 'governing_vc', 'governing_capacity'],
    two_lane_facility: ['facility_average_speed', 'facility_density', 'facility_percent_followers'],
  };
  const selected = preferred[methodId] ?? [];
  const byKey = new Map(metrics.map((metric) => [metric.key, metric]));
  const ordered = selected.map((key) => byKey.get(key)).filter((metric): metric is ResultMetric => Boolean(metric));
  return ordered.length ? ordered.slice(0, 5) : metrics.slice(0, 4);
}

function DetailedResultSection({
  result,
  assetMetadata,
}: {
  result: WorkflowCalculationResponse;
  assetMetadata?: EngineeringAssetMetadata;
}): ReactElement {
  const { t } = useI18n();
  const keyMetrics = new Set(selectKeyMetrics(result.method_id, result.presentation.metrics).map((metric) => metric.key));
  const secondaryMetrics = result.presentation.metrics.filter((metric) => !keyMetrics.has(metric.key));
  return (
    <EngineeringSection className="result-details" title={t('result.details_title')} description={t('result.details_description')}>
      <GeometryEvidenceDiagram methodId={result.method_id} result={result} assetMetadata={assetMetadata} />
      {secondaryMetrics.length ? <DetailsDisclosure title={t('result.more_metrics')}>
        <div className="metric-grid">{secondaryMetrics.map((metric) => <MetricCard key={metric.key} label={t(`result.metric.${metric.key}`)} value={metricDisplayValue(metric, t)} unit={metric.unit ?? undefined} />)}</div>
      </DetailsDisclosure> : null}
      <DetailsDisclosure title={t('result.evidence_title')}>
        <div className="evidence-grid">
          <div><span className="section-label">{t('result.assumptions')}</span><ul>{result.result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><span className="section-label">{t('result.warnings')}</span><ul>{result.result.warnings.length ? result.result.warnings.map((item) => <li key={item}>{item}</li>) : <li>{t('result.no_warnings')}</li>}</ul></div>
          <div><span className="section-label">{t('result.fingerprint')}</span><code>{result.calculation_fingerprint}</code></div>
        </div>
      </DetailsDisclosure>
    </EngineeringSection>
  );
}

type EngineeringAssetMetadata = {
  kind?: string;
  asset_path?: string;
  variants?: Array<{
    subtype?: string;
    segment_type?: string;
    configuration?: string;
    number_of_weaving_lanes?: number;
    asset_path: string;
  }>;
};

function engineeringAssetsFrom(templates: WorkflowTemplatesResponse | null): EngineeringAssetMetadata | undefined {
  const raw = templates?.branches?.engineering_assets;
  return raw && typeof raw === 'object' ? raw as EngineeringAssetMetadata : undefined;
}

function numericValue(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function displayNumber(value: unknown, suffix = ''): string {
  const parsed = numericValue(value);
  return parsed === null ? '—' : `${parsed.toFixed(1)}${suffix}`;
}

function StarterNotice({ starting }: { starting: WorkflowStartingValuesResponse }): ReactElement | null {
  const { t } = useI18n();
  if (starting.starter_kind === 'example') {
    return <ScopeNotice title={t('workflow.example_loaded_title')}>{t('workflow.example_loaded_supporting')}</ScopeNotice>;
  }
  if (starting.starter_kind === 'blank' || starting.starter_kind === 'custom_starter') {
    return <ScopeNotice title={starting.template_label}>{t('workflow.custom_starter_note')}</ScopeNotice>;
  }
  return null;
}

function TwoLaneSchematic({
  inputs,
  unitSystem,
  assets,
}: {
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  assets?: EngineeringAssetMetadata;
}): ReactElement | null {
  const { t } = useI18n();
  const segmentType = String(inputs.segment_type ?? 'passing_constrained');
  const variant = assets?.variants?.find((item) => item.segment_type === segmentType);
  if (!variant) return null;
  const lengthUnit = unitSystem === 'metric' ? 'km' : 'mi';
  const alignment = String(inputs.horizontal_alignment ?? 'straight');
  const facts = [
    `${t('two_lane.schematic_length')}: ${displayNumber(inputs.segment_length, ` ${lengthUnit}`)}`,
    `${t('two_lane.schematic_segment_type')}: ${t(`two_lane_segment.option.${segmentType}`)}`,
    `${t('two_lane.schematic_alignment')}: ${t(`two_lane_segment.option.${alignment}`)}`,
  ];
  if (inputs.terrain_type === 'mountainous') {
    facts.push(`${t('two_lane.schematic_grade')}: ${displayNumber(inputs.grade_percent, ' %')}`);
  }
  return (
    <section className="engineering-reference two-lane-schematic" data-testid="two-lane-schematic" aria-labelledby="two-lane-schematic-title">
      <div className="engineering-reference-copy">
        <span className="section-label">{t('two_lane.schematic_title')}</span>
        <h3 id="two-lane-schematic-title">{t(`two_lane_segment.option.${segmentType}`)}</h3>
        <p>{facts.join(' · ')}</p>
      </div>
      <img src={engineeringAssetUrl(variant.asset_path)} alt={`${t('two_lane.schematic_alt')}: ${t(`two_lane_segment.option.${segmentType}`)}`} data-asset-path={variant.asset_path} />
      <p className="engineering-reference-note">{t('two_lane.schematic_caption')}</p>
    </section>
  );
}

function WeavingReference({
  inputs,
  assets,
}: {
  inputs: DisplayedInputs;
  assets?: EngineeringAssetMetadata;
}): ReactElement | null {
  const { t } = useI18n();
  const configuration = String(inputs.configuration ?? '');
  const numberOfWeavingLanes = numericValue(inputs.number_of_weaving_lanes);
  const variant = assets?.variants?.find((item) => item.configuration === configuration && item.number_of_weaving_lanes === numberOfWeavingLanes);
  const entry = String(inputs.entry_side ?? '');
  const exit = String(inputs.exit_side ?? '');
  const laneChanges = [
    ['RF', inputs.lc_rf],
    ['FR', inputs.lc_fr],
    ['RR', inputs.lc_rr],
  ].filter(([, value]) => value !== null && value !== undefined && value !== '')
    .map(([label, value]) => `${label}=${String(value)}`)
    .join(', ') || '—';
  return (
    <section className="engineering-reference weaving-reference" data-testid="weaving-reference" aria-labelledby="weaving-reference-title">
      <div className="engineering-reference-copy">
        <span className="section-label">{t('weaving.reference_title')}</span>
        <h3 id="weaving-reference-title">{configuration ? t(`weaving.option.${configuration}`) : t('weaving.reference_title')}</h3>
        {variant ? <img src={engineeringAssetUrl(variant.asset_path)} alt={`${t('weaving.reference_title')}: ${configuration ? t(`weaving.option.${configuration}`) : ''}`} data-asset-path={variant.asset_path} /> : <p className="muted">{t('weaving.reference_incomplete')}</p>}
        <dl className="weaving-reference-facts">
          <div><dt>{t('weaving.reference_nwl')}</dt><dd>N={displayNumber(inputs.number_of_lanes)} / NWL={displayNumber(inputs.number_of_weaving_lanes)}</dd></div>
          <div><dt>{t('weaving.reference_entry_exit')}</dt><dd>{entry ? t(`weaving.option.${entry}`) : '—'} / {exit ? t(`weaving.option.${exit}`) : '—'}</dd></div>
          <div><dt>{t('weaving.reference_lane_changes')}</dt><dd>{laneChanges}</dd></div>
        </dl>
      </div>
      <div className="weaving-movement-legend">
        <strong>{t('weaving.reference_legend')}</strong>
        <ul>
          <li>{t('weaving.reference_ff')}</li>
          <li>{t('weaving.reference_fr')}</li>
          <li>{t('weaving.reference_rf')}</li>
          <li>{t('weaving.reference_rr')}</li>
        </ul>
        <p className="engineering-reference-note">{t('weaving.reference_caption')} {t('weaving.reference_conceptual')}</p>
      </div>
    </section>
  );
}

function RampReference({
  methodId,
  assets,
}: {
  methodId: 'merge_segment' | 'diverge_segment';
  assets?: EngineeringAssetMetadata;
}): ReactElement | null {
  const { t } = useI18n();
  const isMerge = methodId === 'merge_segment';
  const title = isMerge ? t('workflow.geometry_merge') : t('workflow.geometry_diverge');
  const note = isMerge ? t('workflow.geometry_merge_note') : t('workflow.geometry_diverge_note');
  if (!assets?.asset_path) return null;
  return (
    <section className="engineering-reference ramp-reference" data-testid="ramp-reference" aria-labelledby={`${methodId}-reference-title`}>
      <div className="engineering-reference-copy"><span className="section-label">{t('workflow.geometry_evidence')}</span><h3 id={`${methodId}-reference-title`}>{title}</h3><p>{note}</p><p className="engineering-reference-note">{t('workflow.conceptual_reference')}</p></div>
      <img src={engineeringAssetUrl(assets.asset_path)} alt={title} data-asset-path={assets.asset_path} />
    </section>
  );
}

type CurveSubsegment = {
  type?: string;
  length?: number | null;
  superelevation_percent?: number | null;
  radius?: number | null;
  central_angle_deg?: number | null;
  horizontal_class?: number | null;
};

function CurveEditor({
  inputs,
  unitSystem,
  onChange,
}: {
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onChange: (value: CurveSubsegment[]) => void;
}): ReactElement {
  const { t } = useI18n();
  const rows = Array.isArray(inputs.horizontal_alignment_subsegments)
    ? inputs.horizontal_alignment_subsegments as CurveSubsegment[]
    : [];
  const [setup, setSetup] = useState({
    totalLength: numericValue(inputs.segment_length) === null
      ? ''
      : String((numericValue(inputs.segment_length) ?? 0) * (unitSystem === 'metric' ? 1000 : 5280)),
    radius: unitSystem === 'metric' ? '137.2' : '450',
    superelevation: '3',
    centralAngle: '55',
    horizontalClass: '3',
    count: '11',
  });
  const updateSetup = (key: keyof typeof setup, value: string) => setSetup((current) => ({ ...current, [key]: value }));
  const updateRow = (index: number, key: keyof CurveSubsegment, value: string) => {
    const next = rows.map((row, rowIndex) => rowIndex === index ? { ...row, [key]: key === 'type' ? value : numericValue(value) } : row);
    onChange(next);
  };
  const addRow = () => onChange([...rows, { type: 'tangent', length: numericValue(setup.totalLength) && rows.length === 0 ? numericValue(setup.totalLength) : null, superelevation_percent: null, radius: null, central_angle_deg: null, horizontal_class: null }]);
  const removeRow = (index: number) => onChange(rows.filter((_, rowIndex) => rowIndex !== index));
  const generate = () => {
    const totalLength = numericValue(setup.totalLength);
    const radius = numericValue(setup.radius);
    const count = numericValue(setup.count);
    if (!totalLength || !radius || !count || count < 1) return;
    const rowLength = totalLength / Math.trunc(count);
    onChange(Array.from({ length: Math.trunc(count) }, () => ({
      type: 'horizontal_curve',
      length: rowLength,
      superelevation_percent: numericValue(setup.superelevation),
      radius,
      central_angle_deg: numericValue(setup.centralAngle),
      horizontal_class: numericValue(setup.horizontalClass),
    })));
  };
  const unit = unitSystem === 'metric' ? 'm' : 'ft';
  return (
    <div className="curve-editor" id="two_lane_segment-horizontal_alignment_subsegments" data-testid="two-lane-curve-editor" tabIndex={-1}>
      <div className="curve-editor-heading">
        <div><h3>{t('two_lane.curve_editor_title')}</h3><p>{t('two_lane.curve_editor_caption')}</p></div>
        <button className="button button-secondary" type="button" onClick={addRow}>{t('two_lane.curve_add_row')}</button>
      </div>
      <DetailsDisclosure title={t('two_lane.curve_generate_title')}>
        <div className="curve-setup-grid">
          <Field id="two-lane-curve-total-length" label={t('two_lane.curve_total_length')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit={unit} value={setup.totalLength} onChange={(event) => updateSetup('totalLength', event.target.value)} />}
          </Field>
          <Field id="two-lane-curve-radius" label={t('two_lane.curve_radius')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit={unit} value={setup.radius} onChange={(event) => updateSetup('radius', event.target.value)} />}
          </Field>
          <Field id="two-lane-curve-superelevation" label={t('two_lane.curve_superelevation')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit="%" value={setup.superelevation} onChange={(event) => updateSetup('superelevation', event.target.value)} />}
          </Field>
          <Field id="two-lane-curve-angle" label={t('two_lane.curve_central_angle')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit="deg" value={setup.centralAngle} onChange={(event) => updateSetup('centralAngle', event.target.value)} />}
          </Field>
          <Field id="two-lane-curve-class" label={t('two_lane.curve_horizontal_class')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit="" value={setup.horizontalClass} onChange={(event) => updateSetup('horizontalClass', event.target.value)} />}
          </Field>
          <Field id="two-lane-curve-count" label={t('two_lane.curve_subsegment_count')}>
            {(controlProps) => <InputWithUnit {...controlProps} type="number" unit="rows" value={setup.count} onChange={(event) => updateSetup('count', event.target.value)} />}
          </Field>
        </div>
        <button className="button button-secondary" type="button" onClick={generate}>{t('two_lane.curve_generate')}</button>
      </DetailsDisclosure>
      {!rows.length ? <p className="curve-empty">{t('two_lane.curve_no_rows')}</p> : (
        <div className="table-scroll curve-table-scroll" role="region" aria-label={t('two_lane.curve_editor_title')} tabIndex={0}>
          <table className="curve-table"><thead><tr>
            <th scope="col">{t('two_lane.curve_type')}</th><th scope="col">{t('two_lane.curve_length')} ({unit})</th><th scope="col">{t('two_lane.curve_superelevation')} (%)</th><th scope="col">{t('two_lane.curve_radius')} ({unit})</th><th scope="col">{t('two_lane.curve_central_angle')} (deg)</th><th scope="col">{t('two_lane.curve_horizontal_class')}</th><th scope="col"><span className="sr-only">{t('two_lane.curve_remove_row')}</span></th>
          </tr></thead><tbody>
            {rows.map((row, index) => <tr key={`curve-row-${index}`} data-testid={`two-lane-curve-row-${index}`}>
              <td><select id={`two-lane-curve-${index}-type`} aria-label={`${t('two_lane.curve_type')} ${index + 1}`} value={String(row.type ?? 'tangent')} onChange={(event) => updateRow(index, 'type', event.target.value)}><option value="tangent">{t('two_lane.curve_tangent')}</option><option value="horizontal_curve">{t('two_lane.curve_horizontal_curve')}</option></select></td>
              <td><input id={`two-lane-curve-${index}-length`} aria-label={`${t('two_lane.curve_length')} ${index + 1}`} type="number" value={row.length ?? ''} onChange={(event) => updateRow(index, 'length', event.target.value)} /></td>
              <td><input id={`two-lane-curve-${index}-superelevation`} aria-label={`${t('two_lane.curve_superelevation')} ${index + 1}`} type="number" value={row.superelevation_percent ?? ''} onChange={(event) => updateRow(index, 'superelevation_percent', event.target.value)} /></td>
              <td><input id={`two-lane-curve-${index}-radius`} aria-label={`${t('two_lane.curve_radius')} ${index + 1}`} type="number" value={row.radius ?? ''} onChange={(event) => updateRow(index, 'radius', event.target.value)} /></td>
              <td><input id={`two-lane-curve-${index}-angle`} aria-label={`${t('two_lane.curve_central_angle')} ${index + 1}`} type="number" value={row.central_angle_deg ?? ''} onChange={(event) => updateRow(index, 'central_angle_deg', event.target.value)} /></td>
              <td><input id={`two-lane-curve-${index}-class`} aria-label={`${t('two_lane.curve_horizontal_class')} ${index + 1}`} type="number" value={row.horizontal_class ?? ''} onChange={(event) => updateRow(index, 'horizontal_class', event.target.value)} /></td>
              <td><button className="button button-link" type="button" onClick={() => removeRow(index)}>{t('two_lane.curve_remove_row')}</button></td>
            </tr>)}
          </tbody></table>
        </div>
      )}
    </div>
  );
}

function ExportMenu({
  stale,
  onExport,
  busy = false,
}: {
  stale: boolean;
  onExport: (format: 'csv' | 'xlsx' | 'markdown' | 'json') => void;
  busy?: boolean;
}): ReactElement {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const placeMenu = () => {
    const trigger = triggerRef.current;
    if (!trigger) return;
    const rect = trigger.getBoundingClientRect();
    const menuWidth = 210;
    const menuHeight = 150;
    const top = window.innerHeight - rect.bottom > menuHeight + 12 ? rect.bottom + 6 : Math.max(12, rect.top - menuHeight - 6);
    const left = Math.max(12, Math.min(rect.right - menuWidth, window.innerWidth - menuWidth - 12));
    setPosition({ top, left });
  };
  useEffect(() => {
    if (!open) return undefined;
    placeMenu();
    const focusFirstItem = window.setTimeout(() => {
      menuRef.current?.querySelector<HTMLButtonElement>('[role="menuitem"]')?.focus();
    }, 0);
    const dismiss = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!triggerRef.current?.contains(target) && !menuRef.current?.contains(target)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    const reposition = () => placeMenu();
    document.addEventListener('pointerdown', dismiss);
    document.addEventListener('keydown', onKeyDown);
    window.addEventListener('resize', reposition);
    window.addEventListener('scroll', reposition, true);
    return () => {
      window.clearTimeout(focusFirstItem);
      document.removeEventListener('pointerdown', dismiss);
      document.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
    };
  }, [open]);
  if (stale) {
    return <div className="export-menu-disabled"><button className="button button-secondary" type="button" disabled>{t('action.export')} ▾</button><span>{t('result.export_stale_reason')}</span></div>;
  }
  return (
    <div className="export-menu">
      <button ref={triggerRef} className="button button-secondary" type="button" aria-haspopup="menu" aria-controls={open ? menuId : undefined} aria-expanded={open} disabled={busy} aria-busy={busy || undefined} onClick={() => { if (!open) placeMenu(); setOpen((current) => !current); }}>{busy ? t('status.exporting') : `${t('action.export')} ▾`}</button>
      {open && position ? createPortal(
        <div ref={menuRef} id={menuId} className="export-menu-content" role="menu" aria-label={t('action.export')} style={{ top: position.top, left: position.left }} onKeyDown={(event) => {
          const items = Array.from(menuRef.current?.querySelectorAll<HTMLButtonElement>('[role="menuitem"]') ?? []);
          if (!items.length) return;
          const current = Math.max(0, items.indexOf(document.activeElement as HTMLButtonElement));
          const next = event.key === 'ArrowDown' ? (current + 1) % items.length
            : event.key === 'ArrowUp' ? (current - 1 + items.length) % items.length
              : event.key === 'Home' ? 0
                : event.key === 'End' ? items.length - 1
                  : null;
          if (next !== null) {
            event.preventDefault();
            items[next]?.focus();
          }
        }}>
          {(['json', 'markdown', 'xlsx'] as const).map((format) => <button className="button button-quiet" type="button" role="menuitem" key={format} onClick={() => { onExport(format); setOpen(false); }}>{t(`action.export_${format}`)}</button>)}
        </div>,
        document.body,
      ) : null}
    </div>
  );
}

function GeometryEvidenceDiagram({
  methodId,
  result,
  assetMetadata,
}: {
  methodId: string;
  result: WorkflowCalculationResponse;
  assetMetadata?: EngineeringAssetMetadata;
}): ReactElement | null {
  const { t } = useI18n();
  if (!['weaving_segment', 'merge_segment', 'diverge_segment'].includes(methodId)) return null;
  const isWeaving = methodId === 'weaving_segment';
  const isMerge = methodId === 'merge_segment';
  const title = isWeaving ? t('workflow.geometry_weaving') : isMerge ? t('workflow.geometry_merge') : t('workflow.geometry_diverge');
  const note = isWeaving ? t('workflow.geometry_weaving_note') : isMerge ? t('workflow.geometry_merge_note') : t('workflow.geometry_diverge_note');
  const weavingVariant = isWeaving
    ? assetMetadata?.variants?.find((item) => item.configuration === result.displayed_inputs.configuration && item.number_of_weaving_lanes === numericValue(result.displayed_inputs.number_of_weaving_lanes))
    : undefined;
  const assetPath = isWeaving ? weavingVariant?.asset_path : assetMetadata?.asset_path;
  if (!assetPath) return null;
  return (
    <div className="geometry-evidence" data-testid="geometry-diagram">
      <div>
        <span className="section-label">{t('workflow.geometry_evidence')}</span>
        <strong>{title}</strong>
        <p>{note}</p>
      </div>
      <img className="geometry-asset" src={engineeringAssetUrl(assetPath)} alt={title} data-asset-path={assetPath} />
      <p className="engineering-reference-note">{t('workflow.conceptual_reference')}</p>
    </div>
  );
}

type FormSection = {
  key: string;
  title: string;
  fields: string[];
  optional?: boolean;
};

function SectionNavigator({
  methodId,
  sections,
  issueCounts,
}: {
  methodId: string;
  sections: FormSection[];
  issueCounts: Map<string, number>;
}): ReactElement | null {
  const { t } = useI18n();
  if (sections.length < 2) return null;
  return (
    <nav className="section-checklist" aria-label={t('workflow.section_navigator')} data-testid="section-checklist">
      {sections.map((section) => {
        const count = issueCounts.get(section.key) ?? 0;
        return <button type="button" className={count ? 'section-checklist-item section-checklist-item-pending' : 'section-checklist-item'} key={section.key} onClick={() => document.getElementById(`workflow-section-${methodId}-${section.key}`)?.scrollIntoView({ block: 'start', behavior: 'smooth' })}>
          <span>{section.title}</span>
          <small>{section.optional ? t('workflow.optional') : count ? t('workflow.section_required', { count }) : t('workflow.section_complete')}</small>
        </button>;
      })}
    </nav>
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
  fieldErrors,
  sectionIssues,
  onFieldTouch,
}: {
  templates: WorkflowTemplatesResponse;
  starting: WorkflowStartingValuesResponse;
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onUnitSystem: (unit: UnitSystem) => void;
  onTemplate: (templateId: string) => void;
  onChange: (key: string, value: unknown) => void;
  fieldErrors: Map<string, string>;
  sectionIssues: Map<string, number>;
  onFieldTouch: (field: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const grouped = [
    { key: 'traffic', title: t('multilane.section_traffic'), fields: ['number_of_lanes', 'segment_length', 'demand_volume_veh_h', 'peak_hour_factor', 'heavy_vehicle_percent'] },
    { key: 'ffs', title: t('multilane.section_ffs'), fields: ['ffs_source', 'free_flow_speed', 'posted_speed_limit', 'lane_width', 'roadside_lateral_clearance', 'median_type', 'left_side_lateral_clearance', 'access_point_density'] },
    { key: 'heavy', title: t('multilane.section_heavy'), fields: ['heavy_vehicle_adjustment_method', 'terrain_type', 'grade_percent', 'truck_mix', 'passenger_car_equivalent'] },
  ];
  const fieldsByKey = new Map(starting.fields.map((field) => [field.key, field]));
  const sections = grouped.map((group) => ({ key: group.key, title: group.title, fields: group.fields }));
  return (
    <div className="workflow-form" data-testid="multilane-form">
      <div className="workflow-controls">
        <Field id="multilane-template" label={t('workflow.start_with')} required>
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
      <StarterNotice starting={starting} />
      <SectionNavigator methodId="multilane" sections={sections} issueCounts={sectionIssues} />
      {grouped.map((group) => (
        <EngineeringSection title={group.title} id={`workflow-section-multilane-${group.key}`} key={group.key}>
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
                    error={fieldErrors.get(field.key)}
                    onChange={(value) => onChange(field.key, value)}
                    onTouched={() => onFieldTouch(field.key)}
                  />
                );
              }
              const hint = field.key === 'access_point_density' ? t('multilane.access_density_hint') : undefined;
              return (
                <Field key={field.key} id={`multilane-${field.key}`} label={t(field.label_key)} required={Boolean(field.required || field.required_if)} hint={hint} error={fieldErrors.get(field.key)} onBlur={() => onFieldTouch(field.key)}>
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

function Phase3Form({
  methodId,
  templates,
  starting,
  inputs,
  unitSystem,
  onUnitSystem,
  onTemplate,
  onChange,
  fieldErrors,
  sectionIssues,
  onFieldTouch,
}: {
  methodId: string;
  templates: WorkflowTemplatesResponse;
  starting: WorkflowStartingValuesResponse;
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onUnitSystem: (unit: UnitSystem) => void;
  onTemplate: (templateId: string) => void;
  onChange: (key: string, value: unknown) => void;
  fieldErrors: Map<string, string>;
  sectionIssues: Map<string, number>;
  onFieldTouch: (field: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const assets = engineeringAssetsFrom(templates);
  const fieldsByKey = new Map((starting.fields ?? templates.fields).map((field) => [field.key, field]));
  const groups: WorkflowGroup[] = templates.groups?.length
    ? templates.groups
    : [{ key: 'worksheet', label_key: 'workflow.worksheet', field_keys: starting.fields.map((field) => field.key) }];
  const sections: FormSection[] = groups.map((group) => ({
    key: group.key,
    title: t(group.label_key),
    fields: group.field_keys,
    optional: /advanced|provenance|calibration/i.test(group.key),
  }));
  const optionLabel = (option: string): string => {
    const namespace = methodId === 'weaving_segment'
      ? 'weaving'
      : methodId === 'basic_freeway_segment'
        ? 'basic_freeway'
        : methodId === 'two_lane_segment'
          ? 'two_lane_segment'
          : 'ramp';
    const key = `${namespace}.option.${option}`;
    const translated = t(key);
    return translated === key ? option.replaceAll('_', ' ') : translated;
  };
  return (
    <div className="workflow-form phase3-form" data-testid={`phase3-form-${methodId}`}>
      <div className="workflow-controls">
        <Field id={`${methodId}-template`} label={t('workflow.start_with')} required>
          <select id={`${methodId}-template`} value={starting.template_id} onChange={(event) => onTemplate(event.target.value)}>
            {templates.templates.map((template) => <option value={template.template_id} key={template.template_id}>{template.label}</option>)}
          </select>
        </Field>
        <Field id={`${methodId}-unit-system`} label={t('workflow.unit_system')} required>
          <select id={`${methodId}-unit-system`} value={unitSystem} onChange={(event) => onUnitSystem(event.target.value as UnitSystem)}>
            <option value="metric">{t('locale.metric')}</option>
            <option value="imperial">{t('locale.imperial')}</option>
          </select>
        </Field>
      </div>
      <StarterNotice starting={starting} />
      <SectionNavigator methodId={methodId} sections={sections} issueCounts={sectionIssues} />
      {groups.map((group) => {
        const groupContent = (
          <>
            {methodId === 'two_lane_segment' && group.key === 'roadway' ? <TwoLaneSchematic inputs={inputs} unitSystem={unitSystem} assets={assets} /> : null}
            {methodId === 'weaving_segment' && /geometry|weaving/i.test(group.key) ? <WeavingReference inputs={inputs} assets={assets} /> : null}
            {(methodId === 'merge_segment' || methodId === 'diverge_segment') && group.key === 'geometry' ? <RampReference methodId={methodId} assets={assets} /> : null}
            <div className="form-grid">
              {group.field_keys.map((key) => {
                const field = fieldsByKey.get(key);
                if (key === 'horizontal_alignment_subsegments') return null;
                if (!field || !isVisible(field, inputs)) return null;
                const required = Boolean(field.required || field.required_if);
                if (field.kind === 'choice' || field.kind === 'boolean') {
                  const options = field.options ?? [];
                  return (
                    <ChoiceGroup
                      key={field.key}
                      legend={t(field.label_key)}
                      name={`${methodId}-${field.key}`}
                      value={valueForField(field, inputs[field.key]) as string}
                      options={options.map((option) => ({ value: option, label: optionLabel(option) }))}
                      error={fieldErrors.get(field.key)}
                      onChange={(value) => onChange(field.key, parseInput(field, value))}
                      onTouched={() => onFieldTouch(field.key)}
                    />
                  );
                }
                if (field.kind === 'json') return null;
                const id = `${methodId}-${field.key}`;
                return (
                  <Field key={field.key} id={id} label={t(field.label_key)} required={required} error={fieldErrors.get(field.key)} onBlur={() => onFieldTouch(field.key)}>
                    {(controlProps) => <InputWithUnit {...controlProps} type={field.kind === 'text' ? 'text' : 'number'} unit={unitFor(field, unitSystem)} value={valueForField(field, inputs[field.key])} onChange={(event: ChangeEvent<HTMLInputElement>) => onChange(field.key, parseInput(field, event.target.value))} />}
                  </Field>
                );
              })}
            </div>
            {methodId === 'two_lane_segment' && group.key === 'roadway' && inputs.horizontal_alignment === 'horizontal_curves' ? <CurveEditor inputs={inputs} unitSystem={unitSystem} onChange={(value) => onChange('horizontal_alignment_subsegments', value)} /> : null}
          </>
        );
        const advanced = /advanced|provenance|calibration/i.test(group.key);
        return <div className="workflow-group" id={`workflow-section-${methodId}-${group.key}`} key={group.key}>{advanced ? <DetailsDisclosure title={t(group.label_key)}>{groupContent}</DetailsDisclosure> : <EngineeringSection title={t(group.label_key)}>{groupContent}</EngineeringSection>}</div>;
      })}
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
  fieldErrors,
  onFieldTouch,
}: {
  templates: WorkflowTemplatesResponse;
  starting: WorkflowStartingValuesResponse;
  inputs: DisplayedInputs;
  unitSystem: UnitSystem;
  onUnitSystem: (unit: UnitSystem) => void;
  onTemplate: (templateId: string) => void;
  onChange: (rows: FacilityRow[]) => void;
  fieldErrors: Map<string, string>;
  onFieldTouch: (field: string) => void;
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
        <Field id="facility-template" label={t('workflow.facility_template')} required>
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
                        aria-invalid={fieldErrors.has(`rows[${rowIndex}].${column}`) ? 'true' : undefined}
                        onBlur={() => onFieldTouch(`rows[${rowIndex}].${column}`)}
                        onChange={(event) => updateRow(rowIndex, column, event.target.value)}
                      />
                      {fieldErrors.get(`rows[${rowIndex}].${column}`) ? <span className="field-error">{fieldErrors.get(`rows[${rowIndex}].${column}`)}</span> : null}
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

export function FacilityResultPanel({
  result,
  onExport,
  onSave,
  saveLabel,
  onRecalculate,
  stale = false,
  workingAction,
}: {
  result: WorkflowCalculationResponse;
  onExport: (format: 'csv' | 'xlsx' | 'markdown' | 'json') => void;
  onSave: () => void;
  saveLabel?: string;
  onRecalculate?: () => void;
  stale?: boolean;
  workingAction?: 'calculate' | 'save' | 'export' | null;
}): ReactElement {
  const { t } = useI18n();
  const capacityFailure = Boolean(result.presentation.capacity.failure);
  const resultWarning = result.calculation_state.presentation_state === 'valid_current_result_with_warning';
  const showWarning = resultWarning && !stale;
  const metricsUnavailable = result.presentation.metrics.some((metric) => metric.availability === 'not_predicted');
  const answer = result.presentation.answer;
  const segments = Array.isArray(result.presentation.segments) ? result.presentation.segments as Array<Record<string, unknown>> : [];
  return (
    <div className="workflow-results" data-testid="workflow-results">
      <EngineeringSection title={t('result.facility_section_title')} description={t('result.facility_section_description')}>
        <ResultHero label={t('result.facility_level_of_service')} value={answer.available && answer.value ? answer.value : t('result.not_calculated')} state={stale ? 'stale' : capacityFailure ? 'capacity' : showWarning ? 'warning' : 'current'} supporting={answer.source} />
        {stale ? <StaleResultPanel /> : capacityFailure ? <CapacityFailurePanel metricsUnavailable={metricsUnavailable} /> : showWarning ? <WarningPanel message={result.presentation.warning} /> : null}
        <div className="metric-grid">
          {result.presentation.metrics.map((metric) => <MetricCard key={metric.key} label={t(`result.metric.${metric.key}`)} value={metricDisplayValue(metric, t)} unit={metric.unit ?? undefined} />)}
        </div>
        <div className="critical-callout"><strong>{t('result.critical_segment')}</strong><span>{String(result.presentation.capacity.critical_segment_id ?? t('result.not_calculated'))}</span></div>
        <div className="table-scroll" role="region" aria-label={t('result.segment_results')} tabIndex={0}>
          <table className="result-table"><thead><tr><th>{t('facility.col.segment_id')}</th><th>{t('facility.col.segment_type')}</th><th>{t('result.segment_speed')}</th><th>{t('result.segment_density')}</th><th>{t('result.level_of_service')}</th></tr></thead><tbody>
            {segments.map((segment) => <tr key={String(segment.segment_id)}><td>{String(segment.segment_id)}</td><td>{String(segment.segment_type)}</td><td>{segment.average_speed === null || segment.average_speed === undefined ? t('result.not_calculated') : `${Number(segment.average_speed).toFixed(1)} ${String(segment.average_speed_unit)}`}</td><td>{segment.follower_density === null || segment.follower_density === undefined ? t('result.not_calculated') : `${Number(segment.follower_density).toFixed(1)} ${String(segment.follower_density_unit)}`}</td><td><StatusBadge tone={segment.level_of_service === 'F' ? 'capacity' : 'current'}>{String(segment.level_of_service ?? t('result.not_calculated'))}</StatusBadge></td></tr>)}
          </tbody></table>
        </div>
        <div className="result-actions">
          {stale ? <button className="button button-primary" type="button" disabled={workingAction === 'calculate'} aria-busy={workingAction === 'calculate' || undefined} onClick={onRecalculate}>{workingAction === 'calculate' ? t('status.calculating') : t('action.recalculate')}</button> : <>
            <button className="button button-primary" type="button" disabled={workingAction === 'save'} aria-busy={workingAction === 'save' || undefined} onClick={onSave}>{workingAction === 'save' ? t('status.saving') : saveLabel ?? t('action.save_project')}</button>
            <ExportMenu stale={false} busy={workingAction === 'export'} onExport={onExport} />
          </>}
        </div>
      </EngineeringSection>
      <DetailsDisclosure title={t('result.evidence_title')}>
        <div className="evidence-grid"><div><span className="section-label">{t('result.assumptions')}</span><ul>{result.result.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></div><div><span className="section-label">{t('result.warnings')}</span><ul>{result.result.warnings.length ? result.result.warnings.map((item) => <li key={item}>{item}</li>) : <li>{t('result.no_warnings')}</li>}</ul></div><div><span className="section-label">{t('result.fingerprint')}</span><code>{result.calculation_fingerprint}</code></div></div>
      </DetailsDisclosure>
    </div>
  );
}

function ResultPlaceholder({
  ready,
  requiredCount,
  exampleValues,
}: {
  ready: boolean;
  requiredCount: number;
  exampleValues: boolean;
}): ReactElement {
  const { t } = useI18n();
  return (
    <section className="result-placeholder" data-testid="result-placeholder" aria-labelledby="result-inspector-title">
      <div className="result-inspector-heading"><div><span className="section-label">{t('result.inspector_label')}</span><h2 id="result-inspector-title" tabIndex={-1}>{ready ? t('status.ready_to_calculate') : t('result.not_calculated')}</h2></div>{exampleValues ? <StatusBadge tone="neutral">{t('workflow.example_values')}</StatusBadge> : null}</div>
      <p>{ready ? t('result.ready_supporting') : t('result.missing_supporting', { count: requiredCount })}</p>
    </section>
  );
}

export function AnalysisWorkflow({ method, onBack, onDirtyChange, onProjectSaved, initialScenario, onScenarioResultSaved }: AnalysisWorkflowProps): ReactElement {
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
  const [activeOperation, setActiveOperation] = useState<'calculate' | 'save' | 'export' | null>(null);
  const [submitAttempted, setSubmitAttempted] = useState(false);
  const [touchedFields, setTouchedFields] = useState<Set<string>>(() => new Set());
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [focusValidationRequest, setFocusValidationRequest] = useState(0);
  const initialScenarioRef = useRef(initialScenario);
  const initialScenarioAppliedRef = useRef(false);
  const validationSequenceRef = useRef(0);
  const calculationSequenceRef = useRef(0);
  const inputRevisionRef = useRef(0);
  const focusValidationRef = useRef(false);
  const resultInspectorRef = useRef<HTMLDivElement>(null);

  const isFacility = method.method_id === 'two_lane_facility';
  const isMultilane = method.method_id === 'multilane_segment';
  const serializedInputs = useMemo(() => serializeInputSnapshot(inputs), [inputs]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = window.setTimeout(() => setNotice(null), 5_000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    onDirtyChange?.(dirty);
  }, [dirty, onDirtyChange]);

  useEffect(() => {
    if (!dirty) return undefined;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', beforeUnload);
    return () => window.removeEventListener('beforeunload', beforeUnload);
  }, [dirty]);

  useEffect(() => {
    let active = true;
    calculationSequenceRef.current += 1;
    inputRevisionRef.current += 1;
    validationSequenceRef.current += 1;
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
    setSubmitAttempted(false);
    setFocusValidationRequest(0);
    focusValidationRef.current = false;
    setTouchedFields(new Set());
    setActiveOperation(null);
    initialScenarioRef.current = initialScenario;
    initialScenarioAppliedRef.current = false;
    fetchWorkflowTemplates(method.method_id)
      .then((response) => {
        if (!active) return;
        setTemplates(response);
        const preferred = initialScenarioRef.current?.templateId;
        const first = response.default_template_id ?? response.templates[0]?.template_id ?? '';
        setTemplateId(response.templates.some((template) => template.template_id === preferred) ? preferred ?? first : first);
      })
      .catch((reason: Error) => { if (active) setError(reason.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [method.method_id]);

  useEffect(() => {
    if (!templateId) return;
    let active = true;
    calculationSequenceRef.current += 1;
    inputRevisionRef.current += 1;
    validationSequenceRef.current += 1;
    setWorking(true);
    setError(null);
    setResult(null);
    setValidation(null);
    setSubmitAttempted(false);
    setTouchedFields(new Set());
    setFocusValidationRequest(0);
    focusValidationRef.current = false;
    fetchWorkflowStartingValues(method.method_id, templateId, unitSystem)
      .then((response) => {
        if (!active) return;
        setStarting(response);
        const scenario = initialScenarioRef.current;
        const canRestoreScenario = !initialScenarioAppliedRef.current
          && scenario
          && scenario.templateId === templateId
          && scenario.unitSystem === unitSystem;
        inputRevisionRef.current += 1;
        validationSequenceRef.current += 1;
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
    const requestSequence = validationSequenceRef.current + 1;
    validationSequenceRef.current = requestSequence;
    const timer = window.setTimeout(() => {
      validateWorkflow(method.method_id, templateId, unitSystem, inputs)
        .then((response) => {
          if (validationSequenceRef.current === requestSequence) setValidation(response);
        })
        .catch((reason: Error) => {
          if (validationSequenceRef.current === requestSequence) setError(reason.message);
        });
    }, 350);
    return () => window.clearTimeout(timer);
  }, [method.method_id, templateId, unitSystem, serializedInputs, starting, inputs]);

  const updateInputs = (next: DisplayedInputs) => {
    inputRevisionRef.current += 1;
    validationSequenceRef.current += 1;
    setInputs(next);
    setDirty(true);
    setNotice(null);
  };

  const markFieldTouched = (field: string) => {
    setTouchedFields((current) => current.has(field) ? current : new Set([...current, field]));
  };

  const confirmWorksheetReset = (): boolean => {
    if (!dirty) return true;
    return window.confirm(t('workflow.discard_confirmation'));
  };

  const changeTemplate = (nextTemplateId: string) => {
    if (!confirmWorksheetReset()) return;
    calculationSequenceRef.current += 1;
    inputRevisionRef.current += 1;
    validationSequenceRef.current += 1;
    setTemplateId(nextTemplateId);
  };

  const changeUnitSystem = (nextUnitSystem: UnitSystem) => {
    if (!confirmWorksheetReset()) return;
    calculationSequenceRef.current += 1;
    inputRevisionRef.current += 1;
    validationSequenceRef.current += 1;
    setUnitSystem(nextUnitSystem);
  };

  const onChangeFromForm = (key: string, value: unknown) => {
    const next = { ...inputs, [key]: value };
    if (key === 'horizontal_alignment') {
      next.horizontal_alignment_subsegments = value === 'horizontal_curves'
        ? (Array.isArray(inputs.horizontal_alignment_subsegments) ? inputs.horizontal_alignment_subsegments : [])
        : [];
    }
    if (method.method_id === 'weaving_segment' && key === 'configuration') {
      if (value === 'two_sided') {
        const entry = String(inputs.entry_side ?? 'right');
        next.number_of_weaving_lanes = 0;
        next.exit_side = entry === 'right' ? 'left' : 'right';
        next.lc_rf = null;
        next.lc_fr = null;
        next.lc_rr = numericValue(inputs.lc_rr) ?? 2;
      } else {
        const entry = String(inputs.entry_side ?? 'right');
        const existingNwl = numericValue(inputs.number_of_weaving_lanes);
        next.number_of_weaving_lanes = existingNwl === 2 || existingNwl === 3 ? existingNwl : 2;
        next.exit_side = entry;
        next.lc_rf = numericValue(inputs.lc_rf) ?? 0;
        next.lc_fr = numericValue(inputs.lc_fr) ?? 0;
        next.lc_rr = null;
      }
    }
    updateInputs(next);
  };

  const focusValidationError = () => {
    focusValidationRef.current = true;
    setFocusValidationRequest((current) => current + 1);
  };

  const handleCalculate = () => {
    setSubmitAttempted(true);
    if (!templateId) {
      focusValidationError();
      return;
    }
    setWorking(true);
    setActiveOperation('calculate');
    setError(null);
    const requestSequence = calculationSequenceRef.current + 1;
    const inputRevision = inputRevisionRef.current;
    calculationSequenceRef.current = requestSequence;
    validateWorkflow(method.method_id, templateId, unitSystem, inputs)
      .then((freshValidation) => {
        if (calculationSequenceRef.current !== requestSequence || inputRevisionRef.current !== inputRevision) return null;
        setValidation(freshValidation);
        if (!freshValidation.valid) {
          focusValidationError();
          return null;
        }
        return calculateWorkflow(method.method_id, templateId, unitSystem, inputs);
      })
      .then((response) => {
        if (!response || calculationSequenceRef.current !== requestSequence || inputRevisionRef.current !== inputRevision) return;
        setResult(response);
        setDirty(false);
        setValidation((current) => current ? {
          ...current,
          valid: true,
          ready: true,
          calculation_fingerprint: response.calculation_fingerprint,
          input_snapshot_fingerprint: response.input_snapshot_fingerprint,
          calculation_state: response.calculation_state,
        } : current);
        if (!isFacility && window.matchMedia('(max-width: 1180px)').matches) {
          window.setTimeout(() => {
            const destination = document.getElementById('result-inspector-title') ?? resultInspectorRef.current;
            destination?.focus();
            destination?.scrollIntoView({ block: 'start', behavior: 'smooth' });
          }, 0);
        }
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => {
        if (calculationSequenceRef.current === requestSequence) {
          setWorking(false);
          setActiveOperation(null);
        }
      });
  };

  const handleExport = (format: 'csv' | 'xlsx' | 'markdown' | 'json') => {
    if (!result || dirty) return;
    setNotice(t('status.exporting'));
    setWorking(true);
    setActiveOperation('export');
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
      .finally(() => { setWorking(false); setActiveOperation(null); });
  };

  const handleSave = () => {
    if (!result || dirty) return;
    setWorking(true);
    setActiveOperation('save');
    if (onScenarioResultSaved) {
      Promise.resolve(onScenarioResultSaved(result))
        .catch((reason: Error) => setError(reason.message))
        .finally(() => { setWorking(false); setActiveOperation(null); });
      return;
    }
    saveAnalysisToProject(result, `${t(method.name_key)} study`)
      .then((response) => {
        onProjectSaved?.(response.project);
        downloadText(`${method.method_id}-project-v2.json`, JSON.stringify(response.project, null, 2), 'application/json');
        setNotice(t('project.saved'));
      })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => { setWorking(false); setActiveOperation(null); });
  };

  const isStale = dirty && Boolean(result);
  const resultWarning = result?.calculation_state.presentation_state === 'valid_current_result_with_warning';
  const capacityFailure = Boolean(result?.presentation.capacity.failure);
  const handoff = result?.calculation_state.presentation_state === 'hcm_stopping_or_handoff' || Boolean(result?.presentation.handoff);
  const status = isStale
    ? t('state.stale_title')
    : handoff
      ? t('state.handoff_title')
      : capacityFailure
        ? t('state.capacity_title')
        : resultWarning
          ? t('state.warning_title')
          : result
            ? t('status.current')
            : validation?.valid
              ? t('status.ready_to_calculate')
              : t('status.items_required');
  const statusTone = isStale ? 'stale' : capacityFailure ? 'capacity' : resultWarning ? 'warning' : result ? 'current' : 'neutral';
  const targetIdForIssue = (field: string | null): string | undefined => {
    if (!field) return undefined;
    const rowMatch = field.match(/^rows\[(\d+)\]\.(.+)$/);
    if (rowMatch) {
      const row = Array.isArray(inputs.rows) ? inputs.rows[Number(rowMatch[1])] as Record<string, unknown> | undefined : undefined;
      const rowId = row?.segment_id ?? Number(rowMatch[1]) + 1;
      return `facility-input-${String(rowId)}-${rowMatch[2]}`;
    }
    return isFacility ? undefined : `${isMultilane ? 'multilane' : method.method_id}-${field}`;
  };
  const allFieldErrors = new Map(
    (validation?.errors ?? [])
      .filter((issue) => issue.field)
      .map((issue) => [issue.field as string, issue.message]),
  );
  const fieldErrors = new Map([...allFieldErrors].filter(([field]) => submitAttempted || touchedFields.has(field)));
  const errors = submitAttempted
    ? (validation?.errors.map((issue) => ({ message: issue.message, targetId: targetIdForIssue(issue.field) })) ?? [])
    : [];
  useEffect(() => {
    if (!focusValidationRequest || !focusValidationRef.current || !errors.length) return undefined;
    const frame = window.requestAnimationFrame(() => {
      const firstTarget = errors[0]?.targetId;
      const target = firstTarget ? document.getElementById(firstTarget) : null;
      const destination = document.getElementById('error-summary') ?? target;
      destination?.focus({ preventScroll: true });
      destination?.scrollIntoView({ block: 'center', behavior: 'smooth' });
      focusValidationRef.current = false;
      setFocusValidationRequest(0);
    });
    return () => window.cancelAnimationFrame(frame);
  }, [errors, focusValidationRequest]);
  const formSections: FormSection[] = isMultilane
    ? [
      { key: 'traffic', title: t('multilane.section_traffic'), fields: ['number_of_lanes', 'segment_length', 'demand_volume_veh_h', 'peak_hour_factor', 'heavy_vehicle_percent'] },
      { key: 'ffs', title: t('multilane.section_ffs'), fields: ['ffs_source', 'free_flow_speed', 'posted_speed_limit', 'lane_width', 'roadside_lateral_clearance', 'median_type', 'left_side_lateral_clearance', 'access_point_density'] },
      { key: 'heavy', title: t('multilane.section_heavy'), fields: ['heavy_vehicle_adjustment_method', 'terrain_type', 'grade_percent', 'truck_mix', 'passenger_car_equivalent'] },
    ]
    : (templates?.groups?.map((group) => ({ key: group.key, title: t(group.label_key), fields: group.field_keys, optional: /advanced|provenance|calibration/i.test(group.key) })) ?? []);
  const sectionIssues = new Map(formSections.map((section) => [
    section.key,
    (validation?.errors ?? []).filter((issue) => issue.field !== null && section.fields.includes(issue.field)).length,
  ]));
  const assetMetadata = engineeringAssetsFrom(templates);
  const exampleResult = Boolean(starting?.starter_kind === 'example' && !initialScenario);
  const requiredCount = validation?.errors.length ?? 0;
  return (
    <div className={`page-stack workflow-page ${isFacility ? 'facility-workflow' : ''}`} data-testid={`workflow-${method.method_id}`}>
      <div className="workflow-toolbar"><button className="button button-quiet" type="button" onClick={onBack}>← {t('action.back_to_methods')}</button></div>
      <AnalysisHeader title={t(method.name_key)} method={`${method.chapter_reference} · ${scopeFor(method, t)}`} status={status} tone={statusTone} context={initialScenario ? t('workflow.project_context') : undefined} />
      {loading ? <ScopeNotice title={t('status.loading')}>{t('workflow.loading')}</ScopeNotice> : null}
      {error ? <ScopeNotice title={t('workflow.error_title')} tone="warning">{error}</ScopeNotice> : null}
      {templates && starting && isFacility ? <div className="facility-workspace">
        <FacilityForm templates={templates} starting={starting} inputs={inputs} unitSystem={unitSystem} onUnitSystem={changeUnitSystem} onTemplate={changeTemplate} fieldErrors={fieldErrors} onFieldTouch={markFieldTouched} onChange={(rows) => updateInputs({ rows })} />
        <ErrorSummary errors={errors} />
        {!result ? <ReadinessBar ready={Boolean(validation?.valid)} requiredCount={requiredCount} disabled={working} working={activeOperation === 'calculate'} actionLabel={t('action.calculate')} onAction={handleCalculate} /> : null}
        {result ? <FacilityResultPanel result={result} stale={isStale} workingAction={activeOperation} onExport={handleExport} onSave={handleSave} onRecalculate={handleCalculate} saveLabel={onScenarioResultSaved ? t('action.save_scenario') : undefined} /> : <ResultPlaceholder ready={Boolean(validation?.valid)} requiredCount={requiredCount} exampleValues={exampleResult} />}
      </div> : null}
      {templates && starting && !isFacility ? <>
        <div className="workflow-workbench">
          <div className="workflow-input-workspace">
            {isMultilane
              ? <MultilaneForm templates={templates} starting={starting} inputs={inputs} unitSystem={unitSystem} onUnitSystem={changeUnitSystem} onTemplate={changeTemplate} fieldErrors={fieldErrors} sectionIssues={sectionIssues} onFieldTouch={markFieldTouched} onChange={onChangeFromForm} />
              : <Phase3Form methodId={method.method_id} templates={templates} starting={starting} inputs={inputs} unitSystem={unitSystem} onUnitSystem={changeUnitSystem} onTemplate={changeTemplate} fieldErrors={fieldErrors} sectionIssues={sectionIssues} onFieldTouch={markFieldTouched} onChange={onChangeFromForm} />}
            <ErrorSummary errors={errors} />
            {!result ? <ReadinessBar ready={Boolean(validation?.valid)} requiredCount={requiredCount} disabled={working} working={activeOperation === 'calculate'} actionLabel={t('action.calculate')} onAction={handleCalculate} /> : <ReadinessBar ready={!isStale} showAction={false} statusLabel={isStale ? t('state.stale_title') : t('status.result_current')} />}
          </div>
          <div className="workflow-result-inspector" ref={resultInspectorRef} tabIndex={-1}>
            {result ? <ResultPanel result={result} stale={isStale} onExport={handleExport} onSave={handleSave} onRecalculate={handleCalculate} exampleResult={exampleResult} workingAction={activeOperation} saveLabel={onScenarioResultSaved ? t('action.save_scenario') : undefined} /> : <ResultPlaceholder ready={Boolean(validation?.valid)} requiredCount={requiredCount} exampleValues={exampleResult} />}
          </div>
        </div>
        {result && !isStale ? <DetailedResultSection result={result} assetMetadata={assetMetadata} /> : null}
      </> : null}
      <ActionToast message={notice} />
    </div>
  );
}
