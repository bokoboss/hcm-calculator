import { expect, test, type Page } from '@playwright/test';
import path from 'node:path';
import { readFileSync } from 'node:fs';
import type { WorkflowStartingValuesResponse } from '../src/api/types';
const fixture = JSON.parse(readFileSync(path.resolve('src/app/lhtWorkflowFixture.json'), 'utf8')) as { starting: WorkflowStartingValuesResponse };

const id = 'urban_street_segment_th_lht';
const route = `/analysis/${id}`;
const fields = fixture.starting.fields;
const values = fixture.starting.displayed_inputs as Record<string, unknown>;
const field = (page: Page, key: string) => page.locator(`#${id}-${key}`);

async function open(page: Page) {
  await page.goto(route);
  await expect(field(page, 'segment_length')).toHaveValue(String(values.segment_length));
  await expect(page.getByRole('button', { name: 'Calculate', exact: true })).toBeEnabled();
}
async function calculate(page: Page) {
  await page.getByRole('button', { name: /^(Calculate|Recalculate)$/, exact: true }).click();
  await expect(page.getByTestId('workflow-results')).toBeVisible();
  await expect(page.locator('[data-slot="stale-result-panel"]')).toHaveCount(0);
}
async function invalid(page: Page, key: string) {
  await page.getByRole('button', { name: 'Calculate', exact: true }).click();
  const link = page.locator(`#error-summary a[href="#${id}-${key}"]`).first();
  await expect(link).toBeVisible();
  await expect(page.locator('#error-summary')).toBeFocused();
  await link.focus();
  await link.press('Enter');
  await expect(field(page, key)).toBeFocused();
}

