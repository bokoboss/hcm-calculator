import { expect, test } from '@playwright/test';

test('Facility template selector localizes labels without changing template IDs', async ({ page }) => {
  await page.goto('/analysis/two_lane_facility');
  const selector = page.locator('#facility-template');

  await expect(selector).toHaveValue('level_example_3');
  await expect(selector).toContainText('Facility template — Chapter 26 Example 3');

  await page.getByRole('button', { name: 'Thai', exact: true }).click();
  await expect(selector).toHaveValue('level_example_3');
  await expect(selector).toContainText('แม่แบบสิ่งอำนวยความสะดวก — ตัวอย่างบทที่ 26 ข้อ 3');
  await expect(selector).not.toContainText('Facility template — Chapter 26 Example');

  await selector.selectOption('mountainous_example_4');
  await expect(selector).toHaveValue('mountainous_example_4');
  await expect(selector).toContainText('แม่แบบสิ่งอำนวยความสะดวก — ตัวอย่างบทที่ 26 ข้อ 4');

  await page.getByRole('button', { name: 'อังกฤษ', exact: true }).click();
  await expect(selector).toHaveValue('mountainous_example_4');
  await expect(selector).toContainText('Facility template — Chapter 26 Example 4');

  await page.getByRole('button', { name: 'Thai', exact: true }).click();
  await expect(selector).toHaveValue('mountainous_example_4');
  await expect(selector).not.toContainText('Facility template — Chapter 26 Example');
});
