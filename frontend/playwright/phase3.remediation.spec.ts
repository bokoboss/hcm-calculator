import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const referenceDirectory = path.resolve('..', 'docs', 'application_rebuild', 'visual-reference');
mkdirSync(referenceDirectory, { recursive: true });

const deliveredMethods = [
  'two_lane_segment',
  'two_lane_facility',
  'multilane_segment',
  'basic_freeway_segment',
  'weaving_segment',
  'merge_segment',
  'diverge_segment',
] as const;

async function capture(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: path.join(referenceDirectory, name), fullPage: true });
}

async function calculateWithFields(page: Page, methodId: string, values: Record<string, number>): Promise<void> {
  await page.goto(`/analysis/${methodId}`);
  for (const [field, value] of Object.entries(values)) {
    await page.locator(`#${methodId}-${field}`).fill(String(value));
  }
  await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
}

test.describe('Phase 3 remediation journeys', () => {
  test('direct routes load every delivered method and New Analysis returns to the chooser', async ({ page }) => {
    for (const methodId of deliveredMethods) {
      await page.goto(`/analysis/${methodId}`);
      await expect(page.getByTestId(`workflow-${methodId}`)).toBeVisible();
      await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
      expect(new URL(page.url()).pathname).toBe(`/analysis/${methodId}`);
    }

    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
    await expect(page.getByTestId('method-card-weaving_segment')).toBeVisible();
    expect(new URL(page.url()).pathname).toBe('/new-analysis');
    await capture(page, 'phase3-remediation-desktop-navigation.png');
  });

  test('persistent method navigation protects a modified quick-analysis draft', async ({ page }) => {
    await page.goto('/analysis/two_lane_segment');
    await expect(page.getByTestId('phase3-form-two_lane_segment')).toBeVisible();
    await page.locator('#two_lane_segment-posted_speed').fill('65');

    let dismissedMessage = '';
    page.once('dialog', async (dialog) => {
      dismissedMessage = dialog.message();
      await dialog.dismiss();
    });
    await page.getByTestId('nav-method-weaving_segment').first().click();
    expect(dismissedMessage.toLowerCase()).toContain('discard');
    await expect(page.getByTestId('workflow-two_lane_segment')).toBeVisible();
    expect(new URL(page.url()).pathname).toBe('/analysis/two_lane_segment');

    page.once('dialog', async (dialog) => dialog.accept());
    await page.getByTestId('nav-method-weaving_segment').first().click();
    await expect(page.getByTestId('workflow-weaving_segment')).toBeVisible();
    expect(new URL(page.url()).pathname).toBe('/analysis/weaving_segment');
  });

  test('Two-Lane restores qualified schematics and uses structured curve editing', async ({ page }) => {
    await page.goto('/analysis/two_lane_segment');
    await expect(page.locator('[data-testid="two-lane-schematic"] img')).toHaveAttribute('data-asset-path', 'two_lane/passing_constrained.png');
    await page.getByRole('radio', { name: 'Passing zone', exact: true }).click();
    await expect(page.locator('[data-testid="two-lane-schematic"] img')).toHaveAttribute('data-asset-path', 'two_lane/passing_zone.png');
    await capture(page, 'phase3-remediation-two-lane-passing-schematic.png');

    await page.getByRole('radio', { name: 'Horizontal curves', exact: true }).click();
    const editor = page.getByTestId('two-lane-curve-editor');
    await expect(editor).toBeVisible();
    await expect(editor.locator('textarea')).toHaveCount(0);
    await editor.getByRole('button', { name: 'Generate from setup', exact: true }).click();
    await editor.getByRole('button', { name: 'Generate curve subsegments', exact: true }).click();
    await expect(editor.getByTestId('two-lane-curve-row-0')).toBeVisible();
    await capture(page, 'phase3-remediation-two-lane-curve-editor.png');
  });

  test('Weaving restores one-sided and two-sided references with advanced evidence disclosure', async ({ page }) => {
    await page.goto('/analysis/weaving_segment');
    const reference = page.getByTestId('weaving-reference');
    await expect(reference.locator('img')).toHaveAttribute('data-asset-path', 'weaving/one_sided_weave.png');
    await capture(page, 'phase3-remediation-weaving-one-sided.png');

    await page.getByRole('radio', { name: 'Two-sided', exact: true }).click();
    await expect(reference.locator('img')).toHaveAttribute('data-asset-path', 'weaving/two_sided_weave.png');
    await page.getByRole('button', { name: 'Advanced geometry / evidence', exact: true }).click();
    await expect(page.locator('#weaving_segment-nwl_basis')).toBeVisible();
    await capture(page, 'phase3-remediation-weaving-two-sided.png');
  });

  test('Merge and Diverge expose the existing detailed SVG assets in current results', async ({ page }) => {
    for (const [methodId, assetPath] of [
      ['merge_segment', 'ramp_influence/merge_right_on_ramp.svg'],
      ['diverge_segment', 'ramp_influence/diverge_right_off_ramp.svg'],
    ] as const) {
      await page.goto(`/analysis/${methodId}`);
      await page.getByRole('button', { name: 'Calculate', exact: true }).click();
      await expect(page.getByTestId('workflow-results')).toBeVisible();
      await expect(page.getByTestId('geometry-diagram').locator('img')).toHaveAttribute('data-asset-path', assetPath);
      await capture(page, `phase3-remediation-${methodId}-detailed-svg.png`);
    }
  });

  test('Basic Freeway capacity failure keeps unavailable predictions explicit', async ({ page }) => {
    await calculateWithFields(page, 'basic_freeway_segment', { demand_volume_veh_h: 10000 });

    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="handoff-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('F');
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
  });

  test('Weaving capacity failure stays distinct from the existing handoff state', async ({ page }) => {
    await calculateWithFields(page, 'weaving_segment', {
      volume_ff_veh_h: 10000,
      volume_fr_veh_h: 10000,
      volume_rf_veh_h: 10000,
      volume_rr_veh_h: 10000,
    });

    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="handoff-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('F');
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
  });

  test('Merge preserves ordinary, warning-only, and capacity-failure presentation states', async ({ page }) => {
    await calculateWithFields(page, 'merge_segment', {});
    await expect(page.locator('[data-slot="warning-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toHaveCount(0);

    await calculateWithFields(page, 'merge_segment', {
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
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('E');
    await expect(page.locator('[data-slot="warning-panel"]')).toContainText('Merge influence-area flow exceeds the maximum desirable level.');
    await expect(page.getByTestId('workflow-results')).not.toContainText('Not predicted in this state');
    await capture(page, 'phase3-remediation-merge-warning-state.png');

    await calculateWithFields(page, 'merge_segment', { freeway_demand_veh_h: 8000 });
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="warning-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('F');
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
  });

  test('Diverge preserves ordinary, warning-only, and capacity-failure presentation states', async ({ page }) => {
    await calculateWithFields(page, 'diverge_segment', {});
    await expect(page.locator('[data-slot="warning-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toHaveCount(0);

    await calculateWithFields(page, 'diverge_segment', {
      freeway_lanes: 2,
      freeway_demand_veh_h: 4000,
      ramp_demand_veh_h: 200,
      freeway_peak_hour_factor: 0.95,
      ramp_peak_hour_factor: 0.95,
      free_flow_speed: 104.60736,
      ramp_ffs: 64.37376,
      auxiliary_lane_length: 182.88,
    });
    await expect(page.locator('[data-slot="warning-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('E');
    await expect(page.locator('[data-slot="warning-panel"]')).toContainText('Diverge influence-area flow exceeds the maximum desirable level.');
    await expect(page.getByTestId('workflow-results')).not.toContainText('Not predicted in this state');
    await capture(page, 'phase3-remediation-diverge-warning-state.png');

    await calculateWithFields(page, 'diverge_segment', { ramp_demand_veh_h: 2300 });
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
    await expect(page.locator('[data-slot="warning-panel"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="result-hero"] .result-value')).toHaveText('F');
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
  });

  test('Multilane blank and estimated-FFS density semantics stay explicit', async ({ page }) => {
    await page.goto('/analysis/multilane_segment');
    await page.locator('#multilane-template').selectOption('blank_custom');
    await expect(page.locator('#multilane-access_point_density')).toHaveValue('0');
    await expect(page.getByText('Use 0 if there are no access points along the segment.', { exact: true })).toBeVisible();

    await page.goto('/analysis/multilane_segment');
    await page.locator('#multilane-access_point_density').fill('');
    await expect(page.locator('[data-slot="error-summary"]')).toHaveCount(0);
    await expect(page.locator('[data-slot="readiness-bar"] button')).toBeEnabled();
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.locator('.error-summary a[href="#multilane-access_point_density"]')).toBeVisible();
    await expect(page.locator('[data-slot="error-summary"]')).toBeFocused();
    await page.locator('#multilane-access_point_density').fill('0');
    await expect(page.locator('.error-summary a[href="#multilane-access_point_density"]')).toHaveCount(0);
  });

  test('current, stale, bilingual, and narrow states remain explicit', async ({ page }) => {
    await page.goto('/analysis/multilane_segment');
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.locator('.result-actions .button-primary')).toHaveCount(1);
    await capture(page, 'phase3-remediation-current-result.png');

    await page.locator('#multilane-demand_volume_veh_h').fill('1510');
    await expect(page.locator('[data-slot="stale-result-panel"]')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.locator('[data-slot="stale-result-panel"]')).toContainText('Unavailable until this stale result is recalculated.');
    await capture(page, 'phase3-remediation-stale-result.png');

    await page.getByRole('button', { name: 'Recalculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await page.getByRole('button', { name: 'Thai' }).click();
    await expect(page.getByText('ระดับการให้บริการ', { exact: true }).first()).toBeVisible();
    await capture(page, 'phase3-remediation-thai-result.png');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/analysis/weaving_segment');
    await expect(page.locator('.mobile-method-nav')).toBeVisible();
    const overflow = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth,
    }));
    expect(overflow.documentWidth).toBeLessThanOrEqual(overflow.viewportWidth + 1);
    await capture(page, 'phase3-remediation-narrow-navigation.png');
  });
});
