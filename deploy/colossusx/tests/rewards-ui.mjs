// ColossusX FHS-D reward acceptance check, 2026-09-21. GPL-3.0-only.
import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [ baseArgument, outputArgument ] = process.argv.slice(2);
if (!baseArgument || !outputArgument) throw new Error('Usage: rewards-ui.mjs BASE_URL OUTPUT_DIRECTORY');
const base = baseArgument.replace(/\/$/, '');
const output = resolve(outputArgument);
const report = { startedAt: new Date().toISOString(), blocks: [], profiles: [], errors: [], passed: false };
await mkdir(output, { recursive: true });
const args = [ '--no-sandbox', '--disable-dev-shm-usage' ];
if (process.env.BROWSER_HOST_RESOLVER_RULES) args.push(`--host-resolver-rules=${process.env.BROWSER_HOST_RESOLVER_RULES}`);
const browser = await chromium.launch({ headless: true, args, executablePath: process.env.BROWSER_EXECUTABLE || undefined });
const expected = new Map([
  [ 1, [ '100000000000000000000000', '0', '0' ] ],
  [ 57, [ '100000000000000000000000', '100000000000000000000000', '0' ] ],
  [ 58, [ '0', '0', '0' ] ],
  [ 64, [ '100000000000000000000000', '0', '4200000000000' ] ],
  [ 2120, [ '100000000000000000000000', '0', '2923200000000000' ] ],
]);
let completeFixture;

try {
  for (const mobile of [ false, true ]) {
    const name = mobile ? 'mobile' : 'desktop';
    const context = await browser.newContext({ locale: 'en-US', viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1000 }, isMobile: mobile, hasTouch: mobile });
    const page = await context.newPage();
    page.on('pageerror', error => report.errors.push({ name, message: error.message }));
    for (const [ height, amounts ] of expected) {
      const endpoint = `/api/v2/blocks/${height}`;
      const responsePromise = page.waitForResponse(response => new URL(response.url()).pathname === endpoint && response.status() === 200);
      const navigation = await page.goto(`${base}/block/${height}`, { waitUntil: 'domcontentloaded' });
      assert.equal(navigation.status(), 200);
      const data = await (await responsePromise).json();
      const rewards = data.colossusx_rewards;
      assert.equal(rewards.status, 'complete', `block ${height} rewards not complete`);
      assert.equal(rewards.rule_version, 'FHS-D/64c12623');
      assert.deepEqual([ rewards.block_reward, rewards.common_miner_reward, rewards.common_rpc_reward ], amounts);
      assert.equal(rewards.total, amounts.reduce((sum, amount) => sum + BigInt(amount), 0n).toString());
      assert.equal(rewards.payouts.reduce((sum, payout) => sum + BigInt(payout.reward), 0n).toString(), rewards.total);
      await page.getByText('Reward distribution', { exact: true }).waitFor();
      for (const label of [ 'Block production', 'Common miner PoW', 'Common RPC' ]) await page.getByText(label, { exact: true }).first().waitFor();
      for (const payout of rewards.payouts) assert.ok(await page.locator(`a[href="/address/${payout.address_hash}"]`).count() > 0, `missing recipient link ${payout.address_hash}`);
      assert.doesNotMatch(await page.locator('body').innerText(), /NaN|Infinity/);
      report.blocks.push({ profile: name, height, rewards });
      if (height === 64) completeFixture = data;
      if ([ 57, 58, 64 ].includes(height)) await page.screenshot({ path: `${output}/${name}-${height}.png`, fullPage: true, animations: 'disabled' });
    }
    for (const path of [ '/', '/blocks' ]) {
      const navigation = await page.goto(`${base}${path}`, { waitUntil: 'domcontentloaded' });
      assert.equal(navigation.status(), 200);
      await page.locator('a[href^="/block/"]:visible').first().waitFor();
      assert.doesNotMatch(await page.locator('body').innerText(), /NaN|Infinity/);
    }
    report.profiles.push(name);
    await context.close();
  }

  // Intercept only this browser's API response; no database or chain writes.
  const context = await browser.newContext({ locale: 'en-US' });
  let requests = 0;
  const pending = structuredClone(completeFixture);
  pending.rewards = [];
  pending.colossusx_rewards = { status: 'pending', rule_version: 'FHS-D/64c12623', total: null, block_reward: null, common_miner_reward: null, common_rpc_reward: null, payouts: [] };
  await context.route('**/api/v2/blocks/64', route => route.fulfill({ json: ++requests === 1 ? pending : completeFixture }));
  const page = await context.newPage();
  page.on('pageerror', error => report.errors.push({ name: 'pending-fixture', message: error.message }));
  await page.goto(`${base}/block/64`, { waitUntil: 'domcontentloaded' });
  await page.getByText('Pending reward indexing', { exact: true }).waitFor();
  await page.getByText('Common RPC', { exact: true }).waitFor({ timeout: 45000 });
  assert.ok(requests >= 2, 'pending rewards must refresh without reloading the page');
  report.pendingRefresh = { requests, passed: true };
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
console.log(JSON.stringify({ passed: report.passed, blocks: report.blocks.length, profiles: report.profiles, pendingRefresh: report.pendingRefresh }));
