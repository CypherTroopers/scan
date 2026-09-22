// ColossusX transaction-fee regression check, 2026-09-21. GPL-3.0-only.
// Checks live data separately from an isolated zero-activity browser fixture.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [ baseArgument, outputArgument ] = process.argv.slice(2);
if (!baseArgument || !outputArgument) throw new Error('Usage: transaction-fees-ui.mjs BASE_URL OUTPUT_DIRECTORY');
const base = baseArgument.replace(/\/$/, '');
const output = resolve(outputArgument);
const endpoint = '/stats-service/api/v1/pages/transactions';
const report = { startedAt: new Date().toISOString(), profiles: [], errors: [], passed: false };
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });

try {
  let liveData;
  for (const mobile of [ false, true ]) {
    const name = mobile ? 'mobile' : 'desktop';
    const context = await browser.newContext({
      locale: 'en-US', viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 },
      isMobile: mobile, hasTouch: mobile,
    });
    const page = await context.newPage();
    page.on('pageerror', (error) => report.errors.push({ name, message: error.message }));
    const responsePromise = page.waitForResponse((response) => new URL(response.url()).pathname === endpoint && response.status() === 200);
    const navigation = await page.goto(`${base}/txs`, { waitUntil: 'domcontentloaded' });
    assert.equal(navigation.status(), 200);
    liveData = await (await responsePromise).json();
    for (const field of [ 'transactions_fee_24h', 'average_transactions_fee_24h', 'transactions_24h' ]) {
      assert.ok(liveData[field]?.value !== undefined && liveData[field]?.value !== null && liveData[field]?.value !== '', `${field} is missing`);
      assert.ok(Number.isFinite(Number(liveData[field].value)) && Number(liveData[field].value) >= 0, `${field} is not a valid nonnegative number`);
    }
    assert.equal(liveData.transactions_fee_24h.units, 'CLX');
    const fee = page.getByRole('link').filter({ has: page.getByRole('heading', { name: 'Transactions fees', exact: true }) });
    await fee.waitFor();
    const expected = Number(liveData.transactions_fee_24h.value).toLocaleString('en-US', { maximumFractionDigits: 2 });
    await page.waitForFunction(({ expected }) => {
      const label = [...document.querySelectorAll('h2')].find((element) => element.textContent === 'Transactions fees');
      return label?.closest('a')?.innerText.replace(/\s+/g, '').includes(`${expected}CLX`);
    }, { expected });
    const text = await fee.innerText();
    assert.doesNotMatch(text, /NaN|Infinity/);
    assert.match(text, /\(24h\)/);
    report.profiles.push({ name, dataSource: 'live-api', value: liveData.transactions_fee_24h.value, widget: text });
    await page.screenshot({ path: `${output}/${name}.png`, animations: 'disabled' });
    await context.close();
  }

  const context = await browser.newContext({ locale: 'en-US' });
  const zero = structuredClone(liveData);
  for (const field of [ 'transactions_fee_24h', 'average_transactions_fee_24h', 'transactions_24h' ]) zero[field].value = '0';
  await context.route(`**${endpoint}*`, (route) => route.fulfill({ json: zero }));
  const page = await context.newPage();
  await page.goto(`${base}/txs`, { waitUntil: 'domcontentloaded' });
  const fee = page.getByRole('link').filter({ has: page.getByRole('heading', { name: 'Transactions fees', exact: true }) });
  await fee.waitFor();
  await page.waitForFunction(() => {
    const label = [...document.querySelectorAll('h2')].find((element) => element.textContent === 'Transactions fees');
    return /\n0\s*CLX/.test(label?.closest('a')?.innerText || '');
  });
  assert.match(await fee.innerText(), /0\s*CLX/);
  assert.doesNotMatch(await fee.innerText(), /NaN|Infinity/);
  report.profiles.push({ name: 'zero-activity', dataSource: 'synthetic-browser-response', widget: await fee.innerText() });
  await context.close();
  assert.deepEqual(report.errors, []);
  report.passed = true;
} catch (error) {
  report.failure = error.message;
  throw error;
} finally {
  report.completedAt = new Date().toISOString();
  await writeFile(`${output}/report.json`, JSON.stringify(report, null, 2) + '\n');
  await browser.close();
}
console.log(JSON.stringify(report));
