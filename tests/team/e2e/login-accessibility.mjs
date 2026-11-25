import assert from 'node:assert/strict';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';

const output = process.env.SQE_EVIDENCE_DIR || '.';
const browser = await chromium.launch({
  executablePath: process.env.SQE_CHROMIUM || undefined
});
try {
  const context = await browser.newContext();
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:5173/web/login');
  await page.getByRole('textbox', { name: 'login-username' }).waitFor();

  const results = await new AxeBuilder({ page }).analyze();
  await writeFile(join(output, 'axe-login.json'), JSON.stringify(results, null, 2));
  await page.screenshot({ path: join(output, 'login.png') });

  const focus = [];
  for (let count = 0; count < 20; count++) {
    await page.keyboard.press('Tab');
    focus.push(await page.locator(':focus').evaluate(element => ({
      tag: element.tagName,
      name: element.getAttribute('aria-label') || element.textContent.trim(),
      visibleFocus: element.matches(':focus-visible')
    })).catch(() => ({ tag: 'none', name: '', visibleFocus: false })));
    if (focus.at(-1).name === 'Log In') break;
  }
  await writeFile(join(output, 'keyboard-login.json'), JSON.stringify(focus, null, 2));
  for (const name of ['login-username', 'login-password', 'Log In']) {
    assert(focus.some(entry => entry.name === name && entry.visibleFocus), name);
  }
  console.log('Keyboard reached both login fields and submit with :focus-visible.');
  console.log('axe violations:', results.violations.map(entry => entry.id));
} finally {
  await browser.close();
}
