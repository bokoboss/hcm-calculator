import {
  cloneElement,
  isValidElement,
  useId,
  useState,
  type ChangeEvent,
  type ReactElement,
  type ReactNode,
} from 'react';
import { useI18n } from '../i18n';

export type PageId = 'home' | 'new-analysis' | 'project' | 'reference';
export type MethodNavigationId =
  | 'two_lane_segment'
  | 'two_lane_facility'
  | 'multilane_segment'
  | 'basic_freeway_segment'
  | 'weaving_segment'
  | 'merge_segment'
  | 'diverge_segment';

export function AppHeader({
  onNavigate,
}: {
  onNavigate: (page: PageId) => void;
}): ReactElement {
  const { locale, setLocale, t } = useI18n();
  return (
    <header className="app-header" data-slot="app-header">
      <div className="brand-lockup">
        <span className="brand-mark" aria-hidden="true">HCM</span>
        <div>
          <p className="brand-kicker">{t('app.brand_kicker')}</p>
          <p className="brand-title">{t('app.brand_title')}</p>
        </div>
      </div>
      <div className="header-actions" aria-label={t('app.header_actions')}>
        <button className="button button-quiet" type="button" onClick={() => onNavigate('new-analysis')}>
          {t('action.new_analysis')}
        </button>
        <button className="button button-quiet" type="button" onClick={() => onNavigate('project')}>
          {t('action.open_project')}
        </button>
        <button className="button button-quiet" type="button" onClick={() => onNavigate('reference')}>
          {t('action.help')}
        </button>
        <div className="locale-switcher" aria-label={t('locale.label')}>
          <span>{t('locale.label')}</span>
          <button className={locale === 'en' ? 'locale-active' : ''} type="button" aria-pressed={locale === 'en'} onClick={() => setLocale('en')}>{t('locale.en')}</button>
          <span aria-hidden="true">/</span>
          <button className={locale === 'th' ? 'locale-active' : ''} type="button" aria-pressed={locale === 'th'} onClick={() => setLocale('th')}>{t('locale.th')}</button>
        </div>
      </div>
    </header>
  );
}

export function SidebarNavigation({
  activePage,
  activeMethodId,
  onNavigate,
  onSelectMethod,
}: {
  activePage: PageId;
  activeMethodId?: string | null;
  onNavigate: (page: PageId) => void;
  onSelectMethod?: (methodId: MethodNavigationId) => void;
}): ReactElement {
  const { t } = useI18n();
  const [mobileOpen, setMobileOpen] = useState(Boolean(activeMethodId));
  const methodGroups: Array<{ key: string; label: string; methods: Array<{ id: MethodNavigationId; label: string }> }> = [
    {
      key: 'roadways',
      label: t('nav.roadways'),
      methods: [
        { id: 'two_lane_segment', label: t('method.two_lane_segment.name') },
        { id: 'two_lane_facility', label: t('method.two_lane_facility.name') },
        { id: 'multilane_segment', label: t('method.multilane_segment.name') },
      ],
    },
    {
      key: 'freeways',
      label: t('nav.freeways'),
      methods: [
        { id: 'basic_freeway_segment', label: t('method.basic_freeway_segment.name') },
        { id: 'weaving_segment', label: t('method.weaving_segment.name') },
        { id: 'merge_segment', label: t('method.merge_segment.name') },
        { id: 'diverge_segment', label: t('method.diverge_segment.name') },
      ],
    },
  ];
  const methodButton = (method: { id: MethodNavigationId; label: string }) => {
    const active = activeMethodId === method.id;
    return (
      <button
        className={`nav-item nav-method-item ${active ? 'nav-item-active' : ''}`}
        type="button"
        aria-current={active ? 'page' : undefined}
        data-testid={`nav-method-${method.id}`}
        onClick={() => onSelectMethod?.(method.id)}
        key={method.id}
      >
        <span className="nav-dot" aria-hidden="true" /> {method.label}
      </button>
    );
  };
  return (
    <aside className="app-sidebar" data-slot="sidebar-navigation">
      <nav aria-label={t('nav.workspace')}>
        <p className="sidebar-group-label">{t('nav.workspace_group')}</p>
        <button
          className={`nav-item ${activePage === 'home' ? 'nav-item-active' : ''}`}
          type="button"
          aria-current={activePage === 'home' ? 'page' : undefined}
          onClick={() => onNavigate('home')}
        >
          <span className="nav-dot" aria-hidden="true" /> {t('nav.home')}
        </button>
        <button
          className={`nav-item ${activePage === 'project' ? 'nav-item-active' : ''}`}
          type="button"
          aria-current={activePage === 'project' ? 'page' : undefined}
          onClick={() => onNavigate('project')}
        >
          <span className="nav-dot" aria-hidden="true" /> {t('nav.project_workspace')}
        </button>
        <button
          className={`nav-item ${activePage === 'new-analysis' && !activeMethodId ? 'nav-item-active' : ''}`}
          type="button"
          aria-current={activePage === 'new-analysis' && !activeMethodId ? 'page' : undefined}
          onClick={() => onNavigate('new-analysis')}
        >
          <span className="nav-dot" aria-hidden="true" /> {t('nav.new_analysis')}
        </button>
        <div className="desktop-method-nav" aria-label={t('nav.method_navigation')}>
          {methodGroups.map((group) => (
            <div key={group.key}>
              <p className="sidebar-group-label">{group.label}</p>
              {group.methods.map(methodButton)}
            </div>
          ))}
        </div>
        <details
          className="mobile-method-nav"
          open={mobileOpen}
          onToggle={(event) => setMobileOpen(event.currentTarget.open)}
        >
          <summary>{t('nav.method_selector')}</summary>
          <div className="mobile-method-nav-content">
            {methodGroups.map((group) => (
              <div key={group.key}>
                <p className="sidebar-group-label">{group.label}</p>
                {group.methods.map(methodButton)}
              </div>
            ))}
          </div>
        </details>
        <p className="sidebar-group-label">{t('nav.reference_group')}</p>
        <button
          className={`nav-item ${activePage === 'reference' ? 'nav-item-active' : ''}`}
          type="button"
          aria-current={activePage === 'reference' ? 'page' : undefined}
          onClick={() => onNavigate('reference')}
        >
          <span className="nav-dot" aria-hidden="true" /> {t('nav.reference')}
        </button>
      </nav>
      <div className="sidebar-note">
        <span className="status-dot" aria-hidden="true" />
        <span>{t('status.local_runtime')}</span>
      </div>
    </aside>
  );
}

