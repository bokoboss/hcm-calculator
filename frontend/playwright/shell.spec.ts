import { expect, test } from '@playwright/test';

test('release-like Python-served shell exposes safe discovery and localization', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'HCM Calculator' })).toBeVisible();
  await expect(page.getByText('API connected')).toBeVisible();

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
  await expect(page.getByText('7 calculation methods available')).toBeVisible();
  const methodButtons = page.getByRole('button', { name: 'Start analysis' });
  await expect(methodButtons).toHaveCount(7);
  expect(await methodButtons.evaluateAll((buttons) => buttons.filter((button) => !(button as HTMLButtonElement).disabled))).toHaveLength(7);

  await page.getByRole('button', { name: 'Analysis guide' }).first().click();
  await expect(page.getByRole('heading', { name: 'HCM Analysis Handbook' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Choose the right workflow' })).toBeVisible();
  await expect(page.getByTestId('reference-multilane_segment')).toBeVisible();
  await expect(page.getByTestId('reference-weaving_segment').getByRole('heading', { name: 'Prepare these inputs' })).toBeVisible();

  await page.getByRole('button', { name: 'Thai' }).click();
  await expect(page.getByRole('heading', { name: 'คู่มือการวิเคราะห์ HCM' })).toBeVisible();
  await page.getByRole('button', { name: 'อังกฤษ' }).click();
  await expect(page.getByRole('heading', { name: 'HCM Analysis Handbook' })).toBeVisible();
});
