import { expect, test } from '@playwright/test';

const MULTILANE_CONTRACT = 'manual_multilane_segment_v0';
const FREEWAY_CONTRACT = 'manual_basic_freeway_v0';
const WEAVING_CONTRACT = 'manual_weaving_segment_hcm70_v0';
const MERGE_CONTRACT = 'manual_merge_segment_hcm70_v0';
const DIVERGE_CONTRACT = 'manual_diverge_segment_hcm70_v0';

async function openMethod(page: Parameters<typeof test>[0]['page'], methodId: string, heading: string) {
  await page.goto('/new-analysis');
  await page.getByTestId(`method-card-${methodId}`).getByRole('button', { name: 'Start analysis' }).click();
  await expect(page.getByTestId(`workflow-${methodId}`)).toBeVisible();
  await expect(page.getByRole('heading', { name: heading })).toBeVisible();
}

test.describe('Phase 2 representative workflows', () => {
  test('Multilane computes, saves, and exports through the shared workflow', async ({ page }) => {
    await openMethod(page, 'multilane_segment', 'Multilane Highway Segment');
    await expect(page.getByText('HCM 7th Edition Chapter 12')).toBeVisible();
    await expect(page.getByTestId('phase2-form-multilane_segment')).toBeVisible();
    await expect(page.getByTestId('phase2-example-asset-multilane_segment')).toBeVisible();
    await page.getByRole('button', { name: 'Calculate' }).click();
    const results = page.getByTestId('workflow-results');
    await expect(results).toBeVisible();
    await expect(results.getByText('Level of service')).toBeVisible();
    await expect(results.getByText('Density', { exact: true }).first()).toBeVisible();
    await expect(results.getByText('Demand flow rate')).toBeVisible();
    const downloadPromise = page.waitForEvent('download');
    await results.getByRole('button', { name: 'Export' }).click();
    await results.getByRole('button', { name: 'CSV' }).click();
    expect((await downloadPromise).suggestedFilename()).toMatch(/multilane.*\.csv$/i);
    const projectDownloadPromise = page.waitForEvent('download');
    await results.getByRole('button', { name: 'Save to Project' }).click();
    expect((await projectDownloadPromise).suggestedFilename()).toMatch(/project.*\.json$/i);
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText(MULTILANE_CONTRACT)).toBeVisible();
  });

  test('Multilane switching FFS source makes conditional fields visible', async ({ page }) => {
    await openMethod(page, 'multilane_segment', 'Multilane Highway Segment');
    await expect(page.getByLabel('Measured free-flow speed')).toBeVisible();
    await page.getByLabel('Free-flow speed source').selectOption('estimated');
    await expect(page.getByLabel('Posted speed limit')).toBeVisible();
    await expect(page.getByLabel('Median type')).toBeVisible();
    await expect(page.getByLabel('Access-point density')).toBeVisible();
    await expect(page.getByLabel('External passenger-car equivalent')).toBeHidden();
    await page.getByLabel('Heavy-vehicle adjustment method').selectOption('external_pce');
    await expect(page.getByLabel('External passenger-car equivalent')).toBeVisible();
  });

  test('Basic Freeway estimates FFS, calculates, and exports JSON', async ({ page }) => {
    await openMethod(page, 'basic_freeway_segment', 'Basic Freeway Segment');
    await expect(page.getByTestId('phase2-form-basic_freeway_segment')).toBeVisible();
    await expect(page.getByTestId('phase2-example-asset-basic_freeway_segment')).toBeVisible();
    await page.getByLabel('Free-flow speed source').selectOption('estimated');
    await expect(page.getByLabel('Base free-flow speed')).toBeVisible();
    await expect(page.getByLabel('Total ramp density')).toBeVisible();
    await page.getByRole('button', { name: 'Calculate' }).click();
    const results = page.getByTestId('workflow-results');
    await expect(results).toBeVisible();
    await expect(results.getByText('Level of service')).toBeVisible();
    await expect(results.getByText('Adjusted capacity')).toBeVisible();
    await results.getByRole('button', { name: 'Export' }).click();
    const downloadPromise = page.waitForEvent('download');
    await results.getByRole('button', { name: 'JSON' }).click();
    expect((await downloadPromise).suggestedFilename()).toMatch(/freeway.*\.json$/i);
  });

  test('Weaving exposes configuration fields and computes a supported one-sided case', async ({ page }) => {
    await openMethod(page, 'weaving_segment', 'Weaving Segment');
    await expect(page.getByTestId('phase2-form-weaving_segment')).toBeVisible();
    await expect(page.getByTestId('phase2-example-asset-weaving_segment')).toBeVisible();
    await expect(page.getByLabel('Configuration')).toHaveValue('one_sided');
    await expect(page.getByLabel('Entry side')).toBeVisible();
    await expect(page.getByLabel('Exit side')).toBeVisible();
    await page.getByRole('button', { name: 'Calculate' }).click();
    const results = page.getByTestId('workflow-results');
    await expect(results).toBeVisible();
    await expect(results.getByText('Level of service')).toBeVisible();
    await expect(results.getByText('Mean speed')).toBeVisible();
    await expect(results.getByText('Governing capacity')).toBeVisible();
  });

  test('Merge and Diverge retain distinct auxiliary-lane labels and compute', async ({ page }) => {
    await openMethod(page, 'merge_segment', 'Merge Segment');
    await expect(page.getByTestId('phase2-form-merge_segment')).toBeVisible();
    await expect(page.getByTestId('phase2-example-asset-merge_segment')).toBeVisible();
    await expect(page.getByLabel('Acceleration lane length')).toBeVisible();
    await page.getByRole('button', { name: 'Calculate' }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByTestId('workflow-results').getByText('Governing v/c')).toBeVisible();

    await page.getByRole('button', { name: 'Back to methods' }).click();
    await page.getByTestId('method-card-diverge_segment').getByRole('button', { name: 'Start analysis' }).click();
    await expect(page.getByTestId('phase2-form-diverge_segment')).toBeVisible();
    await expect(page.getByLabel('Deceleration lane length')).toBeVisible();
    await page.getByRole('button', { name: 'Calculate' }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
  });

  test('invalid Multilane demand is blocked before calculation', async ({ page }) => {
    await openMethod(page, 'multilane_segment', 'Multilane Highway Segment');
    const demand = page.getByLabel('Demand volume');
    await demand.fill('0');
    await demand.blur();
    await expect(page.getByText('Demand volume must be at least 1.')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Calculate' })).toBeDisabled();
  });

  test('capacity failure is explicit instead of fabricating speed and density', async ({ page }) => {
    await openMethod(page, 'basic_freeway_segment', 'Basic Freeway Segment');
    await page.getByLabel('Demand volume').fill('10000');
    await page.getByRole('button', { name: 'Calculate' }).click();
    const results = page.getByTestId('workflow-results');
    await expect(results).toBeVisible();
    await expect(results.getByText('Capacity failure')).toBeVisible();
    await expect(results.getByText('Not predicted in this state')).toBeVisible();
  });

  test('weaving handoff state does not fabricate an LOS answer', async ({ page }) => {
    await openMethod(page, 'weaving_segment', 'Weaving Segment');
    await page.getByLabel('Weaving segment length').fill('9000');
    await page.getByRole('button', { name: 'Calculate' }).click();
    const results = page.getByTestId('workflow-results');
    await expect(results).toBeVisible();
    await expect(results.getByText('HCM handoff required')).toBeVisible();
    await expect(results.getByText('No LOS is assigned in this state.')).toBeVisible();
  });

  test('saved Project v2 round-trips and scenario comparison remains auditable', async ({ page }) => {
    await openMethod(page, 'basic_freeway_segment', 'Basic Freeway Segment');
    await page.getByRole('button', { name: 'Calculate' }).click();
    const projectDownloadPromise = page.waitForEvent('download');
    await page.getByTestId('workflow-results').getByRole('button', { name: 'Save to Project' }).click();
    const projectDownload = await projectDownloadPromise;
    expect(projectDownload.suggestedFilename()).toMatch(/project.*\.json$/i);
    const path = await projectDownload.path();
    expect(path).toBeTruthy();
    await expect(page.getByTestId('project-workspace')).toBeVisible();

    await page.locator('.scenario-actions-menu > summary').click();
    await page.getByLabel('Duplicate name').fill('Alternative A');
    await page.getByRole('button', { name: 'Duplicate scenario' }).click();
    await expect(page.getByText('Alternative A', { exact: true })).toBeVisible();
    await page.getByText('Alternative A', { exact: true }).click();
    await page.getByRole('button', { name: 'Calculate scenario' }).click();
    await page.getByLabel('Left scenario').selectOption({ index: 1 });
    await page.getByLabel('Right scenario').selectOption({ index: 2 });
    await page.getByRole('button', { name: 'Compare' }).click();
    await expect(page.locator('.comparison-table')).toBeVisible();
  });

  test('legacy v0.9 Multilane and Phase 3 imports migrate safely in Project v2', async ({ page }) => {
    await openMethod(page, 'multilane_segment', 'Multilane Highway Segment');
    await page.getByRole('button', { name: 'Calculate' }).click();
    const projectDownloadPromise = page.waitForEvent('download');
    await page.getByTestId('workflow-results').getByRole('button', { name: 'Save to Project' }).click();
    await projectDownloadPromise;
    await expect(page.getByTestId('project-workspace')).toBeVisible();

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
    const workspace = page.getByTestId('project-workspace');
    await expect(workspace).toBeVisible();
    await expect(workspace.getByText('Two-Lane Highway Segment', { exact: true }).first()).toBeVisible();
    await expect(workspace.getByText('HCM 7th Edition Chapter 15', { exact: true }).first()).toBeVisible();
    await expect(workspace.getByRole('button', { name: 'Calculate scenario' })).toBeEnabled();
    await expect(workspace.getByRole('button', { name: 'Edit scenario' })).toBeEnabled();
    await expect(workspace.locator('.scenario-actions-menu > summary')).toBeVisible();
    await workspace.getByRole('button', { name: 'Edit scenario' }).click();
    await expect(page.getByTestId('workflow-two_lane_segment')).toBeVisible();
    await expect(page.getByTestId('phase3-form-two_lane_segment')).toBeVisible();
  });
});
