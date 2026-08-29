import { useEffect, useMemo, useRef, useState, type ReactElement } from 'react';
import { fetchMethods, recordProjectResult } from '../api/client';
import type { MethodDefinition, WorkflowCalculationResponse } from '../api/types';
import { AnalysisWorkflow, type ScenarioEditContext } from './AnalysisWorkflow';
import { ProjectWorkspace } from './ProjectWorkspace';
import {
  getActionableMethods,
  getFrontendModule,
  getMethodActionabilityStatus,
  isMethodActionable,
  isMethodRouteEligible,
  type FrontendModuleDefinition,
  type MethodActionabilityStatus,
} from '../registry/modules';
import { useI18n } from '../i18n';
import {
  AppShell,
  DetailsDisclosure,
  EngineeringSection,
  PageHeader,
  ScopeNotice,
  StatusBadge,
  type MethodNavigationId,
  type PageId,
} from '../components/primitives';

interface RouteTarget {
  page: PageId;
  methodId: string | null;
  scenarioEdit: ScenarioEditContext | null;
}

interface HcmHistoryState {
  hcmHistoryIndex?: number;
  methodId?: string | null;
  scenarioEdit?: ScenarioEditContext | null;
  scrollTop?: number;
}

function routeFromLocation(state: HcmHistoryState = {}): RouteTarget {
  const path = window.location.pathname.replace(/\/+$/, '') || '/';
  const analysisMatch = path.match(/^\/analysis\/([^/]+)$/);
  if (analysisMatch) return { page: 'new-analysis', methodId: decodeURIComponent(analysisMatch[1]), scenarioEdit: null };
  if (path === '/new-analysis') return { page: 'new-analysis', methodId: null, scenarioEdit: null };
  if (path.startsWith('/project/analysis/') && state.scenarioEdit) {
    return { page: 'new-analysis', methodId: state.methodId ?? null, scenarioEdit: state.scenarioEdit };
  }
  if (path === '/project' || path.startsWith('/project/')) return { page: 'project', methodId: null, scenarioEdit: null };
  if (path === '/reference' || path.startsWith('/reference/')) return { page: 'reference', methodId: null, scenarioEdit: null };
  return { page: 'home', methodId: null, scenarioEdit: null };
}

function pathForRoute(route: RouteTarget): string {
  if (route.scenarioEdit) return `/project/analysis/${route.scenarioEdit.analysisId}/scenarios/${route.scenarioEdit.scenarioId}`;
  if (route.page === 'new-analysis' && route.methodId) return `/analysis/${route.methodId}`;
  if (route.page === 'new-analysis') return '/new-analysis';
  if (route.page === 'project') return '/project';
  if (route.page === 'reference') return '/reference';
  return '/';
}

function currentHistoryState(): HcmHistoryState {
  return (window.history.state ?? {}) as HcmHistoryState;
}

function scopeFor(method: MethodDefinition, translate: (key: string) => string): string {
  const scopeKey = method.name_key.replace(/\.name$/, '.scope');
  const translated = translate(scopeKey);
  return translated === scopeKey ? translate(method.description_key) : translated;
}

export function MethodCard({
  method,
  onReference,
  onSelect,
  frontendModule,
}: {
  method: MethodDefinition;
  onReference: (methodId: string) => void;
  onSelect: (methodId: string) => void;
  frontendModule?: FrontendModuleDefinition;
}): ReactElement {
  const { t } = useI18n();
  const module = frontendModule ?? getFrontendModule(method.method_id);
  const actionabilityStatus = getMethodActionabilityStatus(method, module);
  const actionable = isMethodActionable(method, module);
  const routeEligible = isMethodRouteEligible(method, module);
  const statusLabel: Record<Exclude<MethodActionabilityStatus, 'actionable'>, string> = {
    engineering_unavailable: t('new_analysis.engineering_unavailable'),
    not_delivered: t('new_analysis.reference_only'),
    contract_mismatch: t('new_analysis.engineering_unavailable'),
  };
  return (
    <article className="method-card" data-testid={`method-card-${method.method_id}`}>
      <div className="method-card-heading">
        <div>
          <p className="method-family">{t(`method.${method.family}`)}</p>
          <h3>{t(method.name_key)}</h3>
        </div>
        {!actionable ? <StatusBadge tone={actionabilityStatus === 'contract_mismatch' ? 'warning' : 'neutral'}>{statusLabel[actionabilityStatus as Exclude<MethodActionabilityStatus, 'actionable'>]}</StatusBadge> : null}
      </div>
      <p className="method-use"><strong>{t('new_analysis.use_for')}</strong> {t(method.description_key)}</p>
      <dl className="method-meta">
        <div><dt>{t('reference.chapter')}</dt><dd>{method.chapter_reference}</dd></div>
        <div><dt>{t('reference.scope')}</dt><dd>{scopeFor(method, t)}</dd></div>
      </dl>
      <div className="method-card-actions">
        <button
          className="button button-primary"
          type="button"
          disabled={!routeEligible}
          aria-disabled={!routeEligible}
          onClick={() => { if (routeEligible) onSelect(method.method_id); }}
        >
          {t('action.start_analysis')}
        </button>
        <button className="button button-link" type="button" onClick={() => onReference(method.method_id)}>
          {t('action.method_guide')}
        </button>
      </div>
    </article>
  );
}

