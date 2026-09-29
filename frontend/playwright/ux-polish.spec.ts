import { expect, test } from '@playwright/test';

async function expectNoGlobalHorizontalOverflow(page: Parameters<typeof test>[0]['page']): Promise<void> {
  const overflow = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    body: document.body.scrollWidth - document.body.clientWidth,
  }));
  expect(overflow.document).toBeLessThanOrEqual(1);
  expect(overflow.body).toBeLessThanOrEqual(1);
}

test('UX polish keeps method shortcuts contextual and improves reading hierarchy', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'HCM Calculator' })).toBeVisible();

  const twoLaneShortcuts = page.getByTestId('nav-method-two_lane_segment');
  await expect(twoLaneShortcuts).toHaveCount(2);
  await expect(twoLaneShortcuts.nth(0)).toBeHidden();
  await expect(twoLaneShortcuts.nth(1)).toBeHidden();

  const homeSections = page.locator('.home-page .engineering-section');
  await expect(homeSections).toHaveCount(3);
  await expect(page.locator('.home-page')).toHaveCSS('display', 'grid');
  expect(Number.parseFloat(await page.locator('.method-family').first().evaluate((node) => getComputedStyle(node).fontSize))).toBeGreaterThanOrEqual(11);

  await page.getByRole('button', { name: 'New Analysis' }).first().click();
  await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();
  await expect(twoLaneShortcuts.nth(0)).toBeVisible();
  await expect(twoLaneShortcuts.nth(1)).toBeHidden();

  await page.getByRole('button', { name: 'HCM Analysis Guide' }).click();
  await expect(page.getByRole('heading', { name: 'HCM Analysis Handbook' })).toBeVisible();
  await expect(twoLaneShortcuts.nth(0)).toBeHidden();
  await expect(twoLaneShortcuts.nth(1)).toBeHidden();
  await expect(page.locator('.handbook-article')).toHaveCount(1);
  await expect(page.locator('.handbook-section')).toHaveCount(5);
  await expectNoGlobalHorizontalOverflow(page);
});

test('UX polish preserves compact mobile navigation without overflow', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/new-analysis');
  await expect(page.getByRole('heading', { name: 'New Analysis' })).toBeVisible();

  const twoLaneShortcuts = page.getByTestId('nav-method-two_lane_segment');
  await expect(twoLaneShortcuts).toHaveCount(2);
  await expect(twoLaneShortcuts.nth(0)).toBeHidden();
  await expect(page.locator('.mobile-method-nav')).toBeVisible();

  await page.locator('.mobile-method-nav summary').click();
  await expect(twoLaneShortcuts.nth(1)).toBeVisible();
  await expectNoGlobalHorizontalOverflow(page);

  await page.goto('/reference/weaving_segment');
  await expect(page.getByTestId('reference-weaving_segment')).toBeVisible();
  await expect(page.locator('.mobile-method-nav')).toBeHidden();
  await expectNoGlobalHorizontalOverflow(page);
});
