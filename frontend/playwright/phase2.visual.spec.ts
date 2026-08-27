import { mkdirSync } from 'node:fs';
import path from 'node:path';
import { expect, test } from '@playwright/test';

const referenceDirectory = path.resolve('..', '.agent-work', 'visual-reference');

mkdirSync(referenceDirectory, { recursive: true });

function referencePath(name: string): string {
  return path.join(referenceDirectory, name);
}

test('captures the deterministic Phase 2 reference set', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('button', { name: 'New Analysis' }).first()).toBeVisible();
  await page.screenshot({ path: referencePath('01-home.png'), fullPage: true });

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByTestId('method-card-multilane_segment')).toBeVisible();
  await page.screenshot({ path: referencePath('02-new-analysis.png'), fullPage: true });

  await page.getByTestId('method-card-multilane_segment').getByRole('button', { name: 'Select method' }).click();
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await page.screenshot({ path: referencePath('03-multilane-result.png'), fullPage: true });

  await page.getByRole('button', { name: '← Back to methods' }).click();
  await page.getByTestId('method-card-two_lane_facility').getByRole('button', { name: 'Select method' }).click();
  await page.locator('#facility-template').selectOption('mountainous_example_4');
  await expect(page.getByTestId('facility-input-6-segment_length')).toHaveAttribute('readonly', '');
  await page.screenshot({ path: referencePath('04-facility-grid.png'), fullPage: true });
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await page.screenshot({ path: referencePath('05-facility-result.png'), fullPage: true });
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Save to Project' }).click();
  await download;
  await expect(page.getByTestId('project-workspace')).toBeVisible();
  await page.getByRole('button', { name: 'Duplicate scenario' }).click();
  await page.getByRole('button', { name: /Alternative/ }).click();
  await page.getByRole('button', { name: 'Edit scenario' }).click();
  await page.getByTestId('facility-input-1-posted_speed').fill('45');
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await page.getByRole('button', { name: 'Save scenario result' }).click();
  await expect(page.getByTestId('project-workspace')).toBeVisible();
  const selects = page.locator('.project-controls select');
  await selects.nth(0).selectOption({ label: 'Base' });
  await selects.nth(1).selectOption({ label: 'Alternative' });
  await page.getByRole('button', { name: 'Compare', exact: true }).click();
  await expect(page.getByTestId('comparison-result')).toBeVisible();
  await page.screenshot({
    path: referencePath('06-project-compare.png'),
    fullPage: true,
    mask: [page.locator('.project-facts strong').nth(2), page.locator('.project-identity code')],
  });
});