function HomePage({
  methods,
  onNavigate,
}: {
  methods: MethodDefinition[];
  onNavigate: (page: PageId) => void;
}): ReactElement {
  const { t } = useI18n();
  const groups = useMemo(() => {
    const result = new Map<string, MethodDefinition[]>();
    methods.forEach((method) => result.set(method.family, [...(result.get(method.family) ?? []), method]));
    return [...result.entries()];
  }, [methods]);
  return (
    <div className="page-stack home-page">
      <PageHeader eyebrow={t('app.eyebrow')} title={t('home.title')} description={t('app.description')} />
      <div className="home-actions">
        <EngineeringSection title={t('home.quick_title')} description={t('home.quick_description')}>
          <button className="button button-primary" type="button" onClick={() => onNavigate('new-analysis')}>{t('action.start_analysis')}</button>
        </EngineeringSection>
        <EngineeringSection title={t('home.project_title')} description={t('home.project_description')}>
          <button className="button button-secondary" type="button" onClick={() => onNavigate('project')}>{t('action.open_workspace')}</button>
        </EngineeringSection>
      </div>
      <EngineeringSection title={t('home.methods_title')} description={t('home.methods_description')}>
        <div className="home-method-list">
          {groups.map(([family, familyMethods]) => <div key={family}><strong>{t(`method.${family}`)}</strong><span>{familyMethods.map((method) => t(method.name_key)).join(' · ')}</span></div>)}
        </div>
        <button className="button button-link" type="button" onClick={() => onNavigate('reference')}>{t('action.method_guide')}</button>
      </EngineeringSection>
      <ScopeNotice title={t('home.audit_title')} tone="neutral">{t('home.audit_note')}</ScopeNotice>
    </div>
  );
}

