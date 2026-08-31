import { useEffect, useMemo, useRef, useState, type ChangeEvent, type ReactElement } from 'react';
import {
  calculateWorkflow,
  compareProjectScenarios,
  duplicateProjectScenario,
  recordProjectResult,
  renameProjectScenario,
  validateProject,
} from '../api/client';
import { useI18n } from '../i18n';
import {
  ActionToast,
  DetailsDisclosure,
  EngineeringSection,
  ScopeNotice,
  StatusBadge,
} from '../components/primitives';
import type { MethodDefinition } from '../api/types';
import { getFrontendModule, isMethodActionable } from '../registry/modules';
import type { ScenarioEditContext } from './AnalysisWorkflow';

interface ScenarioRecord {
  scenario_id: string;
  scenario_name: string;
  kind: string;
  result_status: 'not_calculated' | 'current' | 'stale';
  calculation_fingerprint: string;
  unit_system: 'metric' | 'imperial';
  template_id: string | null;
  displayed_inputs: Record<string, unknown>;
  result: Record<string, unknown> | null;
}

interface AnalysisRecord {
  analysis_id: string;
  analysis_name: string;
  method_id: string;
  method_identifier: string;
  input_contract: string;
  scenarios: ScenarioRecord[];
}

interface ProjectRecord {
  project_id: string;
  project_name: string;
  schema_version: string;
  updated_at: string;
  analyses: AnalysisRecord[];
  migration?: Record<string, unknown>;
}

interface StoredEngineResult {
  engine_result?: { outputs?: Record<string, unknown> };
  stored_at?: string;
}

interface WorkspaceError {
  message: string;
  titleKey: string;
}

const comparisonVocabulary: Record<string, { labelKey: string; unit: string }> = {
  density_pc_mi_ln: { labelKey: 'result.metric.density', unit: 'pc/mi/ln' },
  facility_follower_density_followers_mi_ln: { labelKey: 'result.metric.follower_density', unit: 'followers/mi/ln' },
  average_speed_mph: { labelKey: 'result.metric.average_speed', unit: 'mph' },
  facility_average_speed_mph: { labelKey: 'result.metric.facility_average_speed', unit: 'mph' },
  demand_flow_rate_pc_h_ln: { labelKey: 'result.metric.demand_flow_rate', unit: 'pc/h/ln' },
  capacity_pc_h_ln: { labelKey: 'result.metric.capacity', unit: 'pc/h/ln' },
  facility_percent_followers: { labelKey: 'result.metric.facility_percent_followers', unit: '%' },
  demand_capacity_ratio: { labelKey: 'result.metric.governing_vc', unit: 'ratio' },
};

function displayValue(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(2) : String(value ?? '—');
}

function statusTone(status: ScenarioRecord['result_status']): 'current' | 'stale' | 'neutral' {
  return status === 'current' ? 'current' : status === 'stale' ? 'stale' : 'neutral';
}

function formatUpdatedAt(value: string, locale: 'en' | 'th'): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat(locale === 'th' ? 'th-TH' : 'en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function storedLos(scenario: ScenarioRecord): string | null {
  const outputs = (scenario.result as StoredEngineResult | null)?.engine_result?.outputs;
  const value = outputs?.level_of_service ?? outputs?.facility_level_of_service;
  return typeof value === 'string' || typeof value === 'number' ? String(value) : null;
}

