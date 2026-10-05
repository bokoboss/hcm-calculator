import { useRef, type ReactElement } from 'react';
import { useI18n } from '../i18n';

/** Keeps list items as numeric JSON values; empty items remain explicit nulls
 * for backend validation. No method-specific parsing or engineering defaults. */
export function NumberListEditor({ id, label, value, unit, required, error, onChange, onTouched }: {
  id: string;
  label: string;
  value: unknown;
  unit: string;
  required?: boolean;
  error?: string;
  onChange: (value: Array<number | null>) => void;
  onTouched: () => void;
}): ReactElement {
  const { t } = useI18n();
  const root = useRef<HTMLFieldSetElement>(null);
  const items: Array<number | null> = Array.isArray(value) ? value : [];
  const errorId = error ? `${id}-error` : undefined;
  const focusItem = (index: number) => window.requestAnimationFrame(() => {
    const controls = root.current?.querySelectorAll<HTMLInputElement>('input');
    (controls?.[index] ?? root.current?.querySelector<HTMLButtonElement>('button'))?.focus();
  });
  return <fieldset ref={root} id={id} tabIndex={-1} className="number-list-editor" aria-describedby={errorId} aria-invalid={error ? 'true' : undefined}>
    <legend>{label} {required ? <span className="required-mark">{t('form.required')}</span> : null}</legend>
    {items.length ? <ol>{items.map((item, index) => <li key={index}>
      <label htmlFor={`${id}-${index}`}>{t('form.list_item', { number: index + 1 })} <span>{unit}</span></label>
      <div className="number-list-row">
        <input id={`${id}-${index}`} type="number" step="any" value={item ?? ''} aria-describedby={errorId} aria-invalid={error ? 'true' : undefined} aria-label={`${label} — ${t('form.list_item', { number: index + 1 })} (${unit})`} onBlur={onTouched} onChange={(event) => {
          const next = [...items];
          next[index] = event.target.value === '' ? null : event.target.valueAsNumber;
          onChange(next);
        }} />
        <button type="button" className="button button-secondary" aria-label={t('form.list_remove', { number: index + 1, field: label })} onClick={() => {
          onTouched();
          onChange(items.filter((_, itemIndex) => itemIndex !== index));
          focusItem(Math.max(0, index - 1));
        }}>{t('form.remove_item')}</button>
      </div>
    </li>)}</ol> : <p className="field-hint">{t('form.list_empty')}</p>}
    <button type="button" className="button button-secondary" aria-label={t('form.list_add', { field: label })} onClick={() => {
      onTouched();
      onChange([...items, null]);
      focusItem(items.length);
    }}>{t('form.add_item')}</button>
    {error ? <span id={errorId} className="field-error" role="alert">{error}</span> : null}
  </fieldset>;
}
