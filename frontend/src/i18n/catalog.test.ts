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

});