export function StatusBar({ apiConnected }: { apiConnected: boolean }): ReactElement {
  const { t } = useI18n();
  return (
    <footer className="status-bar" data-slot="status-bar" aria-live="polite">
      <span className="status-item"><span className="status-dot" aria-hidden="true" /> {t('status.ready')}</span>
      <span className="status-divider" aria-hidden="true" />
      <span className="status-item">{t('app.eyebrow')}</span>
      <span className="status-divider" aria-hidden="true" />
      <span className="status-item">{apiConnected ? t('status.api_connected') : t('status.api_unavailable')}</span>
      <span className="status-spacer" />
      <span className="status-item">{t('status.units')}</span>
    </footer>
  );
}

export function AppShell({
  activePage,
  activeMethodId,
  onNavigate,
  onSelectMethod,
  apiConnected,
  children,
}: {
  activePage: PageId;
  activeMethodId?: string | null;
  onNavigate: (page: PageId) => void;
  onSelectMethod?: (methodId: MethodNavigationId) => void;
  apiConnected: boolean;
  children: ReactNode;
}): ReactElement {
  const { t } = useI18n();
  return (
    <div className="app-shell" data-slot="app-shell">
      <a className="skip-link" href="#main-content">{t('accessibility.skip_to_main')}</a>
      <AppHeader onNavigate={onNavigate} />
      <div className="app-shell-layout">
        <SidebarNavigation activePage={activePage} activeMethodId={activeMethodId} onNavigate={onNavigate} onSelectMethod={onSelectMethod} />
        <main className="app-main" id="main-content">{children}</main>
      </div>
      <StatusBar apiConnected={apiConnected} />
    </div>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}): ReactElement {
  return (
    <header className="page-header" data-slot="page-header">
      {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
      <h1>{title}</h1>
      {description ? <p className="page-description">{description}</p> : null}
    </header>
  );
}

export function AnalysisHeader({
  title,
  method,
  status,
  context,
  tone = 'neutral',
}: {
  title: string;
  method: string;
  status?: string;
  context?: string;
  tone?: 'current' | 'warning' | 'stale' | 'neutral' | 'capacity';
}): ReactElement {
  const { t } = useI18n();
  const displayedStatus = status ?? t('status.current');
  return (
    <div className="analysis-header" data-slot="analysis-header">
      <div>
        <p className="eyebrow">{t('analysis.eyebrow')}</p>
        <h2>{title}</h2>
        <p className="muted">{method}</p>
        {context ? <p className="analysis-context">{context}</p> : null}
      </div>
      <StatusBadge tone={tone}>{displayedStatus}</StatusBadge>
    </div>
  );
}

export function EngineeringSection({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}): ReactElement {
  const headingId = useId();
  return (
    <section className="engineering-section" data-slot="engineering-section" aria-labelledby={headingId}>
      <div className="section-heading">
        <h2 id={headingId}>{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      <div className="section-body">{children}</div>
    </section>
  );
}

export interface FieldControlProps {
  id: string;
  'aria-describedby'?: string;
  'aria-invalid'?: 'true';
  'aria-required'?: 'true';
  required?: boolean;
}

type FieldControl = ReactNode | ((props: FieldControlProps) => ReactNode);

export function Field({
  id,
  label,
  htmlFor,
  required = false,
  hint,
  error,
  children,
}: {
  id?: string;
  label: string;
  htmlFor?: string;
  required?: boolean;
  hint?: string;
  error?: string;
  children: FieldControl;
}): ReactElement {
  const { t } = useI18n();
  const generatedId = useId();
  const controlId = id ?? htmlFor ?? `field-${generatedId.replaceAll(':', '')}`;
  const hintId = hint ? `${controlId}-hint` : undefined;
  const errorId = error ? `${controlId}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined;
  const controlProps: FieldControlProps = {
    id: controlId,
    'aria-describedby': describedBy,
    'aria-invalid': error ? 'true' : undefined,
    'aria-required': required ? 'true' : undefined,
    required: required || undefined,
  };
  const control = typeof children === 'function'
    ? children(controlProps)
    : isValidElement(children)
      ? cloneElement(
        children as ReactElement<Record<string, unknown>>,
        controlProps as unknown as Partial<Record<string, unknown>>,
      )
      : children;
  return (
    <div className={`field ${error ? 'field-invalid' : ''}`} data-slot="field">
      <label htmlFor={controlId} className="field-label">
        {label} {required ? <span className="required-mark">{t('form.required')}</span> : null}
      </label>
      {control}
      {hint && hintId ? <span className="field-hint" id={hintId}>{hint}</span> : null}
      {error && errorId ? <span className="field-error" id={errorId} role="alert">{error}</span> : null}
    </div>
  );
}

export function InputWithUnit({
  id,
  unit,
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
  invalid = false,
  describedBy,
  'aria-describedby': ariaDescribedBy,
  'aria-invalid': ariaInvalid,
  'aria-required': ariaRequired,
  required = false,
}: {
  id: string;
  unit: string;
  value?: string | number;
  onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
  type?: 'text' | 'number';
  placeholder?: string;
  disabled?: boolean;
  invalid?: boolean;
  describedBy?: string;
  'aria-describedby'?: string;
  'aria-invalid'?: boolean | 'false' | 'true';
  'aria-required'?: boolean | 'false' | 'true';
  required?: boolean;
}): ReactElement {
  return (
    <div className="input-unit" data-slot="input-with-unit">
      <input
        id={id}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required || undefined}
        aria-invalid={invalid ? 'true' : ariaInvalid || undefined}
        aria-describedby={describedBy ?? ariaDescribedBy}
        aria-required={ariaRequired || undefined}
      />
      <span className="unit-label" aria-hidden="true">{unit}</span>
    </div>
  );
}

export function ChoiceGroup({
  legend,
  name,
  options,
  value,
  onChange,
  error,
}: {
  legend: string;
  name: string;
  options: Array<{ value: string; label: string; description?: string }>;
  value?: string;
  onChange?: (value: string) => void;
  error?: string;
}): ReactElement {
  return (
    <fieldset className={`choice-group ${error ? 'choice-group-invalid' : ''}`} data-slot="choice-group" aria-invalid={error ? 'true' : undefined}>
      <legend>{legend}</legend>
      <div className="choice-options">
        {options.map((option) => (
          <label className="choice-option" key={option.value}>
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={() => onChange?.(option.value)}
            />
            <span>
              <strong>{option.label}</strong>
              {option.description ? <small>{option.description}</small> : null}
            </span>
          </label>
        ))}
      </div>
      {error ? <span className="field-error" role="alert">{error}</span> : null}
    </fieldset>
  );
}

export function ScopeNotice({
  title,
  children,
  tone = 'info',
}: {
  title: string;
  children: ReactNode;
  tone?: 'info' | 'warning' | 'neutral';
}): ReactElement {
  return <aside className={`scope-notice scope-notice-${tone}`} data-slot="scope-notice"><strong>{title}</strong><span>{children}</span></aside>;
}

export function ErrorSummary({
  errors,
}: {
  errors: Array<string | { message: string; targetId?: string }>;
}): ReactElement | null {
  const { t } = useI18n();
  if (!errors.length) return null;
  return <div className="error-summary" id="error-summary" data-slot="error-summary" role="alert" tabIndex={-1}><strong>{t('form.errors_count', { count: errors.length })}</strong><ul>{errors.map((error, index) => {
    const message = typeof error === 'string' ? error : error.message;
    const targetId = typeof error === 'string' ? undefined : error.targetId;
    return <li key={`${message}-${index}`}>{targetId ? <a href={`#${targetId}`} onClick={(event) => {
      const target = document.getElementById(targetId);
      if (!target) return;
      event.preventDefault();
      target.focus();
      target.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }}>{message}</a> : message}</li>;
  })}</ul></div>;
}