function ScenarioActionsMenu({
  scenario,
  working,
  onDuplicate,
  onRename,
}: {
  scenario: ScenarioRecord;
  working: boolean;
  onDuplicate: (name: string) => void;
  onRename: (name: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const [duplicateName, setDuplicateName] = useState(t('project.default_alternative'));
  const [renameName, setRenameName] = useState('');
  const detailsRef = useRef<HTMLDetailsElement>(null);
  useEffect(() => {
    setDuplicateName(t('project.default_alternative'));
    setRenameName('');
  }, [scenario.scenario_id, t]);
  return (
    <details className="scenario-actions-menu" ref={detailsRef} onKeyDown={(event) => {
      if (event.key === 'Escape') {
        detailsRef.current?.removeAttribute('open');
        (detailsRef.current?.querySelector('summary') as HTMLElement | null)?.focus();
      }
    }}>
      <summary className="button button-secondary">{t('project.scenario_actions')} ▾</summary>
      <div className="scenario-actions-content">
        <label>{t('project.duplicate_name')}<input value={duplicateName} onChange={(event) => setDuplicateName(event.target.value)} /></label>
        <button className="button button-quiet" type="button" disabled={working || !duplicateName.trim()} onClick={() => onDuplicate(duplicateName)}>{t('action.duplicate_scenario')}</button>
        <label>{t('project.rename_name')}<input value={renameName} onChange={(event) => setRenameName(event.target.value)} placeholder={scenario.scenario_name} /></label>
        <button className="button button-quiet" type="button" disabled={working || !renameName.trim()} onClick={() => onRename(renameName)}>{t('action.rename_scenario')}</button>
      </div>
    </details>
  );
}

export function ProjectWorkspace({
  project,
  methods,
  onProjectChange,
  onNewAnalysis,
  onEditScenario,
}: {
  project: Record<string, unknown> | null;
  methods: MethodDefinition[];
  onProjectChange: (project: Record<string, unknown>) => void;
  onNewAnalysis: () => void;
  onEditScenario: (methodId: string, context: ScenarioEditContext) => void;
}): ReactElement {
  const { locale, t } = useI18n();
  const [error, setError] = useState<WorkspaceError | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [workingAction, setWorkingAction] = useState<'open' | 'calculate' | 'scenario' | 'compare' | null>(null);
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('');
  const [selectedScenarioId, setSelectedScenarioId] = useState('');
  const [leftScenarioId, setLeftScenarioId] = useState('');
  const [rightScenarioId, setRightScenarioId] = useState('');
  const [comparison, setComparison] = useState<Record<string, unknown> | null>(null);

  const typedProject = project as unknown as ProjectRecord | null;
  const analyses = typedProject?.analyses ?? [];
  const selectedAnalysis = useMemo(
    () => analyses.find((analysis) => analysis.analysis_id === selectedAnalysisId) ?? analyses[0],
    [analyses, selectedAnalysisId],
  );
  const scenarios = selectedAnalysis?.scenarios ?? [];
  const selectedScenario = scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? scenarios[0];
  const selectedMethod = selectedAnalysis ? methods.find((method) => method.method_id === selectedAnalysis.method_id) : undefined;
  const workflowActionable = selectedMethod ? isMethodActionable(selectedMethod, getFrontendModule(selectedMethod.method_id)) : false;
  const scenarioKindLabel = (kind: string) => t(kind === 'base' ? 'project.kind.base' : 'project.kind.duplicate');
  const scenarioStatusLabel = (status: ScenarioRecord['result_status']) => t(`project.status.${status}`);
  const working = workingAction !== null;
  const showError = (reason: unknown, titleKey = 'workflow.error_title') => {
    setError({
      message: reason instanceof Error ? reason.message : t('project.invalid_file'),
      titleKey,
    });
  };

  useEffect(() => {
    if (!notice) return undefined;
    const timer = window.setTimeout(() => setNotice(null), 5_000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const downloadProject = () => {
    if (!project) return;
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${typedProject?.project_name ?? 'hcm-project'}-v2.json`;
    anchor.style.display = 'none';
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => window.URL.revokeObjectURL(url), 1_000);
    setNotice(t('project.downloaded'));
  };

  const openProject = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as Record<string, unknown>;
        setWorkingAction('open');
        validateProject(parsed)
          .then((response) => {
            onProjectChange(response.project);
            setSelectedAnalysisId('');
            setSelectedScenarioId('');
            setNotice(response.migrated ? t('project.migrated') : t('project.opened'));
            setError(null);
          })
          .catch((reason: Error) => showError(reason))
          .finally(() => setWorkingAction(null));
      } catch (reason) {
        showError(reason);
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const updateProject = (action: Promise<{ project: Record<string, unknown> }>, successMessage: string) => {
    setWorkingAction('scenario');
    action
      .then((response) => { onProjectChange(response.project); setNotice(successMessage); setError(null); })
      .catch((reason: Error) => showError(reason))
      .finally(() => setWorkingAction(null));
  };

  const duplicate = (name: string) => {
    if (!project || !selectedAnalysis || !selectedScenario || !name.trim()) return;
    updateProject(
      duplicateProjectScenario(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, name.trim()),
      t('project.scenario_duplicated'),
    );
  };

  const rename = (name: string) => {
    if (!project || !selectedAnalysis || !selectedScenario || !name.trim()) return;
    updateProject(
      renameProjectScenario(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, name.trim()),
      t('project.scenario_renamed'),
    );
  };

  const calculateScenario = () => {
    if (!workflowActionable || !project || !selectedAnalysis || !selectedScenario || !selectedScenario.template_id) return;
    setWorkingAction('calculate');
    calculateWorkflow(selectedAnalysis.method_id, selectedScenario.template_id, selectedScenario.unit_system, selectedScenario.displayed_inputs)
      .then((snapshot) => recordProjectResult(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, snapshot))
      .then((response) => { onProjectChange(response.project); setNotice(t('project.scenario_calculated')); setError(null); })
      .catch((reason: Error) => showError(reason))
      .finally(() => setWorkingAction(null));
  };

  const compare = () => {
    if (!project || !selectedAnalysis || !leftScenarioId || !rightScenarioId) return;
    setWorkingAction('compare');
    compareProjectScenarios(project, selectedAnalysis.analysis_id, leftScenarioId, rightScenarioId)
      .then((response) => { setComparison(response.comparison); setError(null); })
      .catch((reason: Error) => {
        showError(
          reason,
          /current results/i.test(reason.message) ? 'project.compare_requires_current_title' : 'workflow.error_title',
        );
      })
      .finally(() => setWorkingAction(null));
  };

  const editSelectedScenario = () => {
    if (!workflowActionable || !selectedAnalysis || !selectedScenario?.template_id) return;
    onEditScenario(selectedAnalysis.method_id, {
      analysisId: selectedAnalysis.analysis_id,
      scenarioId: selectedScenario.scenario_id,
      templateId: selectedScenario.template_id,
      unitSystem: selectedScenario.unit_system,
      displayedInputs: selectedScenario.displayed_inputs,
    });
  };

  return (
    <div className="page-stack project-page" data-testid="project-workspace">
      <header className="page-header"><p className="eyebrow">{t('project.eyebrow')}</p><h1>{typedProject?.project_name ?? t('project.title')}</h1><p className="page-description">{t('project.description')}</p></header>
      {error ? <ScopeNotice title={t(error.titleKey)} tone="warning">{error.message}</ScopeNotice> : null}
      {!project ? <EngineeringSection title={t('project.empty_title')} description={t('project.empty_supporting')}>
        <div className="project-empty-actions">
          <label className="button button-secondary project-file-button" htmlFor="project-file-empty">{t('action.open_project')}<input id="project-file-empty" type="file" accept="application/json,.json" onChange={openProject} /></label>
          <button className="button button-primary" type="button" onClick={onNewAnalysis}>{t('action.start_analysis')}</button>
        </div>
      </EngineeringSection> : null}
      {project ? <>
        <div className="project-toolbar project-topbar">
          <div><span className="section-label">{t('project.updated')}</span><strong>{formatUpdatedAt(typedProject?.updated_at ?? '', locale)}</strong></div>
          <span className="project-analysis-count">{t('project.analysis_count')}: {analyses.length}</span>
          <span className="status-spacer" />
          <label className="button button-secondary project-file-button" htmlFor="project-file">{t('action.open_project')}<input id="project-file" type="file" accept="application/json,.json" onChange={openProject} /></label>
          <button className="button button-secondary" type="button" onClick={downloadProject}>{t('action.download_project')}</button>
          <button className="button button-primary" type="button" onClick={onNewAnalysis}>{t('action.new_analysis')}</button>
        </div>
        <div className="project-master-detail">
          <aside className="project-master" aria-label={t('project.analysis_list')}>
            <div className="project-master-heading"><strong>{t('project.analyses_title')}</strong><span>{analyses.length}</span></div>
            <div className="analysis-list">
              {analyses.map((analysis) => {
                const method = methods.find((candidate) => candidate.method_id === analysis.method_id);
                const activeAnalysis = selectedAnalysis?.analysis_id === analysis.analysis_id;
                return <div className={`analysis-tree ${activeAnalysis ? 'analysis-tree-active' : ''}`} key={analysis.analysis_id}>
                  <button className="analysis-row" type="button" onClick={() => { setSelectedAnalysisId(analysis.analysis_id); setSelectedScenarioId(analysis.scenarios[0]?.scenario_id ?? ''); setComparison(null); }}>
                    <span><strong>{method ? t(method.name_key) : analysis.analysis_name}</strong><small>{method?.chapter_reference ?? t('project.method_unavailable')}</small></span><StatusBadge tone="neutral">{analysis.scenarios.length} {t('project.scenarios')}</StatusBadge>
                  </button>
                  <div className="scenario-list" aria-label={t('project.scenarios')}>
                    {analysis.scenarios.map((scenario) => <button className={`scenario-row ${selectedScenario?.scenario_id === scenario.scenario_id ? 'scenario-row-active' : ''}`} type="button" key={scenario.scenario_id} onClick={() => { setSelectedAnalysisId(analysis.analysis_id); setSelectedScenarioId(scenario.scenario_id); setComparison(null); }}><span><strong>{scenario.scenario_name}</strong><small>{scenarioKindLabel(scenario.kind)}</small></span><StatusBadge tone={statusTone(scenario.result_status)}>{scenarioStatusLabel(scenario.result_status)}</StatusBadge></button>)}
                  </div>
                </div>;
              })}
            </div>
          </aside>
          <section className="project-detail" aria-live="polite">
            {selectedAnalysis && selectedScenario ? <>
              <header className="project-detail-header"><div><span className="section-label">{selectedMethod?.chapter_reference ?? t('project.method_unavailable')}</span><h2>{selectedMethod ? t(selectedMethod.name_key) : selectedAnalysis.analysis_name}</h2><p>{selectedScenario.scenario_name}</p></div><StatusBadge tone={statusTone(selectedScenario.result_status)}>{scenarioStatusLabel(selectedScenario.result_status)}</StatusBadge></header>
              {selectedScenario.result_status === 'current' ? <section className="project-result-summary"><span>{t('project.current_result')}</span><strong>{storedLos(selectedScenario) ? `${t('result.level_of_service')}: ${storedLos(selectedScenario)}` : t('project.current_result_supporting')}</strong><p>{t('project.current_result_supporting')}</p></section> : <ScopeNotice title={scenarioStatusLabel(selectedScenario.result_status)} tone={selectedScenario.result_status === 'stale' ? 'warning' : 'neutral'}>{selectedScenario.result_status === 'stale' ? t('state.stale_supporting') : t('project.not_calculated_supporting')}</ScopeNotice>}
              {!workflowActionable ? <ScopeNotice title={t('project.method_unavailable')} tone="warning">{t('project.method_unavailable_supporting')}</ScopeNotice> : null}
              <div className="project-primary-actions">
                {selectedScenario.result_status === 'current' ? <button className="button button-primary" type="button" disabled={!workflowActionable} onClick={editSelectedScenario}>{t('action.edit_scenario')}</button> : <button className="button button-primary" type="button" disabled={working || !workflowActionable || !selectedScenario.template_id} aria-busy={workingAction === 'calculate' || undefined} onClick={calculateScenario}>{workingAction === 'calculate' ? t('status.calculating') : selectedScenario.result_status === 'stale' ? t('action.recalculate') : t('action.calculate_scenario')}</button>}
                {selectedScenario.result_status !== 'current' ? <button className="button button-secondary" type="button" disabled={!workflowActionable || !selectedScenario.template_id} onClick={editSelectedScenario}>{t('action.edit_scenario')}</button> : null}
                <ScenarioActionsMenu key={selectedScenario.scenario_id} scenario={selectedScenario} working={working} onDuplicate={duplicate} onRename={rename} />
              </div>
              <EngineeringSection title={t('project.compare_title')} description={t('project.compare_description')}>
                {scenarios.length < 2 ? <ScopeNotice title={t('project.compare_empty_title')} tone="neutral">{t('project.compare_empty_supporting')}</ScopeNotice> : <>
                  <div className="project-controls"><label>{t('project.left_scenario')}<select value={leftScenarioId} onChange={(event) => setLeftScenarioId(event.target.value)}><option value="">{t('project.choose_scenario')}</option>{scenarios.map((scenario) => <option value={scenario.scenario_id} key={scenario.scenario_id}>{scenario.scenario_name}</option>)}</select></label><label>{t('project.right_scenario')}<select value={rightScenarioId} onChange={(event) => setRightScenarioId(event.target.value)}><option value="">{t('project.choose_scenario')}</option>{scenarios.map((scenario) => <option value={scenario.scenario_id} key={scenario.scenario_id}>{scenario.scenario_name}</option>)}</select></label><button className="button button-secondary" type="button" disabled={working || !leftScenarioId || !rightScenarioId || leftScenarioId === rightScenarioId} aria-busy={workingAction === 'compare' || undefined} onClick={compare}>{workingAction === 'compare' ? t('status.working') : t('action.compare')}</button></div>
                  {comparison ? <div className="comparison-result" data-testid="comparison-result"><strong>{t('project.los_transition')}</strong><span>{String((comparison.los_grade_transition as Record<string, unknown>)?.from ?? t('result.not_calculated'))} → {String((comparison.los_grade_transition as Record<string, unknown>)?.to ?? t('result.not_calculated'))}</span><small>{t('project.compare_current_only')}</small>{Array.isArray(comparison.numeric_deltas) && comparison.numeric_deltas.length ? <div className="table-scroll" role="region" aria-label={t('project.compare_title')} tabIndex={0}><table className="comparison-table"><thead><tr><th>{t('project.metric')}</th><th>{t('project.scenario_a')}</th><th>{t('project.scenario_b')}</th><th>{t('project.delta')}</th><th>{t('project.unit')}</th></tr></thead><tbody>{(comparison.numeric_deltas as Array<Record<string, unknown>>).map((delta) => { const vocabulary = comparisonVocabulary[String(delta.key)]; return <tr key={String(delta.key)}><td>{vocabulary ? t(vocabulary.labelKey) : t('project.additional_metric')}</td><td>{displayValue(delta.left)}</td><td>{displayValue(delta.right)}</td><td>{displayValue(delta.delta)}</td><td>{vocabulary?.unit ?? '—'}</td></tr>; })}</tbody></table></div> : <small>{t('project.no_numeric_deltas')}</small>}</div> : null}
                </>}
              </EngineeringSection>
              <DetailsDisclosure title={t('project.technical_title')}><dl className="technical-facts"><div><dt>{t('project.schema')}</dt><dd>{typedProject?.schema_version}</dd></div><div><dt>{t('project.project_identifier')}</dt><dd><code>{typedProject?.project_id}</code></dd></div><div><dt>{t('reference.method_identifier')}</dt><dd><code>{selectedAnalysis.method_identifier}</code></dd></div><div><dt>{t('reference.contract')}</dt><dd><code>{selectedAnalysis.input_contract}</code></dd></div><div><dt>{t('result.fingerprint')}</dt><dd><code>{selectedScenario.calculation_fingerprint}</code></dd></div></dl></DetailsDisclosure>
            </> : <ScopeNotice title={t('project.empty_title')} tone="neutral">{t('project.empty_supporting')}</ScopeNotice>}
          </section>
        </div>
      </> : null}
      <ActionToast message={notice} />
    </div>
  );
}
