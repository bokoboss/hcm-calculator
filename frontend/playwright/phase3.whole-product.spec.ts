import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const referenceDirectory = path.resolve('..', 'docs', 'application_rebuild', 'visual-reference');
mkdirSync(referenceDirectory, { recursive: true });

async function capture(page: Page, name: string, projectView = false): Promise<void> {
  if (projectView) {
    await page.locator('.project-topbar strong').evaluate((element) => {
      element.textContent = '28 Aug 2026, 15:00';
    });
  }
  await page.evaluate(async () => { await document.fonts.ready; });
  await page.screenshot({
    path: path.join(referenceDirectory, name),
    fullPage: true,
    animations: 'disabled',
  });
}

async function assertNoGlobalHorizontalOverflow(page: Page): Promise<void> {
  const dimensions = await page.evaluate(() => ({
    documentWidth: document.documentElement.scrollWidth,
    viewportWidth: window.innerWidth,
  }));
  expect(dimensions.documentWidth).toBeLessThanOrEqual(dimensions.viewportWidth + 1);
}

async function waitForWorkflow(page: Page, methodId: string): Promise<void> {
  await expect(page.getByTestId(`workflow-${methodId}`)).toBeVisible();
  await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
}

async function calculate(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
}

async function calculateWithInputs(page: Page, methodId: string, values: Record<string, number>): Promise<void> {
  await page.goto(`/analysis/${methodId}`);
  await waitForWorkflow(page, methodId);
  for (const [field, value] of Object.entries(values)) {
    await page.locator(`#${methodId}-${field}`).fill(String(value));
  }
  await calculate(page);
}

