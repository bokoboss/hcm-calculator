import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const referenceDirectory = path.resolve('..', 'docs', 'application_rebuild', 'visual-reference');
mkdirSync(referenceDirectory, { recursive: true });

async function capture(page: Page, name: string): Promise<void> {
  await page.screenshot({ path: path.join(referenceDirectory, name), fullPage: true });
}

async function calculate(page: Page, methodId: string, values: Record<string, number> = {}): Promise<void> {
  await page.goto(`/analysis/${methodId}`);
  for (const [field, value] of Object.entries(values)) {
    await page.locator(`#${methodId}-${field}`).fill(String(value));
  }
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
}

test.describe('Final bounded remediation evidence', () => {
  test('Facility identity stays readable while its numeric values remain presentation-only', async ({ page }) => {
    await page.setViewportSize({ width: 1366, height: 768 });
    await page.goto('/analysis/two_lane_facility');
    const scrollRegion = page.locator('.facility-workspace .table-scroll').first();
    await expect(scrollRegion).toBeVisible();
    await expect(page.locator('.facility-table th')).toHaveCount(16);
    await capture(page, 'final-facility-en-1366-left.png');

    const identityBefore = await page.locator('.facility-table tbody tr').first().locator('td').evaluateAll((cells) => cells.slice(0, 2).map((cell) => cell.getBoundingClientRect().x));
    await scrollRegion.evaluate((element) => { element.scrollLeft = element.scrollWidth; });
    const identityAfter = await page.locator('.facility-table tbody tr').first().locator('td').evaluateAll((cells) => cells.slice(0, 2).map((cell) => cell.getBoundingClientRect().x));
    expect(identityAfter).toEqual(identityBefore);
    await expect(page.getByTestId('facility-input-1-segment_name')).toHaveValue('Segment 1');
    await capture(page, 'final-facility-en-1366-right.png');

    await page.setViewportSize({ width: 1024, height: 768 });
    await capture(page, 'final-facility-en-1024-right.png');
    const overflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
    expect(overflow.width).toBeLessThanOrEqual(overflow.viewport + 1);

    await page.setViewportSize({ width: 1366, height: 768 });
    await page.getByRole('button', { name: 'Thai' }).click();
    await expect(page.getByRole('columnheader', { name: 'ความชัน (%)', exact: true })).toBeVisible();
    await capture(page, 'final-facility-th-1366.png');

    await page.goto('/analysis/two_lane_facility');
    await page.locator('#facility-unit-system').selectOption('metric');
    const facilityNumeric = page.getByTestId('facility-input-1-segment_length');
    await expect(facilityNumeric).not.toHaveValue(/0000000/);
    await capture(page, 'final-converted-facility-values.png');
  });

  test('validation and operational warnings use localized normal-user summaries', async ({ page }) => {
    await page.goto('/analysis/multilane_segment');
    await page.locator('#multilane-access_point_density').fill('');
    await expect(page.locator('#multilane-access_point_density')).toHaveValue('');
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    const summary = page.locator('[data-slot="error-summary"]');
    await expect(summary).toContainText('Access-point density');
    await expect(summary).not.toContainText('access_point_density');
    await capture(page, 'final-validation-readable.png');

    await calculate(page, 'merge_segment', {
      freeway_lanes: 2,
      freeway_demand_veh_h: 3600,
      ramp_demand_veh_h: 600,
      freeway_peak_hour_factor: 0.95,
      ramp_peak_hour_factor: 0.95,
      free_flow_speed: 104.60736,
      ramp_ffs: 64.37376,
      auxiliary_lane_length: 182.88,
    });
    await page.getByRole('button', { name: 'Thai' }).click();
    const warning = page.locator('[data-slot="warning-panel"]');
    await expect(warning).toContainText('เกินระดับที่พึงประสงค์สูงสุด');
    await expect(warning).not.toContainText('Maximum desirable merge influence-area flow');
    await page.getByRole('button', { name: 'หลักฐานตรวจสอบและตัวตนผลลัพธ์', exact: true }).click();
    await expect(page.getByText('Maximum desirable merge influence-area flow is exceeded; this is an interpretation warning, not automatic LOS F.')).toBeVisible();
    await capture(page, 'final-th-warning.png');
  });

  test('converted inputs avoid floating artifacts and mobile Thai export remains usable', async ({ page }) => {
    const validationPayloads: Array<{ unit_system: string; displayed_inputs: Record<string, unknown> }> = [];
    page.on('request', (request) => {
      if (request.url().endsWith('/api/v1/analyses/multilane_segment/validate')) {
        validationPayloads.push(request.postDataJSON() as { unit_system: string; displayed_inputs: Record<string, unknown> });
      }
    });
    await page.goto('/analysis/multilane_segment');
    await page.locator('#multilane-unit-system').selectOption('metric');
    const convertedValue = page.locator('#multilane-lane_width');
    await expect(convertedValue).not.toHaveValue(/0000000/);
    await expect.poll(() => validationPayloads.some((payload) => payload.unit_system === 'metric')).toBe(true);
    const convertedPayload = validationPayloads.find((payload) => payload.unit_system === 'metric');
    expect(convertedPayload?.displayed_inputs.lane_width).toBe(3.6576000000000004);
    await capture(page, 'final-converted-segment-values.png');
    await convertedValue.fill('3.5');
    await expect(convertedValue).toHaveValue('3.5');
    await expect.poll(() => validationPayloads.some((payload) => payload.displayed_inputs.lane_width === 3.5)).toBe(true);

    await page.setViewportSize({ width: 390, height: 844 });
    await calculate(page, 'multilane_segment');
    await page.getByRole('button', { name: 'Thai' }).click();
    await page.getByRole('button', { name: 'ส่งออก' }).click();
    await expect(page.locator('.export-menu-content')).toBeVisible();
    const overflow = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: window.innerWidth }));
    expect(overflow.width).toBeLessThanOrEqual(overflow.viewport + 1);
    await capture(page, 'final-th-mobile-result-export-390.png');
  });
});
