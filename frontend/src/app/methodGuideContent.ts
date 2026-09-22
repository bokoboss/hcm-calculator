export interface MethodGuideSpec {
  methodId: string;
  decisionKey: string;
  useKey: string;
  avoidKey: string;
  prepareKeys: readonly string[];
  outputKeys: readonly string[];
  limitKeys: readonly string[];
}

function guide(
  methodId: string,
  prepareCount = 3,
  outputCount = 2,
  limitCount = 2,
): MethodGuideSpec {
  const prefix = `guide.${methodId}`;
  return {
    methodId,
    decisionKey: `${prefix}.decision`,
    useKey: `${prefix}.use`,
    avoidKey: `${prefix}.avoid`,
    prepareKeys: Array.from({ length: prepareCount }, (_, index) => `${prefix}.prepare.${index + 1}`),
    outputKeys: Array.from({ length: outputCount }, (_, index) => `${prefix}.output.${index + 1}`),
    limitKeys: Array.from({ length: limitCount }, (_, index) => `${prefix}.limit.${index + 1}`),
  };
}

export const methodGuideSpecs: Readonly<Record<string, MethodGuideSpec>> = {
  two_lane_segment: guide('two_lane_segment'),
  two_lane_facility: guide('two_lane_facility'),
  multilane_segment: guide('multilane_segment'),
  basic_freeway_segment: guide('basic_freeway_segment'),
  weaving_segment: guide('weaving_segment'),
  merge_segment: guide('merge_segment'),
  diverge_segment: guide('diverge_segment'),
};

export const methodGuideIds = Object.freeze(Object.keys(methodGuideSpecs));