test.describe('Phase 3 whole-product workstation UAT', () => {
  test.setTimeout(60_000);

  test('captures the launcher, chooser, Method Guide, and persisted locale', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'HCM Calculator' })).toBeVisible();
    await capture(page, 'phase3-ux-home-en-1920.png');

    await page.getByRole('button', { name: 'Thai' }).click();
    await expect(page.locator('html')).toHaveAttribute('lang', 'th');
    await expect(page.getByRole('heading', { name: 'เครื่องคำนวณ HCM' })).toBeVisible();
    await capture(page, 'phase3-ux-home-th-1920.png');
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('lang', 'th');
    await expect(page.getByRole('heading', { name: 'เครื่องคำนวณ HCM' })).toBeVisible();

    await page.getByRole('button', { name: 'อังกฤษ' }).click();
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
    await expect(page.getByTestId('method-card-weaving_segment')).toBeVisible();
    await capture(page, 'phase3-ux-new-analysis-1920.png');

    await page.getByRole('button', { name: 'Method Guide' }).first().click();
    await expect(page.getByRole('heading', { name: 'Method Guide' })).toBeVisible();
    await expect(page.getByTestId('reference-multilane_segment')).toBeVisible();
    await capture(page, 'phase3-ux-method-guide-1920.png');
  });

  test('keeps the segment workbench spatially continuous across desktop and compact widths', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/analysis/multilane_segment');
    await waitForWorkflow(page, 'multilane_segment');
    await expect(page.locator('#multilane-template')).toBeVisible();
    await calculate(page);

    const inputWide = await page.locator('.workflow-input-workspace').boundingBox();
    const resultWide = await page.locator('.workflow-result-inspector').boundingBox();
    expect(inputWide).not.toBeNull();
    expect(resultWide).not.toBeNull();
    expect(resultWide!.x).toBeGreaterThan(inputWide!.x + inputWide!.width);
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-workbench-1920.png');

    await page.setViewportSize({ width: 1366, height: 768 });
    await expect(page.locator('.workflow-result-inspector')).toBeVisible();
    const inputLaptop = await page.locator('.workflow-input-workspace').boundingBox();
    const resultLaptop = await page.locator('.workflow-result-inspector').boundingBox();
    expect(inputLaptop).not.toBeNull();
    expect(resultLaptop).not.toBeNull();
    expect(resultLaptop!.x).toBeGreaterThan(inputLaptop!.x + inputLaptop!.width);
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-workbench-1366.png');

    await page.setViewportSize({ width: 1024, height: 768 });
    const inputCompact = await page.locator('.workflow-input-workspace').boundingBox();
    const resultCompact = await page.locator('.workflow-result-inspector').boundingBox();
    expect(inputCompact).not.toBeNull();
    expect(resultCompact).not.toBeNull();
    expect(resultCompact!.y).toBeGreaterThan(inputCompact!.y + inputCompact!.height);
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-workbench-stacked-1024.png');
  });

  test('provides quiet validation, retained stale results, and keyboard-operable Export', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/analysis/multilane_segment');
    await waitForWorkflow(page, 'multilane_segment');
    await page.locator('#multilane-access_point_density').fill('');
    await expect(page.locator('[data-slot="error-summary"]')).toHaveCount(0);
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.locator('[data-slot="error-summary"]')).toBeFocused();
    await expect(page.locator('.error-summary a[href="#multilane-access_point_density"]')).toBeVisible();
    await capture(page, 'phase3-ux-validation-recovery.png');

    await page.goto('/analysis/multilane_segment');
    await waitForWorkflow(page, 'multilane_segment');
    await calculate(page);
    await page.locator('#multilane-demand_volume_veh_h').fill('1510');
    const stalePanel = page.locator('[data-slot="stale-result-panel"]');
    await expect(stalePanel).toBeVisible();
    await expect(stalePanel).toContainText('Unavailable until this stale result is recalculated.');
    await capture(page, 'phase3-ux-stale-result.png');

    await page.getByRole('button', { name: 'Recalculate', exact: true }).click();
    await expect(stalePanel).toHaveCount(0);
    const exportTrigger = page.getByRole('button', { name: /^Export/ });
    await exportTrigger.focus();
    await page.keyboard.press('Enter');
    const exportMenu = page.getByRole('menu', { name: 'Export' });
    await expect(exportMenu).toBeVisible();
    await expect(exportMenu.getByRole('menuitem').first()).toBeFocused();
    const bounds = await exportMenu.boundingBox();
    expect(bounds).not.toBeNull();
    expect(bounds!.x).toBeGreaterThanOrEqual(0);
    expect(bounds!.y).toBeGreaterThanOrEqual(0);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(1366);
    expect(bounds!.y + bounds!.height).toBeLessThanOrEqual(768);
    await capture(page, 'phase3-ux-export-menu.png');
    await page.keyboard.press('ArrowDown');
    await expect(exportMenu.getByRole('menuitem').nth(1)).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(exportMenu).toHaveCount(0);
    await expect(exportTrigger).toBeFocused();
  });

  test('keeps Facility as a full-width table workflow with contained overflow', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/analysis/two_lane_facility');
    await waitForWorkflow(page, 'two_lane_facility');
    await expect(page.getByTestId('facility-input-1-lane_width')).toBeVisible();
    await calculate(page);
    const tableViewport = page.locator('.facility-workspace .table-scroll').first();
    await expect(tableViewport).toBeVisible();
    const dimensions = await tableViewport.evaluate((element) => ({
      clientWidth: element.clientWidth,
      scrollWidth: element.scrollWidth,
    }));
    expect(dimensions.scrollWidth).toBeGreaterThanOrEqual(dimensions.clientWidth);
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-facility-1366.png');
  });

  test('keeps method-specific diagrams and structured controls in the primary workflow', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/analysis/two_lane_segment');
    await waitForWorkflow(page, 'two_lane_segment');
    await page.getByRole('radio', { name: 'Horizontal curves', exact: true }).click();
    const curveEditor = page.getByTestId('two-lane-curve-editor');
    await expect(curveEditor).toBeVisible();
    await curveEditor.getByRole('button', { name: 'Generate from setup', exact: true }).click();
    await curveEditor.getByRole('button', { name: 'Generate curve subsegments', exact: true }).click();
    await expect(curveEditor.getByTestId('two-lane-curve-row-0')).toBeVisible();
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-two-lane-curve.png');

    await page.goto('/analysis/weaving_segment');
    await waitForWorkflow(page, 'weaving_segment');
    const reference = page.getByTestId('weaving-reference');
    await expect(reference.locator('img')).toHaveAttribute('data-asset-path', 'weaving/one_sided_weave.png');
    await page.getByRole('radio', { name: 'Two-sided', exact: true }).click();
    await page.getByRole('button', { name: 'Advanced geometry / evidence', exact: true }).click();
    await expect(page.locator('#weaving_segment-nwl_basis')).toBeVisible();
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-weaving-1366.png');
  });

  test('retains distinct warning and capacity result states', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await calculateWithInputs(page, 'merge_segment', {
      freeway_lanes: 2,
      freeway_demand_veh_h: 3600,
      ramp_demand_veh_h: 600,
      freeway_peak_hour_factor: 0.95,
      ramp_peak_hour_factor: 0.95,
      free_flow_speed: 104.60736,
      ramp_ffs: 64.37376,
      auxiliary_lane_length: 182.88,
    });
    await expect(page.locator('[data-slot="warning-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toHaveCount(0);
    await capture(page, 'phase3-ux-merge-warning.png');

    await calculateWithInputs(page, 'diverge_segment', { ramp_demand_veh_h: 2300 });
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="warning-panel"]')).toHaveCount(0);
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
    await capture(page, 'phase3-ux-diverge-capacity.png');
  });

  test('runs the Project Workspace master-detail, scenario, edit, and comparison journey', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/project');
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('No project loaded', { exact: true })).toBeVisible();
    await capture(page, 'phase3-ux-project-empty.png');

    await page.goto('/analysis/multilane_segment');
    await waitForWorkflow(page, 'multilane_segment');
    await calculate(page);
    const projectDownload = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Save to Project', exact: true }).click();
    await projectDownload;
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.locator('.project-master-detail')).toBeVisible();
    await capture(page, 'phase3-ux-project-populated.png', true);

    await page.locator('.scenario-actions-menu > summary').click();
    await page.getByRole('button', { name: 'Duplicate scenario', exact: true }).click();
    await expect(page.locator('[data-slot="action-toast"]')).toContainText('Scenario duplicated.');
    await page.locator('.scenario-row').filter({ hasText: 'Alternative' }).click();
    await expect(page.getByRole('button', { name: 'Calculate scenario', exact: true })).toBeVisible();
    await page.locator('.scenario-actions-menu > summary').click();
    await page.getByLabel('Rename selected scenario').fill('Alternative adjusted');
    await page.getByRole('button', { name: 'Rename scenario', exact: true }).click();
    await expect(page.locator('[data-slot="action-toast"]')).toContainText('Scenario renamed.');
    await page.getByRole('button', { name: 'Calculate scenario', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Edit scenario', exact: true })).toBeVisible();

    await page.getByRole('button', { name: 'Edit scenario', exact: true }).click();
    await waitForWorkflow(page, 'multilane_segment');
    await page.locator('#multilane-demand_volume_veh_h').fill('1510');
    await calculate(page);
    await page.getByRole('button', { name: 'Save scenario result', exact: true }).click();
    await expect(page.getByTestId('project-workspace')).toBeVisible();

    const selectors = page.locator('.project-controls select');
    await selectors.nth(0).selectOption({ label: 'Base' });
    await selectors.nth(1).selectOption({ label: 'Alternative adjusted' });
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await expect(page.getByTestId('comparison-result')).toBeVisible();
    await expect(page.getByTestId('comparison-result').locator('tbody tr').first()).toBeVisible();
    await capture(page, 'phase3-ux-project-compare.png', true);
  });

  test('protects browser history for dirty drafts and keeps navigation usable at 390px', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-multilane_segment').getByRole('button', { name: 'Start analysis', exact: true }).click();
    await waitForWorkflow(page, 'multilane_segment');
    await page.locator('#multilane-demand_volume_veh_h').fill('1510');

    page.once('dialog', async (dialog) => dialog.dismiss());
    await page.goBack();
    await expect(page).toHaveURL(/\/analysis\/multilane_segment$/);
    page.once('dialog', async (dialog) => dialog.accept());
    await page.goBack();
    await expect(page).toHaveURL(/\/new-analysis$/);
    await page.goForward();
    await expect(page).toHaveURL(/\/analysis\/multilane_segment$/);

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/analysis/weaving_segment');
    await waitForWorkflow(page, 'weaving_segment');
    const methodMenu = page.locator('.mobile-method-nav');
    await expect(methodMenu).toBeVisible();
    await methodMenu.locator('summary').click();
    await expect(methodMenu).toHaveAttribute('open', '');
    await expect(methodMenu.getByTestId('nav-method-two_lane_segment')).toBeVisible();
    await assertNoGlobalHorizontalOverflow(page);
    await capture(page, 'phase3-ux-mobile-navigation-390.png');
  });
});
