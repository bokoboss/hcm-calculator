import { expect, test } from '@playwright/test';

test.describe('Phase 2 representative workflows', () => {
  test('Multilane supports explicit calculate, stale protection, and FFS branch switching', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-multilane_segment').getByRole('button', { name: 'Select method' }).click();
    await expect(page.getByTestId('workflow-multilane_segment')).toBeVisible();
    await expect(page.locator('#multilane-demand_volume_veh_h')).toHaveValue('1500');
    await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toContainText('Level of service');
    await expect(page.getByTestId('workflow-results')).toContainText('11.2');

    await page.locator('#multilane-demand_volume_veh_h').fill('1800');
    await expect(page.locator('[data-slot="stale-result-banner"]')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).not.toBeVisible();
    await page.locator('[data-slot="stale-result-banner"]').getByRole('button', { name: 'Recalculate' }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();

    await page.getByRole('radio', { name: 'Measured' }).click();
    await expect(page.locator('#multilane-free_flow_speed')).toBeVisible();
    await expect(page.locator('.error-summary a[href="#multilane-free_flow_speed"]')).toBeVisible();
    await page.locator('#multilane-free_flow_speed').fill('90');
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();
    await page.locator('[data-slot="readiness-bar"]').getByRole('button').click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByText('Measured', { exact: true }).first()).toBeVisible();
    const exportDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Export Markdown' }).click();
    expect((await exportDownload).suggestedFilename()).toMatch(/\.md$/);

    await page.getByRole('radio', { name: 'Estimated' }).click();
    await expect(page.locator('#multilane-posted_speed_limit')).toBeVisible();
    await page.getByRole('radio', { name: 'Divided median' }).click();
    await expect(page.locator('#multilane-left_side_lateral_clearance')).toBeVisible();
    await page.locator('#multilane-left_side_lateral_clearance').fill('4');
    await page.getByRole('radio', { name: 'Specific grade' }).click();
    await expect(page.locator('#multilane-grade_percent')).toBeVisible();
    await page.locator('#multilane-grade_percent').fill('-3.5');
    await page.locator('[data-slot="readiness-bar"]').getByRole('button').click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await page.getByRole('radio', { name: 'General terrain' }).click();
    await page.getByRole('radio', { name: 'Level' }).click();
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();
    await page.locator('[data-slot="readiness-bar"]').getByRole('button').click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await page.getByRole('radio', { name: 'External PCE' }).click();
    await page.locator('#multilane-passenger_car_equivalent').fill('2.5');
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();
    await page.locator('[data-slot="readiness-bar"]').getByRole('button').click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
  });

  test('Two-Lane Facility keeps locked context visible, calculates evidence, and saves Project v2', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-two_lane_facility').getByRole('button', { name: 'Select method' }).click();
    await expect(page.getByTestId('workflow-two_lane_facility')).toBeVisible();
    await expect(page.getByTestId('facility-input-4-opposing_direction_volume_veh_h')).toBeEnabled();
    await expect(page.getByTestId('facility-input-1-opposing_direction_volume_veh_h')).toHaveCount(0);
    await page.locator('#facility-template').selectOption('mountainous_example_4');
    await expect(page.getByTestId('facility-input-6-segment_length')).toHaveAttribute('readonly', '');
    await expect(page.getByTestId('facility-input-1-segment_length')).toHaveAttribute('readonly', '');
    await expect(page.getByTestId('facility-input-1-posted_speed')).toBeEnabled();
    await page.getByTestId('facility-input-1-posted_speed').fill('');
    await expect(page.locator('.error-summary a[href="#facility-input-1-posted_speed"]')).toBeVisible();
    await page.getByTestId('facility-input-1-posted_speed').fill('55');
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toContainText('Facility level of service');
    await expect(page.getByTestId('workflow-results')).toContainText('Critical segment');
    const xlsxDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Export XLSX' }).click();
    expect((await xlsxDownload).suggestedFilename()).toMatch(/\.xlsx$/);

    const download = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Save to Project' }).click();
    const projectDownload = await download;
    const downloadedProjectPath = await projectDownload.path();
    expect(downloadedProjectPath).toBeTruthy();
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('2.0', { exact: true })).toBeVisible();
    await expect(page.getByText('Migrated', { exact: false })).not.toBeVisible();

    if (downloadedProjectPath) {
      await page.setInputFiles('#project-file', downloadedProjectPath);
      await expect(page.getByText('Project opened and validated.', { exact: true })).toBeVisible();
      await expect(page.getByText('2.0', { exact: true })).toBeVisible();
    }

    await page.getByRole('button', { name: 'Duplicate scenario' }).click();
    await expect(page.getByRole('button', { name: /Alternative/ })).toBeVisible();
    await page.getByRole('button', { name: /Alternative/ }).click();

    const selectsBeforeRecalculation = page.locator('.project-controls select');
    await selectsBeforeRecalculation.nth(0).selectOption({ label: 'Base' });
    await selectsBeforeRecalculation.nth(1).selectOption({ label: 'Alternative' });
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await expect(page.getByText('Compare and export require current results for both scenarios.', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Edit scenario' }).click();
    await expect(page.getByTestId('workflow-two_lane_facility')).toBeVisible();
    await page.getByTestId('facility-input-1-posted_speed').fill('45');
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await page.getByRole('button', { name: 'Save scenario result' }).click();
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('current', { exact: true }).last()).toBeVisible();

    const selects = page.locator('.project-controls select');
    await selects.nth(0).selectOption({ label: 'Base' });
    await selects.nth(1).selectOption({ label: 'Alternative' });
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await expect(page.getByTestId('comparison-result')).toBeVisible();
    await expect(page.getByTestId('comparison-result')).toContainText('no recalculation');
    await expect(page.getByTestId('comparison-result').locator('ul li').first()).toBeVisible();
  });

  test('Two-Lane Facility keeps narrow overflow inside the engineering grid', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-two_lane_facility').getByRole('button', { name: 'Select method' }).click();
    await page.locator('#facility-template').selectOption('mountainous_example_4');
    await expect(page.getByTestId('facility-input-6-segment_length')).toHaveAttribute('readonly', '');
    const overflow = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth + 1);
    const tableOverflow = await page.locator('.table-scroll').evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
    expect(tableOverflow.scrollWidth).toBeGreaterThan(tableOverflow.clientWidth);
  });

  test('Multilane capacity failure exposes unavailable metrics and preserves identity across locales', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-multilane_segment').getByRole('button', { name: 'Select method' }).click();
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();

    await page.locator('#multilane-demand_volume_veh_h').fill('5000');
    await expect(page.locator('[data-slot="stale-result-banner"]')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Export Markdown' })).toHaveCount(0);
    await page.locator('[data-slot="stale-result-banner"]').getByRole('button', { name: 'Recalculate' }).click();
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.getByText('Not predicted in this state', { exact: true })).toHaveCount(2);
    await expect(page.getByText('Speed and density are not predicted in this state.', { exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Audit evidence and identity' }).click();
    const fingerprint = await page.locator('.evidence-grid code').innerText();
    expect(fingerprint).toMatch(/^[0-9a-f]{64}$/);

    await page.getByRole('button', { name: 'Thai' }).click();
    await expect(page.getByText('ไม่คาดการณ์ในสถานะนี้', { exact: true })).toHaveCount(2);
    await expect(page.getByText('ในสถานะนี้จะไม่คาดการณ์ความเร็วและความหนาแน่น', { exact: true })).toBeVisible();
    await expect(page.locator('.evidence-grid code')).toHaveText(fingerprint);

    await page.getByRole('button', { name: 'อังกฤษ' }).click();
    await expect(page.getByText('Not predicted in this state', { exact: true })).toHaveCount(2);
    await expect(page.locator('.evidence-grid code')).toHaveText(fingerprint);
  });

  test('Two-Lane Facility validates editable rows and renders metric and Thai evidence', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-two_lane_facility').getByRole('button', { name: 'Select method' }).click();
    await expect(page.getByTestId('facility-input-1-lane_width')).toHaveValue(/3\.6576/);
    await expect(page.getByTestId('facility-input-1-shoulder_width')).toHaveValue(/1\.8288/);

    await page.getByTestId('facility-input-1-peak_hour_factor').fill('0');
    await expect(page.locator('.error-summary a[href="#facility-input-1-peak_hour_factor"]')).toBeVisible();
    await expect(page.locator('[data-slot="readiness-bar"] button')).toBeDisabled();
    await page.getByTestId('facility-input-1-peak_hour_factor').fill('0.94');
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();

    await page.getByTestId('facility-input-4-opposing_direction_volume_veh_h').fill('');
    await expect(page.locator('.error-summary a[href="#facility-input-4-opposing_direction_volume_veh_h"]')).toBeVisible();
    await expect(page.locator('[data-slot="readiness-bar"] button')).toBeDisabled();
    await page.getByTestId('facility-input-4-opposing_direction_volume_veh_h').fill('600');
    await expect(page.locator('[data-slot="error-summary"]')).not.toBeVisible();

    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toContainText('94.4');
    await expect(page.getByTestId('workflow-results')).toContainText('4.5');
    await expect(page.getByTestId('workflow-results')).toContainText('km/h');
    await expect(page.getByTestId('workflow-results')).toContainText('fol/km/ln');

    await page.getByRole('button', { name: 'Thai' }).click();
    await expect(page.getByText('ระดับการให้บริการของสิ่งอำนวยความสะดวก', { exact: true })).toBeVisible();
    await expect(page.getByText('ความเร็วเฉลี่ยสิ่งอำนวยความสะดวก', { exact: true })).toBeVisible();
  });

  test('legacy v0.9 Multilane and reference-only imports migrate safely in Project v2', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'Open Project' }).first().click();
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    const startingResponse = await page.request.get('/api/v1/analyses/multilane_segment/starting-values?template_id=MLH-CH26-004-EB&unit_system=imperial');
    expect(startingResponse.ok()).toBeTruthy();
    const starting = await startingResponse.json();
    const calculationResponse = await page.request.post('/api/v1/analyses/multilane_segment/calculate', {
      data: {
        template_id: 'MLH-CH26-004-EB',
        unit_system: 'imperial',
        displayed_inputs: starting.displayed_inputs,
      },
    });
    expect(calculationResponse.ok()).toBeTruthy();
    const snapshot = await calculationResponse.json();
    const legacyMultilane = {
      schema_version: '1.2',
      project_type: 'manual_multilane_v0',
      generated_by: 'hcm-calculator 0.9.0',
      created_at: '2025-01-01T00:00:00+00:00',
      unit_system: 'imperial',
      template_id: snapshot.template_id,
      displayed_ui_inputs: snapshot.displayed_inputs,
      normalized_engine_inputs: snapshot.normalized_inputs,
      method_identifier: 'hcm7_multilane_los',
      method_version: 'phase_8',
      calculation_fingerprint: snapshot.calculation_fingerprint,
      calculation_result: snapshot.result,
      audit: snapshot.audit,
      presentation: { locale: 'en' },
    };
    await page.setInputFiles('#project-file', {
      name: 'legacy-multilane-v09.json',
      mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(legacyMultilane)),
    });
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('Legacy project migrated to Project v2; stale or incompatible results were discarded.', { exact: true })).toBeVisible();
    await expect(page.getByText('2.0', { exact: true })).toBeVisible();
    await expect(page.getByText('Migrated legacy Base', { exact: true }).first()).toBeVisible();

    const legacyReference = {
      schema_version: '1.2',
      project_type: 'manual_single_segment',
      generated_by: 'hcm-calculator 0.9.0',
      created_at: '2025-01-01T00:00:00+00:00',
      unit_system: 'metric',
      manual_inputs: {
        unit_system: 'metric',
        segment_type: 'passing_constrained',
        terrain_type: 'level',
        horizontal_alignment: 'straight',
        segment_length: 1.2,
        posted_speed: 80.0,
        lane_width: 3.5,
        shoulder_width: 1.8,
        access_point_density: 0.0,
        analysis_direction_volume: 750.0,
        peak_hour_factor: 0.94,
        heavy_vehicle_percent: 5.0,
        grade_percent: 0.0,
        opposing_direction_volume: null,
        horizontal_alignment_subsegments: [],
      },
      normalized_engine_inputs: {},
    };
    await page.setInputFiles('#project-file', {
      name: 'legacy-reference-v09.json',
      mimeType: 'application/json',
      buffer: Buffer.from(JSON.stringify(legacyReference)),
    });
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('Reference-only method', { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Calculate scenario' })).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Edit scenario' })).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Duplicate scenario' })).toBeEnabled();
  });
});
