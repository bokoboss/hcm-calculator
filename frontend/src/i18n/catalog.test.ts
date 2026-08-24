import { describe, expect, it } from 'vitest';
import { translate } from './catalog';

describe('frontend localization foundation', () => {
  it('provides shell vocabulary in both supported locales', () => {
    expect(translate('en', 'app.title')).toBe('HCM Analysis Workspace');
    expect(translate('th', 'app.title')).toContain('HCM');
    expect(translate('th', 'action.new_analysis')).not.toBe(translate('en', 'action.new_analysis'));
  });

  it('keeps unknown keys safe and substitutes placeholders', () => {
    expect(translate('en', 'new_analysis.available_count', { count: 0 })).toContain('0');
    expect(translate('en', 'missing.key')).toBe('missing.key');
  });
});
