import { expect, test } from '@playwright/test';

test('release-like Python-served shell exposes safe discovery and localization', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'HCM Calculator' })).toBeVisible();
  await expect(page.getByText('API connected')).toBeVisible();

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
  await expect(page.getByText('7 calculation methods available')).toBeVisible();
  const methodButtons = page.getByRole('button', { name: 'Start analysis' });
  await expect(methodButtons).toHaveCount(8);
  expect(await methodButtons.evaluateAll((buttons) => buttons.filter((button) => !(button as HTMLButtonElement).disabled))).toHaveLength(7);
  const chapter18Card = page.getByTestId('method-card-urban_street_segment');
  await expect(chapter18Card.getByText('Reference only')).toBeVisible();
  await expect(chapter18Card.getByRole('button', { name: 'Start analysis' })).toBeDisabled();

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

test('backend-only Chapter 18 stays reference-only and localized without a false guide', async ({ page }) => {
  await page.goto('/new-analysis');
  const chapter18Card = page.getByTestId('method-card-urban_street_segment');
  await expect(chapter18Card.getByRole('button', { name: 'Start analysis' })).toBeDisabled();
  await expect(chapter18Card.getByRole('button', { name: 'Analysis guide' })).toHaveCount(0);
  await expect(chapter18Card.getByText('Urban Street Segment')).toBeVisible();
  await expect(chapter18Card.getByText(/Bounded signalized 15-minute segment/i)).toBeVisible();
  await expect(chapter18Card).not.toContainText('method.urban_street_segment.name');
  await expect(chapter18Card).not.toContainText('method.urban_streets');

  await page.getByRole('button', { name: 'Thai' }).click();
  await expect(chapter18Card.getByText('ช่วงถนนเขตเมือง')).toBeVisible();
  await expect(chapter18Card).toContainText('สัญญาณไฟ 15 นาที');
  await expect(chapter18Card).not.toContainText('method.urban_street_segment.name');
  await expect(chapter18Card).not.toContainText('method.urban_streets');
  await expect(chapter18Card).toContainText('RHT');
  await expect(chapter18Card).toContainText('LHT');

  await page.getByRole('button', { name: 'อังกฤษ' }).click();
  await page.goto('/reference/urban_street_segment');
  await expect(page.getByText('No method guide is available for this selection.')).toBeVisible();
  await expect(page.getByTestId('reference-two_lane_segment')).toHaveCount(0);
  await page.goto('/reference/unknown_method');
  await expect(page.getByText('No method guide is available for this selection.')).toBeVisible();
  await expect(page.getByTestId('reference-two_lane_segment')).toHaveCount(0);
});
