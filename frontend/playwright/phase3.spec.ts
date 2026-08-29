import { expect, test } from '@playwright/test';
import path from 'node:path';

const phase3Methods = [
  'two_lane_segment',
  'basic_freeway_segment',
  'weaving_segment',
  'merge_segment',
  'diverge_segment',
] as const;

const phase3ReferenceDirectory = path.resolve('..', 'docs', 'application_rebuild', 'visual-reference');

test.describe('Phase 3 full migration', () => {
  test('all seven registered methods are actionable from the normal method chooser', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await expect(page.getByText('7 calculation methods available', { exact: true })).toBeVisible();
    for (const methodId of [
      'two_lane_segment',
      'two_lane_facility',
      'multilane_segment',
      'basic_freeway_segment',
      'weaving_segment',
      'merge_segment',
      'diverge_segment',
    ]) {
      await expect(page.getByTestId(`method-card-${methodId}`).getByRole('button', { name: 'Start analysis' })).toBeEnabled();
    }
  });

  test('each Phase 3 workflow calculates and exposes engineering evidence', async ({ page }) => {
    for (const methodId of phase3Methods) {
      await page.goto('/');
      await page.getByRole('button', { name: 'New Analysis' }).first().click();
      await page.getByTestId(`method-card-${methodId}`).getByRole('button', { name: 'Start analysis' }).click();
      await expect(page.getByTestId(`phase3-form-${methodId}`)).toBeVisible();
      await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
      await page.getByRole('button', { name: 'Calculate', exact: true }).click();
      await expect(page.getByTestId('workflow-results')).toBeVisible();
      await expect(page.getByTestId('workflow-results')).toContainText('Analysis answer and metrics');
      if (methodId === 'weaving_segment' || methodId === 'merge_segment' || methodId === 'diverge_segment') {
        await expect(page.getByTestId('geometry-diagram')).toBeVisible();
      }
      await page.screenshot({
        path: path.join(phase3ReferenceDirectory, `phase3-${methodId}-result.png`),
        fullPage: true,
      });
    }
  });

  test('weaving length handoff keeps unavailable metrics distinct from capacity failure', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('button', { name: 'New Analysis' }).first().click();
    await page.getByTestId('method-card-weaving_segment').getByRole('button', { name: 'Start analysis' }).click();
    await expect(page.getByTestId('phase3-form-weaving_segment')).toBeVisible();
    await page.locator('#weaving_segment-segment_length').fill('5000');
    await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
    await page.getByRole('button', { name: 'Calculate', exact: true }).click();
    await expect(page.getByTestId('workflow-results')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toContainText('HCM method handoff');
    await expect(page.getByTestId('geometry-diagram')).toBeVisible();
    await expect(page.getByTestId('workflow-results')).toContainText('Not predicted in this state');
    await expect(page.locator('[data-slot="capacity-failure-panel"]')).toHaveCount(0);
  });
});
