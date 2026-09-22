import { useEffect, useMemo, useRef, useState, type ReactElement } from 'react';
import { fetchMethods, recordProjectResult } from '../api/client';
import type { MethodDefinition, WorkflowCalculationResponse } from '../api/types';
import { AnalysisWorkflow, type ScenarioEditContext } from './AnalysisWorkflow';
import { ProjectWorkspace } from './ProjectWorkspace';
import { methodGuideSpecs } from './methodGuideContent';
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
  const referenceMatch = path.match(/^\/reference\/([^/]+)$/);
  if (referenceMatch) return { page: 'reference', methodId: decodeURIComponent(referenceMatch[1]), scenarioEdit: null };
  if (path === '/reference') return { page: 'reference', methodId: null, scenarioEdit: null };
  return { page: 'home', methodId: null, scenarioEdit: null };
}

function pathForRoute(route: RouteTarget): string {
  if (route.scenarioEdit) return `/project/analysis/${route.scenarioEdit.analysisId}/scenarios/${route.scenarioEdit.scenarioId}`;
  if (route.page === 'new-analysis' && route.methodId) return `/analysis/${route.methodId}`;
  if (route.page === 'new-analysis') return '/new-analysis';
  if (route.page === 'project') return '/project';
  if (route.page === 'reference' && route.methodId) return `/reference/${encodeURIComponent(route.methodId)}`;
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

export function ReferencePage({
  methods,
  loading,
  selectedMethodId,
  onReferenceSelect,
  onSelect,
}: {
  methods: MethodDefinition[];
  loading: boolean;
  selectedMethodId: string | null;
  onReferenceSelect: (methodId: string) => void;
  onSelect: (methodId: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const guidedMethods = methods.flatMap((method) => {
    const spec = methodGuideSpecs[method.method_id];
    return spec ? [{ method, spec }] : [];
  });
  const selected = guidedMethods.find(({ method }) => method.method_id === selectedMethodId) ?? guidedMethods[0];

  return (
    <div className="page-stack method-guide-page">
      <PageHeader eyebrow={t('reference.eyebrow')} title={t('reference.title')} description={t('reference.description')} />
      {loading ? <ScopeNotice title={t('new_analysis.loading_title')}>{t('status.loading')}</ScopeNotice> : null}
      {!loading && !guidedMethods.length ? <ScopeNotice title={t('status.no_methods')} tone="warning">{t('reference.api_error')}</ScopeNotice> : null}

      {selected ? (
        <div className="handbook-workspace">
          <nav className="handbook-method-nav" aria-label={t('reference.choose_title')}>
            <div className="handbook-method-nav-heading">
              <strong>{t('reference.choose_title')}</strong>
              <span>{t('reference.choose_description')}</span>
            </div>
            {guidedMethods.map(({ method, spec }) => {
              const active = method.method_id === selected.method.method_id;
              return (
                <button
                  className={`handbook-method-nav-item${active ? ' handbook-method-nav-item-active' : ''}`}
                  type="button"
                  aria-current={active ? 'page' : undefined}
                  onClick={() => onReferenceSelect(method.method_id)}
                  key={method.method_id}
                >
                  <span className="method-family">{t(`method.${method.family}`)}</span>
                  <strong>{t(method.name_key)}</strong>
                  <small>{t(spec.decisionKey)}</small>
                </button>
              );
            })}
          </nav>

          <article className="handbook-article" data-testid={`reference-${selected.method.method_id}`}>
            <header className="handbook-article-header">
              <div>
                <p className="method-family">{t(`method.${selected.method.family}`)}</p>
                <h2>{t(selected.method.name_key)}</h2>
                <p className="handbook-article-lead">{t(selected.spec.overviewKey)}</p>
              </div>
              <div className="handbook-method-badges" aria-label={t('reference.qualified_basis')}>
                <span>{selected.method.hcm_edition}</span>
                <span>{selected.method.supported_unit_systems.join(' / ')}</span>
              </div>
            </header>

            <div className="handbook-when-grid">
              <section className="handbook-callout handbook-callout-use">
                <h3>{t('reference.use_when')}</h3>
                <p>{t(selected.spec.useKey)}</p>
              </section>
              <section className="handbook-callout handbook-callout-avoid">
                <h3>{t('reference.avoid_when')}</h3>
                <p>{t(selected.spec.avoidKey)}</p>
              </section>
            </div>

            <section className="handbook-section">
              <div className="handbook-section-heading">
                <span>01</span>
                <div><h3>{t('reference.prepare_title')}</h3><p>{t('reference.prepare_description')}</p></div>
              </div>
              <ul className="handbook-checklist">
                {selected.spec.prepareKeys.map((key) => <li key={key}>{t(key)}</li>)}
              </ul>
            </section>

            <section className="handbook-section">
              <div className="handbook-section-heading">
                <span>02</span>
                <div><h3>{t('reference.key_inputs_title')}</h3><p>{t('reference.key_inputs_description')}</p></div>
              </div>
              <dl className="handbook-glossary">
                {selected.spec.glossaryItems.map((item) => (
                  <div key={item.termKey}>
                    <dt>{t(item.termKey)}</dt>
                    <dd>{t(item.descriptionKey)}</dd>
                  </div>
                ))}
              </dl>
            </section>

            <section className="handbook-section">
              <div className="handbook-section-heading">
                <span>03</span>
                <div><h3>{t('reference.workflow_title')}</h3><p>{t('reference.workflow_description')}</p></div>
              </div>
              <ol className="handbook-steps">
                {selected.spec.stepKeys.map((key, index) => (
                  <li key={key}><span>{index + 1}</span><p>{t(key)}</p></li>
                ))}
              </ol>
            </section>

            <section className="handbook-section">
              <div className="handbook-section-heading">
                <span>04</span>
                <div><h3>{t('reference.results_title')}</h3><p>{t('reference.results_description')}</p></div>
              </div>
              <div className="handbook-results-grid">
                <div>
                  <h4>{t('reference.outputs_title')}</h4>
                  <ul>{selected.spec.outputKeys.map((key) => <li key={key}>{t(key)}</li>)}</ul>
                </div>
                <div>
                  <h4>{t('reference.interpretation_title')}</h4>
                  <ul>{selected.spec.interpretationKeys.map((key) => <li key={key}>{t(key)}</li>)}</ul>
                </div>
              </div>
            </section>

            <section className="handbook-section">
              <div className="handbook-section-heading">
                <span>05</span>
                <div><h3>{t('reference.limits_title')}</h3><p>{t('reference.limits_description')}</p></div>
              </div>
              <ul className="handbook-limit-list">
                {selected.spec.limitKeys.map((key) => <li key={key}>{t(key)}</li>)}
              </ul>
            </section>

            <section className="handbook-source-card">
              <h3>{t('reference.source_title')}</h3>
              <dl className="reference-facts handbook-facts">
                <div><dt>{t('reference.chapter')}</dt><dd>{selected.method.chapter_reference}</dd></div>
                <div><dt>{t('reference.scope')}</dt><dd>{scopeFor(selected.method, t)}</dd></div>
                <div><dt>{t('reference.units')}</dt><dd>{selected.method.supported_unit_systems.join(' / ')}</dd></div>
              </dl>
              <div className="reference-actions">
                <button
                  className="button button-primary"
                  type="button"
                  disabled={!isMethodRouteEligible(selected.method, getFrontendModule(selected.method.method_id))}
                  onClick={() => onSelect(selected.method.method_id)}
                >
                  {t('action.start_analysis')}
                </button>
              </div>
            </section>

            <DetailsDisclosure title={t('reference.technical_title')}>
              <dl className="technical-facts">
                <div><dt>{t('reference.method_identifier')}</dt><dd><code>{selected.method.method_identifier}</code></dd></div>
                <div><dt>{t('reference.engine_identifier')}</dt><dd><code>{selected.method.engine_method_identifier}</code></dd></div>
                <div><dt>{t('reference.method_version')}</dt><dd><code>{selected.method.method_version}</code></dd></div>
                <div><dt>{t('reference.contract')}</dt><dd><code>{selected.method.input_contract}</code></dd></div>
              </dl>
            </DetailsDisclosure>
          </article>
        </div>
      ) : null}
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
  const referenceMethod = (methodId = '') => requestNavigation({ page: 'reference', methodId: methodId || null, scenarioEdit: null });
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
      {page === 'reference' ? <ReferencePage methods={methods} loading={loading} selectedMethodId={selectedMethodId} onReferenceSelect={referenceMethod} onSelect={selectMethod} /> : null}
    </AppShell>
  );
}
