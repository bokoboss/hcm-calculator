import { describe, expect, it } from 'vitest';
import { catalogs } from '../i18n/catalog';
import { frontendModuleRegistry } from '../registry/modules';
import { methodGuideIds, methodGuideSpecs } from './methodGuideContent';

describe('HCM analysis handbook content', () => {
  it('provides an LHT production guide with six glossary entries and seven steps', () => {
    expect(methodGuideSpecs.urban_street_segment_th_lht).toBeDefined();
    expect(methodGuideSpecs.urban_street_segment_th_lht?.glossaryItems).toHaveLength(6);
    expect(methodGuideSpecs.urban_street_segment_th_lht?.stepKeys).toHaveLength(7);
  });
  it('covers every delivered frontend workflow exactly once', () => {
    expect([...methodGuideIds].sort()).toEqual(Object.keys(frontendModuleRegistry).sort());
  });

  it('provides complete bilingual actionable guidance for every workflow', () => {
    for (const spec of Object.values(methodGuideSpecs)) {
      const keys = [
        spec.decisionKey,
        spec.overviewKey,
        spec.useKey,
        spec.avoidKey,
        ...spec.prepareKeys,
        ...spec.glossaryItems.flatMap((item) => [item.termKey, item.descriptionKey]),
        ...spec.stepKeys,
        ...spec.outputKeys,
        ...spec.interpretationKeys,
        ...spec.limitKeys,
      ];
      expect(spec.prepareKeys.length).toBeGreaterThanOrEqual(3);
      expect(spec.glossaryItems.length).toBeGreaterThanOrEqual(4);
      expect(spec.stepKeys.length).toBeGreaterThanOrEqual(4);
      expect(spec.outputKeys.length).toBeGreaterThanOrEqual(2);
      expect(spec.interpretationKeys.length).toBeGreaterThanOrEqual(2);
      expect(spec.limitKeys.length).toBeGreaterThanOrEqual(2);
      for (const key of keys) {
        expect(catalogs.en[key]).toBeTruthy();
        expect(catalogs.th[key]).toBeTruthy();
      }
    }
  });
});
