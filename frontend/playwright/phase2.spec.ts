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
    await download;
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await expect(page.getByText('2.0', { exact: true })).toBeVisible();
    await expect(page.getByText('Migrated', { exact: false })).not.toBeVisible();

    await page.getByRole('button', { name: 'Duplicate scenario' }).click();
    await expect(page.getByRole('button', { name: /Alternative/ })).toBeVisible();
    await page.getByRole('button', { name: /Alternative/ }).click();
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
});
