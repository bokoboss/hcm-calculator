export interface MethodGuideGlossaryItem {
  termKey: string;
  descriptionKey: string;
}

export interface MethodGuideSpec {
  methodId: string;
  decisionKey: string;
  overviewKey: string;
  useKey: string;
  avoidKey: string;
  prepareKeys: readonly string[];
  glossaryItems: readonly MethodGuideGlossaryItem[];
  stepKeys: readonly string[];
  outputKeys: readonly string[];
  interpretationKeys: readonly string[];
  limitKeys: readonly string[];
}

function numberedKeys(prefix: string, count: number): string[] {
  return Array.from({ length: count }, (_, index) => `${prefix}.${index + 1}`);
}

function glossary(prefix: string, count: number): MethodGuideGlossaryItem[] {
  return Array.from({ length: count }, (_, index) => ({
    termKey: `${prefix}.term.${index + 1}`,
    descriptionKey: `${prefix}.description.${index + 1}`,
  }));
}

function guide(
  methodId: string,
  glossaryCount = 4,
  stepCount = 5,
  prepareCount = 3,
  outputCount = 2,
  interpretationCount = 3,
  limitCount = 2,
): MethodGuideSpec {
  const prefix = `guide.${methodId}`;
  return {
    methodId,
    decisionKey: `${prefix}.decision`,
    overviewKey: `${prefix}.overview`,
    useKey: `${prefix}.use`,
    avoidKey: `${prefix}.avoid`,
    prepareKeys: numberedKeys(`${prefix}.prepare`, prepareCount),
    glossaryItems: glossary(`${prefix}.glossary`, glossaryCount),
    stepKeys: numberedKeys(`${prefix}.step`, stepCount),
    outputKeys: numberedKeys(`${prefix}.output`, outputCount),
    interpretationKeys: numberedKeys(`${prefix}.interpretation`, interpretationCount),
    limitKeys: numberedKeys(`${prefix}.limit`, limitCount),
  };
}

export const methodGuideSpecs: Readonly<Record<string, MethodGuideSpec>> = {
  two_lane_segment: guide('two_lane_segment', 4),
  two_lane_facility: guide('two_lane_facility', 4),
  multilane_segment: guide('multilane_segment', 4),
  basic_freeway_segment: guide('basic_freeway_segment', 4),
  weaving_segment: guide('weaving_segment', 5),
  merge_segment: guide('merge_segment', 5),
  diverge_segment: guide('diverge_segment', 5),
};

export const methodGuideIds = Object.freeze(Object.keys(methodGuideSpecs));
