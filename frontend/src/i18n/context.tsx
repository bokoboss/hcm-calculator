import { createContext, useContext, useEffect, useMemo, useState, type ReactElement, type ReactNode } from 'react';
import type { Locale } from '../api/types';
import { translate } from './catalog';

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string, values?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }): ReactElement {
  const [locale, setLocale] = useState<Locale>('en');
  useEffect(() => {
    document.documentElement.lang = locale === 'th' ? 'th' : 'en';
    document.title = translate(locale, 'app.title');
  }, [locale]);
  const value = useMemo<I18nContextValue>(
    () => ({ locale, setLocale, t: (key, values) => translate(locale, key, values) }),
    [locale],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const value = useContext(I18nContext);
  if (!value) throw new Error('useI18n must be used inside I18nProvider');
  return value;
}
