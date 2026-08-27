import { useMemo, useState, type ChangeEvent, type ReactElement } from 'react';
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
  DetailsDisclosure,
  EngineeringSection,
  ScopeNotice,
  StatusBadge,
} from '../components/primitives';
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

function displayDelta(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(2) : String(value);
}

export function ProjectWorkspace({
  project,
  onProjectChange,
  onNewAnalysis,
  onEditScenario,
}: {
  project: Record<string, unknown> | null;
  onProjectChange: (project: Record<string, unknown>) => void;
  onNewAnalysis: () => void;
  onEditScenario: (methodId: string, context: ScenarioEditContext) => void;
}): ReactElement {
  const { t } = useI18n();
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [working, setWorking] = useState(false);
  const [scenarioName, setScenarioName] = useState('Alternative');
  const [renameName, setRenameName] = useState('');
  const [selectedAnalysisId, setSelectedAnalysisId] = useState('');
  const [leftScenarioId, setLeftScenarioId] = useState('');
  const [rightScenarioId, setRightScenarioId] = useState('');
  const [comparison, setComparison] = useState<Record<string, unknown> | null>(null);
  const [selectedScenarioId, setSelectedScenarioId] = useState('');

  const typedProject = project as unknown as ProjectRecord | null;
  const analyses = typedProject?.analyses ?? [];
  const selectedAnalysis = useMemo(
    () => analyses.find((analysis) => analysis.analysis_id === selectedAnalysisId) ?? analyses[0],
    [analyses, selectedAnalysisId],
  );
  const scenarios = selectedAnalysis?.scenarios ?? [];
  const selectedScenario = scenarios.find((scenario) => scenario.scenario_id === selectedScenarioId) ?? scenarios[0];
  const scenarioKindLabel = (kind: string) => t(kind === 'base' ? 'project.kind.base' : 'project.kind.duplicate');
  const scenarioStatusLabel = (status: ScenarioRecord['result_status']) => t(`project.status.${status}`);

  const downloadProject = () => {
    if (!project) return;
    const blob = new Blob([JSON.stringify(project, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${typedProject?.project_name ?? 'hcm-project'}-v2.json`;
    anchor.click();
    window.URL.revokeObjectURL(url);
    setNotice(t('project.downloaded'));
  };

  const openProject = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result)) as Record<string, unknown>;
        setWorking(true);
        validateProject(parsed)
          .then((response) => {
            onProjectChange(response.project);
            setNotice(response.migrated ? t('project.migrated') : t('project.opened'));
            setError(null);
          })
          .catch((reason: Error) => setError(reason.message))
          .finally(() => setWorking(false));
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : t('project.invalid_file'));
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  const updateProject = (action: Promise<{ project: Record<string, unknown> }>, successMessage: string) => {
    setWorking(true);
    action
      .then((response) => { onProjectChange(response.project); setNotice(successMessage); setError(null); })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  const duplicate = () => {
    if (!project || !selectedAnalysis || !selectedScenario || !scenarioName.trim()) return;
    updateProject(
      duplicateProjectScenario(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, scenarioName.trim()),
      t('project.scenario_duplicated'),
    );
  };

  const rename = () => {
    if (!project || !selectedAnalysis || !selectedScenario || !renameName.trim()) return;
    updateProject(
      renameProjectScenario(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, renameName.trim()),
      t('project.scenario_renamed'),
    );
  };

  const calculateScenario = () => {
    if (!project || !selectedAnalysis || !selectedScenario || !selectedScenario.template_id) return;
    setWorking(true);
    calculateWorkflow(
      selectedAnalysis.method_id,
      selectedScenario.template_id,
      selectedScenario.unit_system,
      selectedScenario.displayed_inputs,
    )
      .then((snapshot) => recordProjectResult(project, selectedAnalysis.analysis_id, selectedScenario.scenario_id, snapshot))
      .then((response) => { onProjectChange(response.project); setNotice(t('project.scenario_calculated')); setError(null); })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  const compare = () => {
    if (!project || !selectedAnalysis || !leftScenarioId || !rightScenarioId) return;
    setWorking(true);
    compareProjectScenarios(project, selectedAnalysis.analysis_id, leftScenarioId, rightScenarioId)
      .then((response) => { setComparison(response.comparison); setError(null); })
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setWorking(false));
  };

  return (
    <div className="page-stack project-page" data-testid="project-workspace">
      <header className="page-header"><p className="eyebrow">{t('project.eyebrow')}</p><h1>{typedProject?.project_name ?? t('project.title')}</h1><p className="page-description">{t('project.description')}</p></header>
      <div className="project-toolbar">
        <label className="button button-secondary project-file-button" htmlFor="project-file">{t('action.open_project')}<input id="project-file" type="file" accept="application/json,.json" onChange={openProject} /></label>
        <button className="button button-secondary" type="button" disabled={!project} onClick={downloadProject}>{t('action.download_project')}</button>
        <button className="button button-primary" type="button" onClick={onNewAnalysis}>{t('action.new_analysis')}</button>
      </div>
      {error ? <ScopeNotice title={t('workflow.error_title')} tone="warning">{error}</ScopeNotice> : null}
      {notice ? <ScopeNotice title={t('workflow.notice_title')}>{notice}</ScopeNotice> : null}
      {!project ? <ScopeNotice title={t('project.empty_title')}>{t('project.empty_supporting')}</ScopeNotice> : null}
      {project ? <>
        <EngineeringSection title={t('project.graph_title')} description={t('project.graph_description')}>
          <div className="project-facts"><div><span>{t('project.schema')}</span><strong>{typedProject?.schema_version}</strong></div><div><span>{t('project.analysis_count')}</span><strong>{analyses.length}</strong></div><div><span>{t('project.updated')}</span><strong>{typedProject?.updated_at}</strong></div></div>
          <div className="analysis-list">
            {analyses.map((analysis) => <button className={`analysis-row ${selectedAnalysis?.analysis_id === analysis.analysis_id ? 'analysis-row-active' : ''}`} type="button" key={analysis.analysis_id} onClick={() => { setSelectedAnalysisId(analysis.analysis_id); setSelectedScenarioId(analysis.scenarios[0]?.scenario_id ?? ''); setComparison(null); }}><span><strong>{analysis.analysis_name}</strong><small>{analysis.method_id} · {analysis.input_contract}</small></span><StatusBadge tone="neutral">{analysis.scenarios.length} {t('project.scenarios')}</StatusBadge></button>)}
          </div>
        </EngineeringSection>
        {selectedAnalysis ? <EngineeringSection title={t('project.scenario_title')} description={t('project.scenario_description')}>
          <div className="scenario-list">{scenarios.map((scenario) => <button className={`scenario-row ${selectedScenario?.scenario_id === scenario.scenario_id ? 'scenario-row-active' : ''}`} type="button" key={scenario.scenario_id} onClick={() => setSelectedScenarioId(scenario.scenario_id)}><span><strong>{scenario.scenario_name}</strong><small>{scenarioKindLabel(scenario.kind)} · {scenarioStatusLabel(scenario.result_status)}</small></span><StatusBadge tone={scenario.result_status === 'current' ? 'current' : scenario.result_status === 'stale' ? 'stale' : 'neutral'}>{scenarioStatusLabel(scenario.result_status)}</StatusBadge></button>)}</div>
          <div className="project-actions"><button className="button button-primary" type="button" disabled={working || !selectedScenario || !selectedScenario.template_id} onClick={calculateScenario}>{t('action.calculate_scenario')}</button><button className="button button-secondary" type="button" disabled={working || !selectedScenario || !selectedScenario.template_id} onClick={() => { if (selectedScenario?.template_id) onEditScenario(selectedAnalysis.method_id, { analysisId: selectedAnalysis.analysis_id, scenarioId: selectedScenario.scenario_id, templateId: selectedScenario.template_id, unitSystem: selectedScenario.unit_system, displayedInputs: selectedScenario.displayed_inputs }); }}>{t('action.edit_scenario')}</button><label>{t('project.duplicate_name')}<input value={scenarioName} onChange={(event) => setScenarioName(event.target.value)} /></label><button className="button button-secondary" type="button" disabled={working || !selectedScenario} onClick={duplicate}>{t('action.duplicate_scenario')}</button><label>{t('project.rename_name')}<input value={renameName} onChange={(event) => setRenameName(event.target.value)} placeholder={selectedScenario?.scenario_name} /></label><button className="button button-secondary" type="button" disabled={working || !selectedScenario || !renameName.trim()} onClick={rename}>{t('action.rename_scenario')}</button></div>
        </EngineeringSection> : null}
        {selectedAnalysis && scenarios.length > 1 ? <EngineeringSection title={t('project.compare_title')} description={t('project.compare_description')}>
          <div className="project-controls"><label>{t('project.left_scenario')}<select value={leftScenarioId} onChange={(event) => setLeftScenarioId(event.target.value)}><option value="">{t('project.choose_scenario')}</option>{scenarios.map((scenario) => <option value={scenario.scenario_id} key={scenario.scenario_id}>{scenario.scenario_name}</option>)}</select></label><label>{t('project.right_scenario')}<select value={rightScenarioId} onChange={(event) => setRightScenarioId(event.target.value)}><option value="">{t('project.choose_scenario')}</option>{scenarios.map((scenario) => <option value={scenario.scenario_id} key={scenario.scenario_id}>{scenario.scenario_name}</option>)}</select></label><button className="button button-primary" type="button" disabled={working || !leftScenarioId || !rightScenarioId || leftScenarioId === rightScenarioId} onClick={compare}>{t('action.compare')}</button></div>
          {comparison ? <div className="comparison-result" data-testid="comparison-result"><strong>{t('project.los_transition')}</strong><span>{String((comparison.los_grade_transition as Record<string, unknown>)?.from ?? t('result.not_calculated'))} → {String((comparison.los_grade_transition as Record<string, unknown>)?.to ?? t('result.not_calculated'))}</span><small>{t('project.compare_current_only')}</small>{Array.isArray(comparison.numeric_deltas) && comparison.numeric_deltas.length ? <ul>{(comparison.numeric_deltas as Array<Record<string, unknown>>).map((delta) => <li key={String(delta.key)}>{String(delta.key)}: {displayDelta(delta.delta)}</li>)}</ul> : <small>{t('project.no_numeric_deltas')}</small>}</div> : null}
        </EngineeringSection> : null}
        <DetailsDisclosure title={t('project.identity_title')}><div className="project-identity"><code>{typedProject?.project_id}</code><span>{t('project.identity_supporting')}</span></div></DetailsDisclosure>
      </> : null}
      {working ? <p className="muted" role="status">{t('status.working')}</p> : null}
    </div>
  );
}
