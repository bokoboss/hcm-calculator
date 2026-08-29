import { describe, expect, it } from 'vitest';
import { catalogs, translate } from './catalog';

const sharedPrimitiveKeys = [
  'accessibility.skip_to_main',
  'form.required',
  'form.errors_count',
  'analysis.eyebrow',
  'action.calculate',
  'action.recalculate',
  'status.ready_to_calculate',
  'status.items_required',
  'assessment.kicker',
  'state.stale_title',
  'state.stale_supporting',
  'state.capacity_title',
  'state.capacity_supporting',
  'state.handoff_title',
  'state.handoff_supporting',
] as const;

describe('localization catalog', () => {
  it('provides shell vocabulary in both supported locales', () => {
    expect(translate('en', 'app.title')).toBe('HCM Calculator');
    expect(translate('th', 'app.title')).toContain('HCM');
    expect(translate('th', 'action.new_analysis')).not.toBe(translate('en', 'action.new_analysis'));
  });

  it('contains every shared primitive/state key in English and Thai', () => {
    for (const key of sharedPrimitiveKeys) {
      expect(catalogs.en[key]).toBeTruthy();
      expect(catalogs.th[key]).toBeTruthy();
    }
  });

  it('interpolates localized error counts without a second translation system', () => {
    expect(translate('en', 'form.errors_count', { count: 2 })).toBe('2 items require attention');
    expect(translate('th', 'form.errors_count', { count: 2 })).toBe('ต้องแก้ไข 2 รายการ');
  });

  it('keeps unknown keys safe and substitutes placeholders', () => {
    expect(translate('en', 'new_analysis.available_count', { count: 0 })).toContain('0');
    expect(translate('en', 'missing.key')).toBe('missing.key');
  });
});
