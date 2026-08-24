import { useEffect, useMemo, useState, type ReactElement } from 'react';
import { fetchMethods } from '../api/client';
import type { MethodDefinition } from '../api/types';
import { getActionableMethods, getFrontendModule } from '../registry/modules';
import { useI18n } from '../i18n';
import {
  AppShell,
  DetailsDisclosure,
  EngineeringAssessment,
  EngineeringSection,
  PageHeader,
  ResultHero,
  ScopeNotice,
  StatusBadge,
  type PageId,
} from '../components/primitives';

function MethodCard({
  method,
  onReference,
}: {
  method: MethodDefinition;
  onReference: (methodId: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const module = getFrontendModule(method.method_id);
  const delivered = module?.status === 'delivered';
  return (
    <article className="method-card" data-testid={`method-card-${method.method_id}`}>
      <div className="method-card-heading">
        <div>
          <p className="method-family">{t(`method.${method.family}`)}</p>
          <h3>{t(method.name_key)}</h3>
        </div>
        <StatusBadge tone={delivered ? 'current' : 'neutral'}>{delivered ? t('action.select_method') : t('new_analysis.reference_only')}</StatusBadge>
      </div>
      <p>{t(method.description_key)}</p>
      <dl className="method-meta">
        <div><dt>{t('reference.chapter')}</dt><dd>{method.chapter_reference}</dd></div>
        <div><dt>{t('reference.units')}</dt><dd>{method.supported_unit_systems.join(' / ')}</dd></div>
      </dl>
      <div className="method-card-actions">
        <button className="button button-secondary" type="button" disabled={!delivered} aria-disabled={!delivered}>
          {t('action.select_method')}
        </button>
        <button className="button button-link" type="button" onClick={() => onReference(method.method_id)}>
          {t('action.view_reference')}
        </button>
      </div>
      {!delivered ? <p className="method-legacy-note">{t('new_analysis.legacy_note')}</p> : null}
    </article>
  );
}

function HomePage({ onNavigate }: { onNavigate: (page: PageId) => void }): ReactElement {
  const { t } = useI18n();
  return (
    <div className="page-stack">
      <PageHeader eyebrow={t('app.eyebrow')} title={t('home.title')} description={t('app.description')} />
      <div className="home-actions">
        <EngineeringSection title={t('home.quick_title')} description={t('home.quick_description')}>
          <button className="button button-primary" type="button" onClick={() => onNavigate('new-analysis')}>{t('action.new_analysis')}</button>
        </EngineeringSection>
        <EngineeringSection title={t('home.project_title')} description={t('home.project_description')}>
          <button className="button button-secondary" type="button" disabled aria-disabled="true">{t('action.new_project')}</button>
        </EngineeringSection>
      </div>
      <ScopeNotice title={t('home.status_label')}>{t('home.foundation_note')}</ScopeNotice>
      <div className="foundation-summary">
        <span className="summary-kicker">{t('home.status_label')}</span>
        <strong>{t('home.status_value')}</strong>
        <span className="summary-rule" aria-hidden="true" />
        <button className="button button-link" type="button" onClick={() => onNavigate('reference')}>{t('nav.reference')}</button>
      </div>
    </div>
  );
}

function NewAnalysisPage({
  methods,
  loading,
  onReference,
}: {
  methods: MethodDefinition[];
  loading: boolean;
  onReference: (methodId: string) => void;
}): ReactElement {
  const { t } = useI18n();
  const actionable = useMemo(() => getActionableMethods(methods), [methods]);
  const grouped = useMemo(() => {
    const groups = new Map<string, MethodDefinition[]>();
    methods.forEach((method) => groups.set(method.family, [...(groups.get(method.family) ?? []), method]));
    return [...groups.entries()];
  }, [methods]);
  return (
    <div className="page-stack">
      <PageHeader eyebrow={t('new_analysis.eyebrow')} title={t('new_analysis.title')} description={t('new_analysis.description')} />
      <div className="delivery-summary" role="status"><span className="delivery-count">{actionable.length}</span><span>{t('new_analysis.available_count', { count: actionable.length })}</span></div>
      {loading ? <ScopeNotice title={t('new_analysis.loading_title')}>{t('status.loading')} backend method metadata…</ScopeNotice> : null}
      {!loading && !methods.length ? <ScopeNotice title={t('status.no_methods')} tone="warning">{t('reference.api_error')}</ScopeNotice> : null}
      {grouped.map(([family, familyMethods]) => (
        <EngineeringSection title={t(`method.${family}`)} key={family}>
          <div className="method-grid">
            {familyMethods.map((method) => <MethodCard method={method} onReference={onReference} key={method.method_id} />)}
          </div>
        </EngineeringSection>
      ))}
    </div>
  );
}

function ReferencePage({
  methods,
  loading,
}: {
  methods: MethodDefinition[];
  loading: boolean;
}): ReactElement {
  const { t } = useI18n();
  return (
    <div className="page-stack">
      <PageHeader eyebrow={t('reference.eyebrow')} title={t('reference.title')} description={t('reference.description')} />
      {loading ? <ScopeNotice title={t('new_analysis.loading_title')}>{t('status.loading')} backend method metadata…</ScopeNotice> : null}
      <div className="reference-list">
        {methods.map((method) => {
          const module = getFrontendModule(method.method_id);
          return (
            <article className="reference-row" key={method.method_id} data-testid={`reference-${method.method_id}`}>
              <div className="reference-row-title"><p className="method-family">{t(`method.${method.family}`)}</p><h2>{t(method.name_key)}</h2><p>{t(method.description_key)}</p></div>
              <dl className="reference-facts">
                <div><dt>{t('reference.chapter')}</dt><dd>{method.chapter_reference}</dd></div>
                <div><dt>{t('reference.contract')}</dt><dd><code>{method.input_contract}</code></dd></div>
                <div><dt>{t('reference.frontend_status')}</dt><dd><StatusBadge tone="neutral">{module?.status === 'delivered' ? t('action.select_method') : t('reference.not_delivered')}</StatusBadge></dd></div>
              </dl>
            </article>
          );
        })}
      </div>
      <DetailsDisclosure title={t('reference.assessment_title')}>
        <EngineeringAssessment items={[
          t('reference.assessment_backend'),
          t('reference.assessment_frontend'),
          t('reference.assessment_r1'),
        ]} />
      </DetailsDisclosure>
      <ResultHero label={t('reference.result_label')} value={t('reference.result_value')} supporting={t('reference.result_supporting')} />
    </div>
  );
}

export function App(): ReactElement {
  const [page, setPage] = useState<PageId>('home');
  const [methods, setMethods] = useState<MethodDefinition[]>([]);
  const [loading, setLoading] = useState(true);
  const [apiConnected, setApiConnected] = useState(false);
  useEffect(() => {
    let active = true;
    fetchMethods()
      .then((response) => {
        if (!active) return;
        setMethods(response.methods);
        setApiConnected(true);
      })
      .catch(() => {
        if (active) setApiConnected(false);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, []);

  const referenceMethod = (methodId: string) => {
    setPage('reference');
    window.history.replaceState({}, '', `/reference/methods/${methodId}`);
  };

  return (
    <>
      <AppShell activePage={page} onNavigate={setPage} apiConnected={apiConnected}>
        {page === 'home' ? <HomePage onNavigate={setPage} /> : null}
        {page === 'new-analysis' ? <NewAnalysisPage methods={methods} loading={loading} onReference={referenceMethod} /> : null}
        {page === 'reference' ? <ReferencePage methods={methods} loading={loading} /> : null}
      </AppShell>
    </>
  );
}
