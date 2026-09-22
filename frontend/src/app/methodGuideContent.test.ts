import { describe, expect, it } from 'vitest';
import { catalogs } from '../i18n/catalog';
import { frontendModuleRegistry } from '../registry/modules';
import { methodGuideIds, methodGuideSpecs } from './methodGuideContent';

describe('HCM analysis handbook content', () => {
  it('covers every delivered frontend workflow exactly once', () => {
    expect([...methodGuideIds].sort()).toEqual(Object.keys(frontendModuleRegistry).sort());
  });

  it('provides complete bilingual actionable guidance for every workflow', () => {
    for (const spec of Object.values(methodGuideSpecs)) {
      const keys = [
        spec.decisionKey,
        spec.useKey,
        spec.avoidKey,
        ...spec.prepareKeys,
        ...spec.outputKeys,
        ...spec.limitKeys,
      ];
      expect(spec.prepareKeys.length).toBeGreaterThanOrEqual(3);
      expect(spec.outputKeys.length).toBeGreaterThanOrEqual(2);
      expect(spec.limitKeys.length).toBeGreaterThanOrEqual(2);
      for (const key of keys) {
        expect(catalogs.en[key]).toBeTruthy();
        expect(catalogs.th[key]).toBeTruthy();
      }
    }
  });
});