function NewAnalysisPage({
  methods,
  loading,
  onReference,
  onSelect,
}: {
  methods: MethodDefinition[];
  loading: boolean;
  onReference: (methodId: string) => void;
  onSelect: (methodId: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const actionable = useMemo(() => getActionableMethods(methods), [methods]);
  const grouped = useMemo(() => {
    const groups = new Map<string, MethodDefinition[]>();
    methods.forEach((method) => groups.set(method.family, [...(groups.get(method.family) ?? []), method]));
    return [...groups.entries()];
  }, [methods]);
  return (
    <div className="page-stack chooser-page">
      <PageHeader eyebrow={t('new_analysis.eyebrow')} title={t('new_analysis.title')} description={t('new_analysis.description')} />
      <div className="availability-summary" role="status"><strong>{actionable.length}</strong><span>{t('new_analysis.available_count', { count: actionable.length })}</span><button className="button button-link" type="button" onClick={() => onReference('')}>{t('action.method_guide')}</button></div>
      {loading ? <ScopeNotice title={t('new_analysis.loading_title')}>{t('status.loading')}</ScopeNotice> : null}
      {!loading && !methods.length ? <ScopeNotice title={t('status.no_methods')} tone="warning">{t('reference.api_error')}</ScopeNotice> : null}
      {grouped.map(([family, familyMethods]) => (
        <EngineeringSection title={t(`method.${family}`)} key={family}>
          <div className="method-grid">
            {familyMethods.map((method) => <MethodCard method={method} onReference={onReference} onSelect={onSelect} key={method.method_id} />)}
          </div>
        </EngineeringSection>
      ))}
    </div>
  );
}

function ReferencePage({
  methods,
  loading,
  onSelect,
}: {
  methods: MethodDefinition[];
  loading: boolean;
  onSelect: (methodId: string) => void;
}): ReactElement {
  const { t } = useI18n();
  return (
    <div className="page-stack method-guide-page">
      <PageHeader eyebrow={t('reference.eyebrow')} title={t('reference.title')} description={t('reference.description')} />
      {loading ? <ScopeNotice title={t('new_analysis.loading_title')}>{t('status.loading')}</ScopeNotice> : null}
      <div className="reference-list">
        {methods.map((method) => {
          const module = getFrontendModule(method.method_id);
          const actionabilityStatus = getMethodActionabilityStatus(method, module);
          const actionable = isMethodActionable(method, module);
          const unavailableLabel: Record<Exclude<MethodActionabilityStatus, 'actionable'>, string> = {
            engineering_unavailable: t('new_analysis.engineering_unavailable'),
            not_delivered: t('new_analysis.reference_only'),
            contract_mismatch: t('new_analysis.engineering_unavailable'),
          };
          return (
            <article className="reference-row" id={`method-guide-${method.method_id}`} key={method.method_id} data-testid={`reference-${method.method_id}`}>
              <div className="reference-row-title">
                <p className="method-family">{t(`method.${method.family}`)}</p>
                <h2>{t(method.name_key)}</h2>
                <p><strong>{t('new_analysis.use_for')}</strong> {t(method.description_key)}</p>
              </div>
              <dl className="reference-facts">
                <div><dt>{t('reference.chapter')}</dt><dd>{method.chapter_reference}</dd></div>
                <div><dt>{t('reference.scope')}</dt><dd>{scopeFor(method, t)}</dd></div>
                <div><dt>{t('reference.units')}</dt><dd>{method.supported_unit_systems.join(' / ')}</dd></div>
              </dl>
              <div className="reference-actions">
                <button className="button button-primary" type="button" disabled={!isMethodRouteEligible(method, module)} onClick={() => onSelect(method.method_id)}>{t('action.start_analysis')}</button>
                {!actionable ? <StatusBadge tone={actionabilityStatus === 'contract_mismatch' ? 'warning' : 'neutral'}>{unavailableLabel[actionabilityStatus as Exclude<MethodActionabilityStatus, 'actionable'>]}</StatusBadge> : null}
              </div>
              <DetailsDisclosure title={t('reference.technical_title')}>
                <dl className="technical-facts">
                  <div><dt>{t('reference.method_identifier')}</dt><dd><code>{method.method_identifier}</code></dd></div>
                  <div><dt>{t('reference.contract')}</dt><dd><code>{method.input_contract}</code></dd></div>
                </dl>
              </DetailsDisclosure>
            </article>
          );
        })}
      </div>
    </div>
  );
}

export function App(): ReactElement {
  const { t } = useI18n();
  const initialState = currentHistoryState();
  const initialRoute = useMemo(() => routeFromLocation(initialState), []);
  const [page, setPage] = useState<PageId>(initialRoute.page);
  const [selectedMethodId, setSelectedMethodId] = useState<string | null>(initialRoute.methodId);
  const [scenarioEdit, setScenarioEdit] = useState<ScenarioEditContext | null>(initialRoute.scenarioEdit);
  const [project, setProject] = useState<Record<string, unknown> | null>(null);
  const [methods, setMethods] = useState<MethodDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  const [workflowDirty, setWorkflowDirty] = useState(false);
  const currentRouteRef = useRef<RouteTarget>(initialRoute);
  const historyIndexRef = useRef(typeof initialState.hcmHistoryIndex === 'number' ? initialState.hcmHistoryIndex : 0);
  const ignoreRestorePopRef = useRef(false);

  useEffect(() => {
    if (typeof initialState.hcmHistoryIndex === 'number') return;
    window.history.replaceState({ ...initialState, hcmHistoryIndex: historyIndexRef.current, methodId: initialRoute.methodId, scrollTop: 0 }, '', window.location.pathname + window.location.search + window.location.hash);
  }, []);

  useEffect(() => {
    let active = true;
    fetchMethods()
      .then((response) => {
        if (!active) return;
        setMethods(response.methods);
        setApiConnected(true);
      })
      .catch(() => { if (active) setApiConnected(false); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  const applyRoute = (route: RouteTarget, scrollTop = 0) => {
    currentRouteRef.current = route;
    setPage(route.page);
    setSelectedMethodId(route.methodId);
    setScenarioEdit(route.scenarioEdit);
    setWorkflowDirty(false);
    window.setTimeout(() => {
      const main = document.getElementById('main-content');
      if (main) {
        main.scrollTo({ top: scrollTop, behavior: 'auto' });
        main.focus({ preventScroll: true });
      }
    }, 0);
  };

  const confirmLeave = (): boolean => {
    if (scenarioEdit) return window.confirm(t('workflow.project_switch_confirmation'));
    if (workflowDirty) return window.confirm(t('workflow.discard_confirmation'));
    return true;
  };

  const commitRoute = (route: RouteTarget, replace = false) => {
    const main = document.getElementById('main-content');
    const currentState = currentHistoryState();
    window.history.replaceState({
      ...currentState,
      hcmHistoryIndex: historyIndexRef.current,
      methodId: currentRouteRef.current.methodId,
      scenarioEdit: currentRouteRef.current.scenarioEdit,
      scrollTop: main?.scrollTop ?? 0,
    }, '', window.location.pathname + window.location.search + window.location.hash);
    const nextIndex = replace ? historyIndexRef.current : historyIndexRef.current + 1;
    const nextState: HcmHistoryState = { hcmHistoryIndex: nextIndex, methodId: route.methodId, scenarioEdit: route.scenarioEdit, scrollTop: 0 };
    if (replace) window.history.replaceState(nextState, '', pathForRoute(route));
    else window.history.pushState(nextState, '', pathForRoute(route));
    historyIndexRef.current = nextIndex;
    applyRoute(route);
  };

  const requestNavigation = (route: RouteTarget) => {
    if (!confirmLeave()) return;
    commitRoute(route);
  };

  useEffect(() => {
    const onPopState = (event: PopStateEvent) => {
      if (ignoreRestorePopRef.current) {
        ignoreRestorePopRef.current = false;
        return;
      }
      const targetState = (event.state ?? {}) as HcmHistoryState;
      const targetRoute = routeFromLocation(targetState);
      if (!confirmLeave()) {
        if (typeof targetState.hcmHistoryIndex === 'number') {
          const offset = historyIndexRef.current - targetState.hcmHistoryIndex;
          if (offset !== 0) {
            ignoreRestorePopRef.current = true;
            window.history.go(offset);
            return;
          }
        }
        window.history.pushState({ hcmHistoryIndex: historyIndexRef.current, methodId: currentRouteRef.current.methodId, scenarioEdit: currentRouteRef.current.scenarioEdit, scrollTop: 0 }, '', pathForRoute(currentRouteRef.current));
        return;
      }
      historyIndexRef.current = typeof targetState.hcmHistoryIndex === 'number' ? targetState.hcmHistoryIndex : historyIndexRef.current;
      applyRoute(targetRoute, typeof targetState.scrollTop === 'number' ? targetState.scrollTop : 0);
    };
    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [scenarioEdit, t, workflowDirty]);

  const navigate = (nextPage: PageId) => requestNavigation({ page: nextPage, methodId: null, scenarioEdit: null });
  const referenceMethod = () => requestNavigation({ page: 'reference', methodId: null, scenarioEdit: null });
  const selectMethod = (methodId: MethodNavigationId | string) => requestNavigation({ page: 'new-analysis', methodId, scenarioEdit: null });
  const editScenario = (methodId: string, context: ScenarioEditContext) => requestNavigation({ page: 'new-analysis', methodId, scenarioEdit: context });

  const saveEditedScenario = (snapshot: WorkflowCalculationResponse): Promise<void> => {
    if (!project || !scenarioEdit) return Promise.reject(new Error(t('project.edit_session_expired')));
    return recordProjectResult(project, scenarioEdit.analysisId, scenarioEdit.scenarioId, snapshot)
      .then((response) => {
        setProject(response.project);
        commitRoute({ page: 'project', methodId: null, scenarioEdit: null });
      });
  };

  const backFromWorkflow = () => requestNavigation({ page: scenarioEdit ? 'project' : 'new-analysis', methodId: null, scenarioEdit: null });
  const selectedMethod = selectedMethodId ? methods.find((method) => method.method_id === selectedMethodId) : undefined;

  return (
    <AppShell activePage={page} activeMethodId={selectedMethodId} onNavigate={navigate} onSelectMethod={selectMethod} apiConnected={apiConnected}>
      {page === 'home' ? <HomePage methods={methods} onNavigate={navigate} /> : null}
      {page === 'new-analysis' && selectedMethod ? <AnalysisWorkflow method={selectedMethod} initialScenario={scenarioEdit ?? undefined} onDirtyChange={setWorkflowDirty} onBack={backFromWorkflow} onScenarioResultSaved={scenarioEdit ? saveEditedScenario : undefined} onProjectSaved={(savedProject) => { setProject(savedProject); commitRoute({ page: 'project', methodId: null, scenarioEdit: null }); }} /> : null}
      {page === 'new-analysis' && !selectedMethod ? <NewAnalysisPage methods={methods} loading={loading} onReference={referenceMethod} onSelect={selectMethod} /> : null}
      {page === 'project' ? <ProjectWorkspace project={project} methods={methods} onProjectChange={setProject} onNewAnalysis={() => navigate('new-analysis')} onEditScenario={editScenario} /> : null}
      {page === 'reference' ? <ReferencePage methods={methods} loading={loading} onSelect={selectMethod} /> : null}
    </AppShell>
  );
}
