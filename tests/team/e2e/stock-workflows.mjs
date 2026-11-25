import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const frontend = 'http://localhost:5173';
const backend = process.env.SQE_BACKEND || 'http://localhost:18763';
const output = process.env.SQE_EVIDENCE_DIR || '.';
const stockMenu = 'action-menu-stock-operations';
const browser = await chromium.launch({
  executablePath: process.env.SQE_CHROMIUM || undefined
});

async function login(user, password) {
  assert(password, 'Provide the disposable fixture password.');
  const context = await browser.newContext();
  await context.addInitScript(host => {
    window.INVENTREE_SETTINGS = {
      server_list: { 'sqe-local': { host, name: 'SQE' } },
      default_server: 'sqe-local'
    };
  }, backend);
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  await page.goto(frontend + '/web/login');
  await page.getByRole('textbox', { name: 'login-username' }).fill(user);
  await page.getByRole('textbox', { name: 'login-password' }).fill(password);
  await page.getByRole('button', { name: 'Log In', exact: true }).click();
  await page.waitForURL(/\/web\/(home|dashboard)/);
  return page;
}

function quantity(page, amount) {
  return page.getByRole('row', { name: 'Quantity ' + amount, exact: true });
}

async function workflow(page, { id, action, endpoint, amount, expected }) {
  assert(Number.isInteger(Number(id)) && Number(id) > 0, 'Provide a stock fixture ID.');
  await page.goto(frontend + '/web/stock/item/' + id + '/');
  await quantity(page, 10).waitFor();
  await page.getByRole('button', { name: stockMenu }).click();
  await page.getByRole('menuitem', { name: stockMenu + '-' + endpoint + '-stock' }).click();
  const dialog = page.getByRole('dialog', { name: action + ' Stock' });
  await dialog.waitFor();
  await dialog.getByLabel('number-field-quantity').fill(String(amount));
  const [response] = await Promise.all([
    page.waitForResponse(response =>
      response.request().method() === 'POST' &&
      new URL(response.url()).pathname === '/api/stock/' + endpoint + '/'
    ),
    dialog.getByRole('button', { name: 'Submit', exact: true }).click()
  ]);
  assert.equal(response.status(), 201);
  await page.reload();
  await quantity(page, expected).waitFor();
  console.log(action + ' Stock passed. 10 → ' + expected + ' after reload.');
  await page.screenshot({ path: join(output, endpoint + '-stock.png') });
}

let failed = false;
try {
  const admin = await login('admin', process.env.SQE_ADMIN_PASSWORD);
  for (const scenario of [
    { id: process.env.SQE_RECEIVE_ID, action: 'Add', endpoint: 'add', amount: 5, expected: 15 },
    { id: process.env.SQE_DISPATCH_ID, action: 'Remove', endpoint: 'remove', amount: 3, expected: 7 }
  ]) {
    try {
      await workflow(admin, scenario);
    } catch (error) {
      failed = true;
      console.error(scenario.action + ' Stock failed.', error.message);
    }
  }

  await admin.goto(frontend + '/web/stock/item/' + process.env.SQE_RECEIVE_ID + '/');
  await admin.getByRole('tab', { name: 'Stock Details' }).waitFor();
  const results = await new AxeBuilder({ page: admin }).analyze();
  await writeFile(join(output, 'axe-stock.json'), JSON.stringify(results, null, 2));
  console.log('Stock detail axe violations:', results.violations.map(entry => entry.id));

  const reader = await login('sqe-reader', process.env.SQE_READER_PASSWORD);
  await reader.goto(frontend + '/web/stock/item/' + process.env.SQE_RECEIVE_ID + '/');
  await reader.getByRole('tab', { name: 'Stock Details' }).waitFor();
  const menu = reader.getByRole('button', { name: stockMenu });
  if (await menu.isVisible() && await menu.isEnabled()) await menu.click();
  for (const endpoint of ['add', 'remove']) {
    const operation = reader.getByRole('menuitem', { name: stockMenu + '-' + endpoint + '-stock' });
    assert(!(await operation.isVisible()) || !(await operation.isEnabled()));
  }
  console.log('View-only account could view the item and had no enabled stock adjustments.');
} finally {
  await browser.close();
}
if (failed) process.exitCode = 1;
