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
  await expect(page.getByTestId('reference-two_lane_segment')).toBeVisible();
  await expect(page.getByTestId('reference-basic_freeway_segment')).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Key inputs and concepts' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'How the method works' })).toBeVisible();

  await page.goto('/reference/weaving_segment');
  await expect(page).toHaveURL(/\/reference\/weaving_segment$/);
  const weavingGuide = page.getByTestId('reference-weaving_segment');
  await expect(weavingGuide).toBeVisible();
  await expect(weavingGuide.getByText('LS and LMAX')).toBeVisible();
  await expect(weavingGuide.getByText(/LS ≥ LMAX is not a poor weaving LOS/)).toBeVisible();

  await page.getByRole('button', { name: 'Thai' }).click();
  await expect(page.getByRole('heading', { name: 'คู่มือการวิเคราะห์ HCM' })).toBeVisible();
  await expect(page.getByTestId('reference-weaving_segment').getByText('LS และ LMAX')).toBeVisible();
  await page.getByRole('button', { name: 'อังกฤษ' }).click();
  await expect(page.getByRole('heading', { name: 'HCM Analysis Handbook' })).toBeVisible();
});