export function ReadinessBar({
  ready,
  actionLabel,
  onAction,
  disabled = false,
}: {
  ready: boolean;
  actionLabel?: string;
  onAction?: () => void;
  disabled?: boolean;
}): ReactElement {
  const { t } = useI18n();
  const displayedActionLabel = actionLabel ?? t('action.calculate');
  return <div className="readiness-bar" data-slot="readiness-bar"><span className={ready ? 'readiness-ready' : 'readiness-blocked'}>{ready ? `✓ ${t('status.ready_to_calculate')}` : t('status.items_required')}</span><button className="button button-primary" type="button" disabled={disabled || !ready} onClick={onAction}>{displayedActionLabel}</button></div>;
}

export function ResultHero({
  label,
  value,
  supporting,
  state = 'current',
}: {
  label: string;
  value: string;
  supporting?: string;
  state?: 'current' | 'warning' | 'stale' | 'capacity' | 'handoff';
}): ReactElement {
  return <section className={`result-hero result-hero-${state}`} data-slot="result-hero"><p className="result-label">{label}</p><p className="result-value">{value}</p>{supporting ? <p className="result-supporting">{supporting}</p> : null}</section>;
}

export function MetricCard({
  label,
  value,
  unit,
}: {
  label: string;
  value: string;
  unit?: string;
}): ReactElement {
  return <article className="metric-card" data-slot="metric-card"><p>{label}</p><strong>{value}</strong>{unit ? <span>{unit}</span> : null}</article>;
}

