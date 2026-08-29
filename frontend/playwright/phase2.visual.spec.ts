import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { expect, test, type Page } from '@playwright/test';

const referenceDirectory = path.resolve('..', 'docs', 'application_rebuild', 'visual-reference');

mkdirSync(referenceDirectory, { recursive: true });

async function capture(page: Page, name: string, projectView = false): Promise<void> {
  await page.screenshot({
    path: path.join(referenceDirectory, name),
    fullPage: true,
    mask: projectView
      ? [page.locator('.project-topbar strong')]
      : undefined,
  });
}

async function selectMethod(page: Page, methodId: string): Promise<void> {
  await page.getByTestId(`method-card-${methodId}`).getByRole('button').first().click();
}

test('captures the deterministic Phase 2 reference set', async ({ page }) => {
  test.setTimeout(120_000);

  await page.goto('/');
  await expect(page.getByRole('button', { name: 'New Analysis' }).first()).toBeVisible();
  await capture(page, '01-home-desktop.png');

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByTestId('method-card-multilane_segment')).toBeVisible();
  await capture(page, '02-new-analysis-desktop.png');

  await selectMethod(page, 'multilane_segment');
  await expect(page.getByTestId('workflow-multilane_segment')).toBeVisible();
  await expect(page.locator('#multilane-template')).toBeVisible();
  await capture(page, '03-multilane-input.png');
  await page.locator('[data-slot="readiness-bar"] button').click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await capture(page, '04-multilane-result.png');

  await page.locator('#multilane-demand_volume_veh_h').fill('1900');
  await expect(page.locator('[data-slot="stale-result-panel"]')).toBeVisible();
  await capture(page, '05-multilane-stale.png');
  await page.getByRole('button', { name: 'Recalculate', exact: true }).click();
  await expect(page.locator('[data-slot="stale-result-panel"]')).toHaveCount(0);
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await page.locator('#multilane-demand_volume_veh_h').fill('5000');
  await expect(page.locator('[data-slot="stale-result-panel"]')).toBeVisible();
  await page.getByRole('button', { name: 'Recalculate', exact: true }).click();
  await expect(page.locator('[data-slot="capacity-failure-panel"]')).toBeVisible();
  await capture(page, '06-multilane-capacity-failure.png');

  await page.locator('.workflow-toolbar button').click();
  await selectMethod(page, 'two_lane_facility');
  await expect(page.getByTestId('facility-input-1-lane_width')).toHaveValue(/3\.6576/);
  await capture(page, '07-facility-grid.png');
  await page.getByTestId('facility-input-1-peak_hour_factor').fill('0');
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.locator('[data-slot="error-summary"]')).toBeVisible();
  await capture(page, '08-facility-validation.png');
  await page.getByTestId('facility-input-1-peak_hour_factor').fill('0.94');
  await page.locator('[data-slot="readiness-bar"] button').click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await capture(page, '09-facility-result.png');

  const projectDownload = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save to Project' }).click();
  await projectDownload;
  await expect(page.getByTestId('project-workspace')).toBeVisible();
  await capture(page, '10-project-v2-overview.png', true);

  await page.locator('.scenario-actions-menu > summary').click();
  await page.getByRole('button', { name: 'Duplicate scenario' }).click();
  await page.getByRole('button', { name: /Alternative/ }).click();
  await page.getByRole('button', { name: 'Edit scenario' }).click();
  await page.getByTestId('facility-input-1-posted_speed').fill('45');
  await page.locator('[data-slot="readiness-bar"] button').click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await page.getByRole('button', { name: 'Save scenario result' }).click();
  await expect(page.getByTestId('project-workspace')).toBeVisible();
  const compareSelects = page.locator('.project-controls select');
  await compareSelects.nth(0).selectOption({ label: 'Base' });
  await compareSelects.nth(1).selectOption({ label: 'Alternative' });
  await page.getByRole('button', { name: 'Compare', exact: true }).click();
  await expect(page.getByTestId('comparison-result')).toBeVisible();
  await capture(page, '11-project-compare.png', true);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await selectMethod(page, 'multilane_segment');
  await expect(page.getByTestId('workflow-multilane_segment')).toBeVisible();
  await capture(page, '12-narrow-analysis.png');
  await page.locator('.workflow-toolbar button').click();
  await selectMethod(page, 'two_lane_facility');
  await expect(page.getByTestId('facility-input-1-lane_width')).toBeVisible();
  await capture(page, '13-narrow-facility-grid.png');

  await page.setViewportSize({ width: 1280, height: 900 });
  await page.locator('.workflow-toolbar button').click();
  await selectMethod(page, 'multilane_segment');
  await page.getByRole('button', { name: 'Thai' }).click();
  await page.locator('[data-slot="readiness-bar"] button').click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await capture(page, '14-thai-multilane-result.png');
  await page.locator('.workflow-toolbar button').click();
  await selectMethod(page, 'two_lane_facility');
  await page.locator('[data-slot="readiness-bar"] button').click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await capture(page, '15-thai-facility-result.png');
});