test.describe('Chapter 18 Thailand/LHT production qualification', () => {
  test.setTimeout(90_000);

  test('shows boundary overview and fixed method conditions without one-option radios', async ({ page }) => {
    const initialValidation = page.waitForRequest((request) => request.url().endsWith(`/${id}/validate`) && request.method() === 'POST');
    await open(page);
    const validationInputs = (await initialValidation).postDataJSON().displayed_inputs as Record<string, unknown>;
    expect(validationInputs.control_type).toBe('signalized');
    expect(validationInputs.external_control_type).toBe('signalized');
    const worksheet = page.getByTestId(`phase3-form-${id}`);
    await expect(worksheet.getByRole('region', { name: 'Boundary overview' })).toBeVisible();
    await expect(worksheet.getByText('Upstream boundary', { exact: true })).toBeVisible();
    await expect(worksheet.getByText('Analyzed segment', { exact: true })).toBeVisible();
    await expect(worksheet).toContainText('L_s is the spacing between the applicable bracketing controls that require the subject through movement to stop or yield. It may differ from segment length.');
    await expect(worksheet.getByText('Downstream boundary', { exact: true })).toBeVisible();
    await expect(worksheet.getByRole('status').filter({ hasText: 'Fixed by current qualified method' })).toBeVisible();
    await expect(worksheet.getByRole('group', { name: 'Downstream boundary control type' })).toHaveCount(0);
    await expect(worksheet.getByRole('group', { name: 'External downstream control type' })).toHaveCount(0);
    await expect(worksheet.getByRole('radio', { name: 'Signalized', exact: true })).toHaveCount(0);
    await expect(worksheet).toContainText('Upstream intersection performance and delay are not calculated');
    await expect(worksheet).toContainText('v_th, c_th and d_t come from qualified external downstream analysis');
  });

  test('restored invalid fixed controls expose backend errors and recover only the affected field', async ({ page }) => {
    for (const key of ['control_type', 'external_control_type']) {
      await page.route(`**/api/v1/analyses/${id}/starting-values?**`, async (route) => {
        const response = await route.fetch();
        const body = await response.json();
        body.displayed_inputs[key] = null;
        await route.fulfill({ response, json: body });
      });
      const beforeValidation = page.waitForRequest((request) => request.url().endsWith(`/${id}/validate`) && request.method() === 'POST');
      await page.goto(route);
      const before = (await beforeValidation).postDataJSON().displayed_inputs as Record<string, unknown>;
      const fixed = page.locator(`#${id}-${key}`);
      await expect(fixed).toContainText('Required value: Signalized');
      await expect(fixed.getByText('Signalized', { exact: true })).toHaveCount(0);
      await expect(fixed.getByRole('status')).toHaveCount(0);
      await expect(fixed).toContainText(/must be signalized/i);
      await expect(fixed.getByRole('button', { name: 'Use required value: Signalized', exact: true })).toBeVisible();
      await page.getByRole('button', { name: 'Thai', exact: true }).click();
      await expect(fixed).toContainText('ค่าที่วิธีกำหนด: สัญญาณไฟ');
      await expect(fixed.getByText('สัญญาณไฟ', { exact: true })).toHaveCount(0);
      await page.getByRole('button', { name: 'อังกฤษ', exact: true }).click();
      await page.getByRole('button', { name: 'Calculate', exact: true }).click();
      const summaryLink = page.locator(`#error-summary a[href="#${id}-${key}"]`).first();
      await expect(summaryLink).toBeVisible();
      await summaryLink.focus();
      await summaryLink.press('Enter');
      await expect(fixed).toBeFocused();
      const validation = page.waitForRequest((request) => request.url().endsWith(`/${id}/validate`) && request.method() === 'POST');
      const recovery = fixed.getByRole('button', { name: 'Use required value: Signalized', exact: true });
      await recovery.focus();
      await recovery.press('Enter');
      const restored = (await (await validation).postDataJSON()).displayed_inputs as Record<string, unknown>;
      expect(restored[key]).toBe('signalized');
      expect(restored[key === 'control_type' ? 'external_control_type' : 'control_type']).toBe('signalized');
      expect(Object.fromEntries(Object.entries(restored).filter(([name]) => name !== key))).toEqual(Object.fromEntries(Object.entries(before).filter(([name]) => name !== key)));
      await expect(fixed.getByRole('button')).toHaveCount(0);
      await expect(fixed.getByText('Signalized', { exact: true })).toBeVisible();
      await expect(fixed.getByRole('status')).toHaveText(key === 'control_type' ? 'Fixed by current qualified method' : 'Must match downstream boundary');
      await expect(fixed.getByText('Required value: Signalized', { exact: true })).toHaveCount(0);
      await page.getByRole('button', { name: 'Thai', exact: true }).click();
      await expect(fixed.getByText('สัญญาณไฟ', { exact: true })).toBeVisible();
      await expect(fixed.getByText('ค่าที่วิธีกำหนด: สัญญาณไฟ', { exact: true })).toHaveCount(0);
      await expect(fixed.getByRole('status')).toHaveText(key === 'control_type' ? 'กำหนดโดยขอบเขตของวิธีที่ผ่านการรับรอง' : 'ต้องตรงกับทางแยกปลายทาง');
      await expect(fixed.getByRole('button')).toHaveCount(0);
      await page.getByRole('button', { name: 'อังกฤษ', exact: true }).click();
      await page.unroute(`**/api/v1/analyses/${id}/starting-values?**`);
    }
  });

  test('delivers only LHT, opens direct/history routes and bilingual Handbook', async ({ page }) => {
    await page.goto('/new-analysis');
    await expect(page.getByText('8 calculation methods available', { exact: true })).toBeVisible();
    const lht = page.getByTestId(`method-card-${id}`);
    await expect(lht.getByRole('button', { name: 'Start analysis' })).toBeEnabled();
    await expect(page.getByTestId('method-card-urban_street_segment').getByRole('button', { name: 'Start analysis' })).toBeDisabled();
    await lht.getByRole('button', { name: 'Analysis guide' }).click();
    const guide = page.getByTestId(`reference-${id}`);
    await expect(guide).toContainText('Physical left for each direction');
    await expect(guide).toContainText('already coordinated final delay');
    await expect(guide).toContainText('upstream boundary may be signalized or non-signalized');
    await expect(guide).toContainText('The immediate upstream boundary may be signalized, STOP-controlled, YIELD-controlled (including subject through movements that must stop or yield), or through-uncontrolled.');
    await expect(guide).toContainText('No upstream intersection performance or delay is calculated');
    await expect(guide).toContainText('d_t remains qualified downstream through delay');
    await expect(guide).toContainText('Case A: STOP/YIELD-controlled upstream');
    await expect(guide).toContainText('Case B: through-uncontrolled TWSC upstream');
    await expect(guide).toContainText('through-uncontrolled TWSC upstream');
    await expect(guide).toContainText('urban street segment → signalized downstream boundary');
    await expect(guide).toContainText('Downstream unsignalized control types remain deferred');
    await page.getByRole('button', { name: 'Thai', exact: true }).click();
    await expect(guide).toContainText('ด้านซ้ายกายภาพ');
    await expect(guide).toContainText('ไม่ใช่การสอบเทียบเชิงประจักษ์');
    await expect(guide).toContainText('ทางแยกต้นน้ำที่ติดกับช่วงทางโดยตรงอาจมีหรือไม่มีสัญญาณไฟ');
    await expect(guide).toContainText('รวมถึงกรณี STOP/YIELD ที่บังคับให้จราจรตรงที่วิเคราะห์หยุดหรือให้ทาง');
    await expect(guide).toContainText('ไม่มีการคำนวณสมรรถนะหรือความล่าช้าของทางแยกต้นน้ำ');
    await expect(guide).toContainText('d_t คือความล่าช้าจราจรตรงปลายทางสุดท้ายที่ผ่านการประเมิน');
    await expect(guide).toContainText('กรณี A: ทางแยก STOP/YIELD ต้นน้ำ');
    await expect(guide).toContainText('กรณี B: TWSC ต้นน้ำที่จราจรตรงไม่ถูกควบคุม');
    await expect(guide).toContainText('TWSC ต้นน้ำไม่บังคับให้จราจรตรงหยุดหรือให้ทาง');
    await expect(guide).toContainText('การควบคุมปลายทางที่ไม่มีสัญญาณไฟยังอยู่ระหว่างรอการพัฒนา');
    await expect(guide).not.toContainText(`guide.${id}`);
    await page.getByRole('button', { name: 'อังกฤษ' }).click();
    await page.goBack();
    await lht.getByRole('button', { name: 'Start analysis' }).click();
    await expect(page).toHaveURL(new RegExp(`${route}$`));
    await page.goBack();
    await expect(page).toHaveURL(/\/new-analysis$/);
    await page.goForward();
    await expect(field(page, 'segment_length')).toBeVisible();
    await page.getByRole('button', { name: 'Thai', exact: true }).click();
    await expect(page.locator(`#${id}-control_type`)).toContainText('สัญญาณไฟ');
    await expect(page.getByText(/L_s คือระยะระหว่างจุดควบคุมต้นและปลายที่เกี่ยวข้องซึ่งบังคับให้จราจรตรงในทิศทางที่วิเคราะห์ต้องหยุดหรือให้ทาง และอาจไม่เท่ากับความยาวช่วงทาง/)).toBeVisible();
    await expect(page.getByLabel('ระยะระหว่างจุดควบคุม L_s')).toBeVisible();
    await expect(page.getByText(/จุดควบคุมที่เกี่ยวข้องซึ่งบังคับให้การเคลื่อนที่ตรงในทิศทางที่วิเคราะห์ต้องหยุดหรือให้ทาง/)).toBeVisible();
    await page.getByRole('button', { name: 'อังกฤษ', exact: true }).click();
    await expect(page.locator(`#${id}-control_type`)).toContainText('Signalized');
    await expect(page.getByLabel('Control spacing, L_s')).toBeVisible();
    await expect(page.getByText(/Distance between the applicable bracketing controls that require the subject through movement to stop or yield/i)).toBeVisible();
    await expect(page.getByText(/Geometry of the immediate upstream boundary intersection/i)).toBeVisible();
    await page.goto('/analysis/urban_street_segment');
    await expect(page).toHaveURL(/\/new-analysis$/);
  });

  test('calculates the accepted fixture, orders metrics, preserves locale, marks stale and exports all four formats', async ({ page }) => {
    await open(page);
    const responsePromise = page.waitForResponse((response) => response.url().endsWith(`/${id}/calculate`));
    await calculate(page);
    const snapshot = await (await responsePromise).json();
    expect(snapshot.result.outputs.level_of_service).toBe('C');
    await expect(page.locator('[data-slot="result-hero"]')).toContainText('C');
    const result = page.getByTestId('workflow-results');
    expect(await result.locator('[data-slot="metric-card"] p').allTextContents()).toEqual(['Travel speed', 'Through v/c', 'Running speed', 'Total travel time', 'Running time']);
    await page.getByRole('button', { name: 'Thai', exact: true }).click();
    await expect(field(page, 'segment_length')).toHaveValue(String(values.segment_length));
    await expect(result).toContainText('ความเร็วเดินทาง');
    await expect(result).not.toContainText('result.metric.');
    await page.getByRole('button', { name: 'อังกฤษ' }).click();
    await field(page, 'd_other_s_veh').fill('1.25');
    await expect(page.locator('[data-slot="stale-result-panel"]')).toBeVisible();
    await expect(page.getByRole('button', { name: /^Export/ })).toHaveCount(0);
    await calculate(page);
    for (const [format, extension] of [['JSON', 'json'], ['Markdown', 'md'], ['CSV', 'csv'], ['XLSX', 'xlsx']]) {
      await page.getByRole('button', { name: /^Export/ }).click();
      const exported = page.waitForResponse((response) => response.url().endsWith(`/${id}/export`));
      const downloaded = page.waitForEvent('download');
      await page.getByRole('menuitem', { name: `Export ${format}`, exact: true }).click();
      const payload = await (await exported).json();
      expect(payload.recalculated).toBe(false);
      expect((await downloaded).suggestedFilename()).toMatch(new RegExp(`\\.${extension}$`));
    }
  });

  test('keyboard list editing and backend boolean/list validation recover without coercion', async ({ page }) => {
    await open(page);
    const list = field(page, 'access_point_delays_s_veh');
    const add = list.getByRole('button', { name: /Add item/ });
    await add.focus();
    await page.keyboard.press('Enter');
    const item = list.getByRole('spinbutton').last();
    await expect(item).toBeFocused();
    await invalid(page, 'access_point_delays_s_veh');
    await item.fill('1.234567');
    await expect(item).toHaveValue('1.234567');
    await list.getByRole('button', { name: /Remove item/ }).last().focus();
    await page.keyboard.press('Enter');
    await expect(list.getByRole('spinbutton')).toHaveCount((values.access_point_delays_s_veh as number[]).length);
    for (const key of ['demand_balanced', 'demand_adjustments_resolved', 'capacity_effects_resolved', 'spillback_present']) {
      const group = field(page, key);
      const invalidChoice = key === 'spillback_present' ? 'Yes' : 'No';
      await group.getByRole('radio', { name: invalidChoice, exact: true }).check();
      await invalid(page, key);
      await group.getByRole('radio', { name: invalidChoice === 'Yes' ? 'No' : 'Yes', exact: true }).check();
    }
    await calculate(page);
  });

  test('calibration reveals errors in closed disclosure, retains source and adjustment, then recovers', async ({ page }) => {
    await open(page);
    const group = page.locator(`#workflow-section-${id}-calibration`);
    const trigger = group.getByRole('button', { name: 'Calibration', exact: true });
    await expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await trigger.click();
    await expect(field(page, 'calibration_source_note')).toHaveCount(0);
    await group.getByRole('radio', { name: 'User local calibration', exact: true }).check();
    await trigger.click();
    await invalid(page, 'calibration_source_note');
    await expect(trigger).toHaveAttribute('aria-expanded', 'true');
    await field(page, 'calibration_source_note').fill('Qualified local speed study');
    await field(page, 's_calib').fill('2.5');
    await group.getByRole('radio', { name: 'HCM reference — not locally calibrated', exact: true }).check();
    await expect(field(page, 'calibration_source_note')).toHaveCount(0);
    await expect(field(page, 's_calib')).toHaveValue('2.5');
    await invalid(page, 's_calib');
    await group.getByRole('radio', { name: 'User local calibration', exact: true }).check();
    await expect(field(page, 'calibration_source_note')).toHaveValue('Qualified local speed study');
    await calculate(page);
    await group.getByRole('radio', { name: 'HCM reference — not locally calibrated', exact: true }).check();
    await field(page, 's_calib').fill('0');
    await calculate(page);
  });

  test('blank custom starts fail-closed and can be completed entirely with production controls', async ({ page }) => {
    await open(page);
    const blankStarting = page.waitForResponse((response) => response.url().includes(`/${id}/starting-values`) && response.url().includes('template_id=blank_custom'));
    await field(page, 'template').selectOption('blank_custom');
    const blankValues = (await (await blankStarting).json()).displayed_inputs as Record<string, unknown>;
    expect(blankValues.control_type).toBe('signalized');
    expect(blankValues.external_control_type).toBe('signalized');
    for (const key of ['demand_balanced', 'demand_adjustments_resolved', 'capacity_effects_resolved', 'spillback_present']) expect(blankValues[key]).toBeNull();
    await expect(field(page, 'segment_length')).toHaveValue('');
    await expect(page.locator(`#${id}-control_type`)).toContainText('Signalized');
    await expect(page.locator(`#${id}-external_control_type`)).toContainText('Signalized');
    await expect(page.getByRole('button', { name: 'Use required value: Signalized', exact: true })).toHaveCount(0);
    for (const key of ['demand_balanced', 'demand_adjustments_resolved', 'capacity_effects_resolved', 'spillback_present']) await expect(field(page, key).getByRole('radio', { checked: true })).toHaveCount(0);
    for (const group of ['provenance', 'calibration']) await page.locator(`#workflow-section-${id}-${group} .disclosure-trigger`).click();
    for (const metadata of fields) {
      const value = values[metadata.key];
      if (metadata.key === 'control_type' || metadata.key === 'external_control_type') continue;
      if (value === null || value === undefined) continue;
      if (metadata.kind === 'boolean' || metadata.kind === 'choice') {
        await field(page, metadata.key).locator(`input[value="${String(value)}"]`).check();
      } else if (metadata.kind === 'number_list') {
        for (const item of value as number[]) {
          await field(page, metadata.key).getByRole('button', { name: /Add item/ }).click();
          await field(page, metadata.key).getByRole('spinbutton').last().fill(String(item));
        }
      } else await field(page, metadata.key).fill(String(value));
    }
    await calculate(page);
    await expect(page.locator('[data-slot="result-hero"]')).toContainText('C');
  });

  test('attributes mismatched downstream inputs and reveals closed provenance for recovery', async ({ page }) => {
    await open(page);
    for (const [key, bad] of [['external_direction', 'westbound'], ['external_through_movement_id', 'WB_TH'], ['external_analysis_period_min', '60'], ['analysis_period_min', '60']]) {
      await field(page, key).fill(bad);
      if (key === 'external_direction') {
        await field(page, key).press('Tab');
        await expect(field(page, key)).toHaveAttribute('aria-invalid', 'true');
        await expect(page.getByRole('alert')).toContainText('Qualified downstream direction must match the subject direction.');
      } else {
        await invalid(page, key);
      }
      await field(page, key).fill(String(values[key]));
    }
    const provenance = page.locator(`#workflow-section-${id}-provenance`);
    await provenance.getByRole('button', { name: 'External source / provenance', exact: true }).click();
    await field(page, 'external_source_tool').fill('');
    await provenance.getByRole('button', { name: 'External source / provenance', exact: true }).click();
    await invalid(page, 'external_source_tool');
    await field(page, 'external_source_tool').fill(String(values.external_source_tool));
    await calculate(page);
  });

  test('saves, restores exact Project inputs without rerun, edits a scenario and compares', async ({ page }) => {
    await open(page);
    await calculate(page);
    const downloaded = page.waitForEvent('download');
    const saved = page.waitForResponse((response) => response.url().endsWith('/projects/from-analysis'));
    await page.getByRole('button', { name: 'Save to Project', exact: true }).click();
    await downloaded;
    const project = (await (await saved).json()).project;
    expect(project.schema_version).toBe('2.0');
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    await page.locator('.scenario-actions-menu > summary').click();
    await page.getByRole('button', { name: 'Duplicate scenario', exact: true }).click();
    await page.locator('.scenario-row').filter({ hasText: 'Alternative' }).click();
    await page.getByRole('button', { name: 'Calculate scenario', exact: true }).click();
    let calculations = 0;
    page.on('request', (request) => { if (request.url().endsWith(`/${id}/calculate`)) calculations++; });
    const restoredValidation = page.waitForRequest((request) => request.url().endsWith(`/${id}/validate`));
    await page.getByRole('button', { name: 'Edit scenario', exact: true }).click();
    expect((await restoredValidation).postDataJSON().displayed_inputs).toEqual(values);
    await expect(field(page, 'segment_length')).toHaveValue(String(values.segment_length));
    await expect(field(page, 'control_type')).toContainText('Signalized');
    await expect(field(page, 'external_control_type')).toContainText('Signalized');
    for (const metadata of fields) {
      if (metadata.key === 'calibration_source_note') continue;
      if (metadata.key === 'control_type' || metadata.key === 'external_control_type') continue;
      const value = values[metadata.key];
      if (metadata.kind === 'boolean' || metadata.kind === 'choice') await expect(field(page, metadata.key).locator(`input[value="${String(value)}"]`)).toBeChecked();
      else if (metadata.kind === 'number_list') expect(await field(page, metadata.key).getByRole('spinbutton').evaluateAll((items) => items.map((item) => (item as HTMLInputElement).valueAsNumber))).toEqual(value);
      else await expect(field(page, metadata.key)).toHaveValue(typeof value === 'number' ? String(Number(value.toFixed(3))) : String(value ?? ''));
    }
    expect(calculations).toBe(0);
    await page.getByRole('button', { name: 'Thai', exact: true }).click();
    await expect(page).toHaveURL(/\/project\/analysis\/.*\/scenarios\//);
    await expect(field(page, 'segment_length')).toHaveValue(String(values.segment_length));
    await page.getByRole('button', { name: 'อังกฤษ' }).click();
    await calculate(page);
    await field(page, 'd_other_s_veh').fill('1.25');
    await expect(page.locator('[data-slot="stale-result-panel"]')).toBeVisible();
    await calculate(page);
    await page.getByRole('button', { name: 'Save scenario result', exact: true }).click();
    await expect(page.getByTestId('project-workspace')).toBeVisible();
    const selects = page.locator('.project-controls select');
    await selects.nth(0).selectOption({ label: 'Base' });
    await selects.nth(1).selectOption({ label: 'Alternative' });
    await page.getByRole('button', { name: 'Compare', exact: true }).click();
    await expect(page.getByTestId('comparison-result')).toContainText('Travel speed');
  });

  for (const width of [1920, 1366, 1024, 390]) for (const locale of ['en', 'th']) {
    test(`${locale} responsive worksheet, list, results and Handbook at ${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: width === 390 ? 844 : 900 });
      await open(page);
      if (locale === 'th') await page.getByRole('button', { name: 'Thai', exact: true }).click();
      await page.getByRole('button', { name: locale === 'th' ? 'คำนวณ' : 'Calculate', exact: true }).click();
      await expect(page.getByTestId('workflow-results')).toBeVisible();
      const list = field(page, 'access_point_delays_s_veh');
      await list.getByRole('button', { name: locale === 'th' ? /เพิ่มรายการ/ : /Add item/ }).click();
      await list.getByRole('spinbutton').last().fill('1.25');
      await list.getByRole('button', { name: locale === 'th' ? /ลบรายการ/ : /Remove item/ }).last().click();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
      const controls = await page.locator('.workflow-input-workspace input, .workflow-input-workspace button').evaluateAll((items) => items.filter((item) => (item as HTMLElement).offsetParent !== null && !item.closest('.section-checklist') && item.getBoundingClientRect().width > 1).map((item) => { const rect = item.getBoundingClientRect(); return { left: rect.left, right: rect.right }; }));
      expect(controls.filter((rect) => rect.left < -1 || rect.right > width + 1)).toEqual([]);
      await page.screenshot({ path: path.resolve('..', '.tmp', 'evidence', `lht-${locale}-${width}.png`), fullPage: true });
      await page.goto(`/reference/${id}`);
      await expect(page.getByTestId(`reference-${id}`)).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width + 1);
      await expect(page.locator('main')).not.toContainText(`guide.${id}`);
    });
  }
});