export function EngineeringAssessment({
  items,
}: {
  items: string[];
}): ReactElement {
  const { t } = useI18n();
  return <section className="assessment-panel" data-slot="engineering-assessment"><p className="section-label">{t('assessment.kicker')}</p><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></section>;
}

export function StatusBadge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'current' | 'warning' | 'stale' | 'neutral' | 'capacity';
}): ReactElement {
  return <span className={`status-badge status-badge-${tone}`} data-slot="status-badge">{children}</span>;
}

export function DetailsDisclosure({
  title,
  children,
  defaultOpen = false,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}): ReactElement {
  const [open, setOpen] = useState(defaultOpen);
  const contentId = useId();
  return <div className="details-disclosure" data-slot="details-disclosure"><button className="disclosure-trigger" type="button" aria-expanded={open} aria-controls={contentId} onClick={() => setOpen((current) => !current)}><span>{title}</span><span aria-hidden="true">{open ? '−' : '+'}</span></button>{open ? <div className="disclosure-content" id={contentId}>{children}</div> : null}</div>;
}

export function StaleResultBanner({ onRecalculate }: { onRecalculate?: () => void }): ReactElement {
  const { t } = useI18n();
  return <div className="stale-banner" data-slot="stale-result-banner" role="status"><div><strong>{t('state.stale_title')}</strong><span>{t('state.stale_supporting')}</span><span className="stale-export-note">{t('result.export_stale_reason')}</span></div><div className="stale-action-readiness readiness-bar" data-slot="readiness-bar"><button className="button button-primary" type="button" onClick={onRecalculate}>{t('action.recalculate')}</button></div></div>;
}

export function CapacityFailurePanel({ metricsUnavailable = true }: { metricsUnavailable?: boolean } = {}): ReactElement {
  const { t } = useI18n();
  return <section className="state-panel state-panel-capacity" data-slot="capacity-failure-panel"><strong>{t('state.capacity_title')}</strong><span>{metricsUnavailable ? t('state.capacity_supporting') : t('state.capacity_calculated_supporting')}</span></section>;
}

export function HandoffPanel(): ReactElement {
  const { t } = useI18n();
  return <section className="state-panel state-panel-handoff" data-slot="handoff-panel"><strong>{t('state.handoff_title')}</strong><span>{t('state.handoff_supporting')}</span></section>;
}

export function WarningPanel({ message }: { message?: string | null } = {}): ReactElement {
  const { t } = useI18n();
  return <section className="state-panel state-panel-warning" data-slot="warning-panel" role="status"><strong>{t('state.warning_title')}</strong><span>{message || t('state.warning_supporting')}</span></section>;
}
