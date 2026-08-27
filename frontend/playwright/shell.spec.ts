import { expect, test } from '@playwright/test';

test('release-like Python-served shell exposes safe discovery and localization', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Highway Capacity Analysis' })).toBeVisible();
  await expect(page.getByText('API connected')).toBeVisible();

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
  await expect(page.getByText('2 rebuilt workflows delivered')).toBeVisible();
  await expect(page.getByText('Reference only').first()).toBeVisible();
  const methodButtons = page.getByRole('button', { name: 'Select method' });
  await expect(methodButtons).toHaveCount(7);
  expect(await methodButtons.evaluateAll((buttons) => buttons.filter((button) => !(button as HTMLButtonElement).disabled))).toHaveLength(2);

  await page.getByRole('button', { name: 'Supported Methods' }).first().click();
  await expect(page.getByRole('heading', { name: 'Supported Methods' })).toBeVisible();
  await expect(page.getByTestId('reference-multilane_segment')).toBeVisible();

  await page.getByRole('button', { name: 'Thai' }).click();
  await expect(page.getByRole('heading', { name: 'วิธีที่รองรับ' })).toBeVisible();
  await page.getByRole('button', { name: 'อังกฤษ' }).click();
  await expect(page.getByRole('heading', { name: 'Supported Methods' })).toBeVisible();
});
