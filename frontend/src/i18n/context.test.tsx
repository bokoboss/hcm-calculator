import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider, useI18n } from './context';

function LocaleProbe() {
  const { locale, setLocale, t } = useI18n();
  return (
    <div>
      <span>{locale}</span>
      <span>{t('home.title')}</span>
      <button type="button" onClick={() => setLocale('th')}>ไทย</button>
    </div>
  );
}

describe('i18n foundation', () => {
  it('updates document metadata and catalog-backed UI language', async () => {
    render(<I18nProvider><LocaleProbe /></I18nProvider>);
    expect(document.documentElement.lang).toBe('en');
    expect(document.title).toBe('HCM Analysis Workspace');

    screen.getByRole('button', { name: 'ไทย' }).click();
    expect(await screen.findByText('th')).toBeInTheDocument();
    expect(screen.getByText('การวิเคราะห์ความจุทางหลวง')).toBeInTheDocument();
    expect(document.documentElement.lang).toBe('th');
    expect(document.title).toBe('พื้นที่ทำงานวิเคราะห์ HCM');
  });
});
