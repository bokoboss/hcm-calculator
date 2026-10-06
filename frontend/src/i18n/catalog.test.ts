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
  'status.local_runtime',
  'status.vercel_runtime',
  'status.hosted_runtime',
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

  it('provides every rendered Facility column and remediation label in both locales', () => {
    const facilityColumns = [
      'segment_id', 'segment_name', 'segment_type', 'segment_length', 'posted_speed',
      'analysis_direction_volume_veh_h', 'opposing_direction_volume_veh_h', 'peak_hour_factor',
      'heavy_vehicle_percent', 'terrain_type', 'grade_percent', 'horizontal_alignment',
      'lane_width', 'shoulder_width', 'access_point_density', 'passing_lane_role',
    ];
    const remediationKeys = [
      ...facilityColumns.map((column) => `facility.col.${column}`),
      'facility.option.passing_lane_role.none',
      'facility.option.passing_lane_role.passing_lane',
      'facility.option.passing_lane_role.downstream_affected',
      'facility.template.level_example_3',
      'facility.template.mountainous_example_4',
      'warning.merge.maximum_desirable_flow',
      'warning.diverge.maximum_desirable_flow',
      'validation.invalid_value',
      'validation.outside_qualified_scope',
    ];
    for (const key of remediationKeys) {
      expect(catalogs.en[key]).toBeTruthy();
      expect(catalogs.th[key]).toBeTruthy();
      expect(translate('th', key)).not.toBe(key);
    }
  });

  it('discloses Thailand traffic-side scope without changing engineering terms', () => {
    expect(translate('en', 'multilane.right_clearance')).toBe('Roadside lateral clearance');
    expect(translate('en', 'multilane.left_clearance')).toContain('HCM source term');
    expect(translate('en', 'basic_freeway.right_side_lateral_clearance')).toContain('HCM source term');
    expect(translate('en', 'weaving.right_side_lateral_clearance')).toContain('HCM source term');
    expect(translate('en', 'ramp.right_side_lateral_clearance')).toContain('HCM source term');
    expect(translate('en', 'weaving.reference_caption')).toContain('origin/destination movement codes');
    expect(translate('en', 'method.merge_segment.scope')).toContain('left-side/LHT mirroring is not qualified');
    expect(translate('en', 'method.diverge_segment.scope')).toContain('left-side/LHT mirroring is not qualified');

    expect(translate('th', 'multilane.right_clearance')).toBe('ระยะเคลียร์ข้างทาง');
    expect(translate('th', 'multilane.left_clearance')).toContain('คำศัพท์ต้นฉบับ HCM');
    expect(translate('th', 'basic_freeway.right_side_lateral_clearance')).toContain('คำศัพท์ต้นฉบับ HCM');
    expect(translate('th', 'weaving.reference_caption')).toContain('ไม่ใช่รหัสตำแหน่งช่องจราจรด้านซ้าย/ขวา');
    expect(translate('th', 'method.merge_segment.scope')).toContain('ยังไม่ผ่านการรับรอง');
  });

  it('localizes bounded Chapter 18 discovery metadata without leaking catalog keys', () => {
    const keys = [
      'method.urban_streets',
      'method.urban_street_segment.name',
      'method.urban_street_segment.description',
      'method.urban_street_segment.scope',
    ];
    for (const locale of ['en', 'th'] as const) {
      for (const key of keys) {
        expect(catalogs[locale][key]).toBeTruthy();
        expect(translate(locale, key)).not.toBe(key);
      }
      expect(translate(locale, 'method.urban_street_segment.description')).toContain('15');
      expect(translate(locale, 'method.urban_street_segment.scope')).toContain('RHT');
      expect(translate(locale, 'method.urban_street_segment.scope')).toContain('LHT');
    }
    expect(translate('en', 'method.urban_street_segment.scope')).toContain('signalized');
    expect(translate('en', 'method.urban_street_segment.scope')).toMatch(/bounded/i);
    expect(translate('th', 'method.urban_street_segment.scope')).toContain('สัญญาณไฟ');
    expect(translate('th', 'method.urban_street_segment.scope')).toContain('ขอบเขตจำกัด');
  });

  it('translates every advertised Chapter 18 field and group label key in both locales', () => {
    const fieldKeys = [
      'segment_length', 'upstream_intersection_width', 'signal_control_spacing',
      'through_lane_count', 'subject_direction', 'through_movement_id',
      'posted_speed_limit', 's_calib', 'restrictive_median_proportion',
      'curb_proportion', 'parking_proportion', 'subject_side_access_count',
      'opposing_side_access_count', 'v_m_veh_h', 'access_point_delays_s_veh',
      'd_other_s_veh', 'analysis_period_min', 'control_type', 'demand_balanced',
      'demand_adjustments_resolved', 'capacity_effects_resolved', 'spillback_present',
      'external_source_class', 'external_source_tool', 'external_source_method_note',
      'external_hcm_edition_note', 'external_direction', 'external_control_type',
      'external_through_movement_id', 'external_analysis_period_min',
      'external_scenario_note', 'v_th_veh_h', 'c_th_veh_h', 'd_t_s_veh',
    ];
    const keys = [
      ...fieldKeys.map((field) => `urban_street_segment.${field}`),
      'urban_street_segment.group_segment',
      'urban_street_segment.group_external_through',
    ];

    for (const locale of ['en', 'th'] as const) {
      for (const key of keys) {
        expect(catalogs[locale][key]).toBeTruthy();
        expect(translate(locale, key)).not.toBe(key);
      }
    }
  });

  it('localizes the complete Thailand/LHT reference-only method and public field contract', () => {
    const fields = [
      'segment_length', 'upstream_intersection_width', 'signal_control_spacing',
      'through_lane_count', 'subject_direction', 'through_movement_id',
      'posted_speed_limit', 's_calib', 'restrictive_median_proportion',
      'kerbside_curb_proportion', 'kerbside_parking_proportion',
      'subject_kerbside_access_count', 'opposing_kerbside_access_count',
      'v_m_veh_h', 'access_point_delays_s_veh', 'd_other_s_veh',
      'analysis_period_min', 'control_type', 'demand_balanced',
      'demand_adjustments_resolved', 'capacity_effects_resolved', 'spillback_present',
      'external_source_class', 'external_source_tool', 'external_source_method_note',
      'external_hcm_edition_note', 'external_direction', 'external_control_type',
      'external_through_movement_id', 'external_analysis_period_min',
      'external_scenario_note', 'v_th_veh_h', 'c_th_veh_h', 'd_t_s_veh',
      'calibration_status', 'calibration_source_note',
    ];
    const keys = [
      'method.urban_street_segment_th_lht.name',
      'method.urban_street_segment_th_lht.description',
      'method.urban_street_segment_th_lht.scope',
      'method.urban_street_segment_th_lht.scope.bounded_signalized_15min',
      'method.urban_street_segment_th_lht.scope.th_lht_reference',
      ...fields.map((field) => `urban_street_segment_th_lht.${field}`),
      'urban_street_segment_th_lht.calibration_status.hcm_reference_uncalibrated',
      'urban_street_segment_th_lht.calibration_status.user_local_calibration',
      'urban_street_segment_th_lht.group_segment',
      'urban_street_segment_th_lht.group_external_through',
    ];
    for (const locale of ['en', 'th'] as const) {
      for (const key of keys) {
        expect(catalogs[locale][key], `${locale}:${key}`).toBeTruthy();
        expect(translate(locale, key)).not.toBe(key);
      }
    }
    expect(translate('en', 'urban_street_segment_th_lht.kerbside_curb_proportion')).toContain('outside roadside');
    expect(translate('en', 'method.urban_street_segment_th_lht.scope')).toContain('not Thai empirical calibration');
    expect(translate('th', 'method.urban_street_segment_th_lht.scope')).toContain('ทางซ้าย');
  });

  it('distinguishes the upstream boundary from the qualified signalized downstream boundary', () => {
    const id = 'urban_street_segment_th_lht';
    expect(translate('en', `method.${id}.description`)).toMatch(/signalized downstream boundary/i);
    expect(translate('th', `method.${id}.description`)).toContain('ทางแยกเขตปลายทาง');
    expect(translate('en', `guide.${id}.decision`)).toMatch(/upstream boundary may be signalized or non-signalized/i);
    expect(translate('th', `guide.${id}.decision`)).toContain('ทางแยกต้นน้ำที่ติดกับช่วงทางโดยตรงอาจมีหรือไม่มีสัญญาณไฟ');
    expect(translate('en', `guide.${id}.avoid`)).toMatch(/immediate upstream boundary may be signalized, STOP-controlled, YIELD-controlled.*or through-uncontrolled/i);
    expect(translate('en', `guide.${id}.avoid`)).toMatch(/does not calculate upstream intersection performance or delay/i);
    expect(translate('en', `guide.${id}.avoid`)).not.toMatch(/allowed when they do not require the subject through movement to stop or yield/i);
    expect(translate('th', `guide.${id}.avoid`)).toContain('ทางแยกต้นน้ำที่ติดกับช่วงทางโดยตรงอาจควบคุมด้วยสัญญาณไฟ STOP หรือ YIELD');
    expect(translate('th', `guide.${id}.avoid`)).toContain('โปรแกรมนี้ไม่ได้คำนวณสมรรถนะหรือความล่าช้าของทางแยกต้นน้ำ');
    expect(translate('th', `guide.${id}.avoid`)).not.toMatch(/ใช้ได้เมื่อ.*ไม่บังคับให้จราจรตรงที่วิเคราะห์หยุดหรือให้ทาง/);
    expect(translate('en', `guide.${id}.overview`)).toMatch(/No upstream intersection performance or delay is calculated.*neither is included in d_t.*d_t remains qualified downstream through delay/i);
    expect(translate('th', `guide.${id}.overview`)).toMatch(/ไม่มีการคำนวณสมรรถนะหรือความล่าช้าของทางแยกต้นน้ำ.*ไม่รวมใน d_t.*d_t คือความล่าช้าจราจรตรงปลายทางสุดท้าย/);
    expect(translate('en', `guide.${id}.limit.4`)).toMatch(/downstream unsignalized control types remain deferred/i);
    expect(translate('en', `guide.${id}.limit.4`)).toMatch(/including STOP- or YIELD-controlled subject through movements.*upstream intersection performance is not calculated/i);
    expect(translate('en', `guide.${id}.limit.4`)).not.toMatch(/when the subject through movement is through-uncontrolled there/i);
    expect(translate('th', `guide.${id}.limit.4`)).toContain('การควบคุมปลายทางที่ไม่มีสัญญาณไฟยังอยู่ระหว่างรอการพัฒนา');
    expect(translate('th', `guide.${id}.limit.4`)).toContain('รวมถึงกรณี STOP/YIELD ที่บังคับให้จราจรตรงที่วิเคราะห์หยุดหรือให้ทาง');
    expect(translate('th', `guide.${id}.limit.4`)).toContain('ไม่ได้คำนวณสมรรถนะของทางแยกต้นน้ำ');
    expect(translate('th', `guide.${id}.limit.4`)).not.toMatch(/เมื่อจราจรตรงที่วิเคราะห์ไม่ต้องหยุดหรือให้ทาง/);
    expect(translate('en', `guide.${id}.glossary.description.7`)).toMatch(/through-uncontrolled TWSC upstream/i);
    expect(translate('th', `guide.${id}.glossary.description.7`)).toContain('TWSC ต้นน้ำไม่บังคับให้จราจรตรงหยุดหรือให้ทาง');
    expect(translate('en', `guide.${id}.step.8`)).toMatch(/Case A: STOP\/YIELD-controlled upstream.*Case B: through-uncontrolled TWSC upstream.*L_s.*user supplies/i);
    expect(translate('th', `guide.${id}.step.8`)).toMatch(/กรณี A: ทางแยก STOP\/YIELD ต้นน้ำ.*กรณี B: TWSC ต้นน้ำที่จราจรตรงไม่ถูกควบคุม.*L_s.*ผู้ใช้ระบุ/);
  });

  it('explains L_s and the immediate upstream width in both locales', () => {
    const id = 'urban_street_segment_th_lht';
    expect(translate('en', `${id}.signal_control_spacing`)).toBe('Control spacing, L_s');
    expect(translate('th', `${id}.signal_control_spacing`)).toBe('ระยะระหว่างจุดควบคุม L_s');
    expect(translate('en', `${id}.signal_control_spacing.help`)).toMatch(/stop or yield.*may differ from the analyzed segment length/i);
    expect(translate('th', `${id}.signal_control_spacing.help`)).toContain('บังคับให้การเคลื่อนที่ตรงในทิศทางที่วิเคราะห์ต้องหยุดหรือให้ทาง');
    expect(translate('en', `${id}.upstream_intersection_width.help`)).toMatch(/immediate upstream boundary intersection/i);
    expect(translate('th', `${id}.upstream_intersection_width.help`)).toContain('ทางแยกที่เขตต้นน้ำติดกับช่วงทางโดยตรง');
    expect(translate('en', `${id}.control_type`)).toBe('Downstream boundary control type');
    expect(translate('th', `${id}.control_type`)).toBe('ประเภทการควบคุมที่ทางแยกเขตปลายทาง');
    expect(translate('en', `${id}.external_control_type`)).toBe('External downstream control type');
    expect(translate('th', `${id}.external_control_type`)).toBe('ประเภทการควบคุมปลายทางจากแหล่งภายนอก');
    expect(translate('en', `${id}.validation.control_type`)).toMatch(/qualified downstream boundary must be signalized/i);
    expect(translate('en', `${id}.validation.external_control_type`)).toMatch(/qualified external downstream result must be signalized and match the downstream boundary/i);
    expect(translate('th', `${id}.validation.control_type`)).toContain('ทางแยกเขตปลายทางที่ผ่านการรับรองต้องควบคุมด้วยสัญญาณไฟ');
    expect(translate('th', `${id}.validation.external_control_type`)).toContain('ต้องเป็นสัญญาณไฟและตรงกับทางแยกเขตปลายทาง');
  });

});
