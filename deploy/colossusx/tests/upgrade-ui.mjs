// ColossusX upgrade acceptance checks, 2026-09-21. GPL-3.0-only.
// Usage: node upgrade-ui.mjs BASE_URL OUTPUT_DIRECTORY
// Install Playwright, or set PLAYWRIGHT_MODULE to its absolute index.mjs path.
// Synthetic responses are intercepted only in an isolated browser context and
// are explicitly identified in the report; they never create on-chain data.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const [ baseArgument, outputArgument ] = process.argv.slice(2);
if (!baseArgument || !outputArgument) throw new Error('Usage: upgrade-ui.mjs BASE_URL OUTPUT_DIRECTORY');
const output = resolve(outputArgument);
const base = baseArgument.replace(/\/$/, '');
const url = (path) => new URL(path, `${base}/`).href;
const apiHot = '/api/v2/stats/hot-smart-contracts';
const donation = '0x7d7cC2AbEB8256d11E9Ec63C13782E77300c7e30';
const report = { base, startedAt: new Date().toISOString(), profiles: [], checks: [], errors: [], passed: false };
const candidates = new Set((process.env.UPGRADE_UI_CONTRACTS || '').split(',').filter(Boolean));
const sha256 = (bytes) => createHash('sha256').update(bytes).digest('hex');
const logoRoot = new URL('../frontend/assets/', import.meta.url);
const mascotHashes = new Set(await Promise.all(['logo-64.png', 'logo-128.png'].map(async (name) => sha256(await readFile(new URL(name, logoRoot))))));
const numeric = (value) => Number(value?.match(/[\d,]+/)?.[0]?.replaceAll(',', ''));
const sleep = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
async function eventually(check, message, timeout = 30000) {
  const deadline = Date.now() + timeout;
  let last;
  do {
    try { const value = await check(); if (value) return value; } catch (error) { last = error; }
    await sleep(200);
  } while (Date.now() < deadline);
  throw new Error(`${message}${last ? `: ${last.message}` : ''}`);
}
function trackErrors(page, label) {
  page.on('pageerror', (error) => report.errors.push({ page: label, message: error.message }));
}
async function json(context, path) {
  const response = await context.request.get(url(path), { timeout: 60000 });
  assert.equal(response.status(), 200, path);
  return response.json();
}
async function navigate(page, path) {
  const response = await page.goto(url(path), { waitUntil: 'domcontentloaded', timeout: 90000 });
  assert.equal(response.status(), 200, path);
}
async function newContext(browser, { mobile = false, theme = 'light', timezone = 'UTC' } = {}) {
  const context = await browser.newContext({
    viewport: mobile ? { width: 390, height: 844 } : { width: 1440, height: 1100 },
    colorScheme: theme, timezoneId: timezone, isMobile: mobile, hasTouch: mobile,
  });
  // v2.7 uses next-themes: the key is "theme", not Chakra v2's old key.
  await context.addInitScript((value) => localStorage.setItem('theme', value), theme);
  return context;
}
async function checkFooter(page) {
  const footer = page.locator('footer');
  await footer.waitFor();
  await eventually(async () => /Backend:.*v?10\.2\.6(?:-colossusx)?/.test(await footer.innerText()), 'Updated backend version is absent from footer');
  const text = await footer.innerText();
  assert.match(text, /Made with/);
  assert.match(text, /Copyright © Blockscout Limited 2023-/);
  assert.match(text, /Frontend: v2\.7\.2-colossusx/);
  const links = [
    ['Blockscout', 'https://blockscout.com'],
    ['Licenses & Notices', '/legal/'],
    ['Source code', '/source/'],
    ['GitHub', 'https://github.com/CypherTroopers'],
  ];
  for (const [name, href] of links) {
    assert.equal(await footer.getByRole('link', { name, exact: true }).getAttribute('href'), href);
  }
  assert.match(await footer.getByRole('link', { name: /^Donate/ }).getAttribute('href'), new RegExp(`/address/${donation}$`));
  assert.equal(await page.getByText('Sponsored', { exact: true }).count(), 0);
  assert.equal(await page.getByText('Advertisement', { exact: true }).count(), 0);
  const width = await page.evaluate(() => ({ document: document.documentElement.scrollWidth, viewport: innerWidth }));
  assert.ok(width.document <= width.viewport + 1, `Horizontal overflow ${JSON.stringify(width)}`);
  return text;
}
async function readHome(page) {
  return page.evaluate(() => {
    const headings = [...document.querySelectorAll('h2')];
    const stat = (pattern) => headings.find((element) => pattern.test(element.textContent))?.closest('a')?.innerText;
    const dailyTitle = [...document.querySelectorAll('p')].find((element) => element.textContent === "Today's transactions (UTC)");
    return {
      blocks: stat(/^Total blocks$/), transactions: stat(/^Total (txns|transactions)$/),
      daily: dailyTitle?.parentElement?.nextElementSibling?.innerText,
      theme: document.documentElement.className,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      logos: [...document.querySelectorAll('a[aria-label="ColossusX home"] img')]
        .filter((element) => element.getBoundingClientRect().width > 0)
        .map((element) => ({ src: element.currentSrc, loaded: element.complete && element.naturalWidth > 0, filter: getComputedStyle(element).filter })),
    };
  });
}
async function homepage(browser, mobile, theme) {
  const name = `${mobile ? 'mobile' : 'desktop'}-${theme}`;
  const timezone = mobile ? 'Asia/Tokyo' : 'UTC';
  const context = await newContext(browser, { mobile, theme, timezone });
  const page = await context.newPage();
  trackErrors(page, name);
  const calls = { stats: [], daily: [], main: [] };
  let latestStats, latestDaily, dailyRequest;
  page.on('response', async (response) => {
    const endpoint = new URL(response.url());
    if (response.status() !== 200) return;
    try {
      if (endpoint.pathname === '/api/v2/stats') { latestStats = await response.json(); calls.stats.push(Date.now()); }
      if (endpoint.pathname === '/stats-service/api/v1/lines/newTxns') {
        latestDaily = await response.json(); dailyRequest = Object.fromEntries(endpoint.searchParams); calls.daily.push(Date.now());
      }
      if (endpoint.pathname === '/stats-service/api/v1/pages/main') calls.main.push(Date.now());
    } catch { /* Aborted navigation responses are not verification data. */ }
  });
  await navigate(page, '/');
  await page.getByText("Today's transactions (UTC)", { exact: true }).first().waitFor({ timeout: 60000 });
  await eventually(() => latestStats && latestDaily, 'Homepage did not load live stats and UTC chart');
  if (!mobile && theme === 'light') {
    await eventually(() => Object.values(calls).every((timestamps) => timestamps.some((time) => time - timestamps[0] >= 25000)),
      'Homepage stats did not refresh automatically', 50000);
  }
  const state = await eventually(async () => {
    const current = await readHome(page);
    const point = latestDaily.chart.find((item) => item.date === dailyRequest.to);
    const dailyMatches = point?.value !== undefined && point?.value !== null && point.value !== '' ?
      numeric(current.daily) === Number(point.value) : /N\/A|—/.test(current.daily || '');
    return numeric(current.blocks) === Number(latestStats.total_blocks) && numeric(current.transactions) === Number(latestStats.total_transactions) && dailyMatches && current;
  }, 'Homepage totals / daily value differ from the responses consumed by the browser');
  const today = new Date().toISOString().slice(0, 10);
  const from = new Date(Date.parse(`${today}T00:00:00Z`) - 29 * 86400000).toISOString().slice(0, 10);
  assert.deepEqual(dailyRequest, { resolution: 'DAY', from, to: today });
  assert.ok(state.theme.split(/\s+/).includes(theme), `next-themes did not select ${theme}`);
  assert.equal(state.timezone, timezone);
  assert.ok(state.logos.length && state.logos.every((logo) => logo.loaded && logo.filter === 'none'), 'Mascot missing or visually inverted');
  for (const logo of state.logos) {
    const response = await context.request.get(logo.src);
    assert.equal(response.status(), 200);
    assert.ok(mascotHashes.has(sha256(await response.body())), 'Displayed mascot differs from approved assets');
  }
  const faviconLinks = await page.locator('head link[rel*="icon"]').evaluateAll((links) => links.map((link) => link.href));
  assert.equal(faviconLinks.length, 6, 'Expected desktop and mobile favicon sizes');
  const favicons = [];
  for (const href of [...faviconLinks, url('/favicon.ico')]) {
    const filename = new URL(href).pathname.split('/').at(-1);
    const expected = sha256(await readFile(new URL(`favicons/${filename}`, logoRoot)));
    const response = await context.request.get(href);
    assert.equal(response.status(), 200, href);
    assert.equal(sha256(await response.body()), expected, `Favicon differs from approved mascot: ${href}`);
    assert.match(response.headers()['cache-control'], /must-revalidate/);
    favicons.push({ href, sha256: expected });
  }
  const footer = await checkFooter(page);
  await page.screenshot({ path: `${output}/${name}.png`, fullPage: true });
  await page.locator('footer').screenshot({ path: `${output}/${name}-footer.png` });
  report.profiles.push({ name, dataSource: 'real-api', state, footer, favicons, calls, dailyRequest, todayPresent: latestDaily.chart.some((point) => point.date === today) });
  await page.locator('footer').getByRole('link', { name: 'Licenses & Notices', exact: true }).click();
  await page.waitForURL('**/legal/');
  assert.match(await page.locator('main').innerText(), /without warranty/);
  await page.getByRole('navigation').getByRole('link', { name: 'Source code', exact: true }).click();
  await page.waitForURL('**/source/');
  assert.ok((await page.getByRole('link', { name: 'Download the complete modified frontend source (.tar.gz)', exact: true }).getAttribute('href')).endsWith('.tar.gz'));
  await context.close();
}
async function hotContracts(browser) {
  const context = await newContext(browser);
  const page = await context.newPage();
  trackErrors(page, 'hot-contracts-real');
  await navigate(page, '/hot-contracts');
  await page.getByRole('heading', { name: 'Hot contracts', exact: true }).waitFor();
  const checks = [];
  let rankedScale, rankedAddress;
  for (const scale of ['5m', '1h', '3h', '1d', '7d', '30d']) {
    // Fresh navigation also verifies shareable filter URLs, independently of cache.
    const responsePromise = page.waitForResponse((response) => {
      const endpoint = new URL(response.url());
      return endpoint.pathname === apiHot && endpoint.searchParams.get('scale') === scale && response.status() === 200;
    }, { timeout: 60000 });
    await navigate(page, `/hot-contracts?scale=${scale}`);
    const body = await (await responsePromise).json();
    assert.ok(Array.isArray(body.items));
    if (body.items.length) {
      rankedScale ||= scale;
      rankedAddress ||= body.items[0].contract_address.hash;
      for (const item of body.items) candidates.add(item.contract_address.hash);
      await page.locator(`table a[href*="${body.items[0].contract_address.hash}"]`).first().waitFor();
      assert.ok(await page.getByRole('columnheader', { name: 'Txn count' }).isVisible());
      assert.ok(await page.getByRole('columnheader', { name: 'Gas used' }).isVisible());
    } else {
      await page.getByText('No results', { exact: true }).waitFor();
    }
    for (const value of ['5m', '1h', '3h', '1d', '7d', '30d']) assert.ok(await page.locator(`[data-id="${value}"]`).first().isVisible());
    checks.push({ scale, count: body.items.length, state: body.items.length ? 'ranked-list' : 'empty' });
  }
  // Verify an actual UI click changes the API query, including when no contracts exist.
  const clicked = page.waitForResponse((response) => new URL(response.url()).pathname === apiHot && new URL(response.url()).searchParams.get('scale') === '1h');
  await page.locator('[data-id="1h"]').first().click();
  assert.equal((await clicked).status(), 200);
  const sortChecks = [];
  if (rankedScale) {
    await navigate(page, `/hot-contracts?scale=${rankedScale}`);
    await page.locator(`table a[href*="${rankedAddress}"]`).first().waitFor();
    for (const [label, field] of [['Txn count', 'transactions_count'], ['Gas used', 'total_gas_used']]) {
      const sorted = page.waitForResponse((response) => {
        const endpoint = new URL(response.url());
        return endpoint.pathname === apiHot && endpoint.searchParams.get('sort') === field && endpoint.searchParams.get('order') === 'desc';
      });
      await page.getByRole('columnheader', { name: label }).click();
      const response = await sorted;
      assert.equal(response.status(), 200);
      const data = await response.json();
      const values = data.items.map((item) => BigInt(item[field] || '0'));
      assert.ok(values.every((value, index) => index === 0 || values[index - 1] >= value), `${field} is not ranked descending`);
      sortChecks.push({ field, order: 'desc', rows: values.length });
    }
  }
  await checkFooter(page);
  await page.screenshot({ path: `${output}/hot-contracts-real.png`, fullPage: true });
  report.checks.push({ feature: 'hot-contracts', dataSource: 'real-api', intervals: checks, filterClick: true, sorting: sortChecks, rankingStatus: rankedScale ? 'verified' : 'skipped-empty-chain-data' });
  await context.close();
}
async function searchAndLogs(browser) {
  const context = await newContext(browser);
  const contracts = await json(context, '/api/v2/smart-contracts');
  for (const item of contracts.items || []) if (item.address?.hash) candidates.add(item.address.hash);
  const page = await context.newPage();
  trackErrors(page, 'contract-search-and-logs');
  let searchChecked = false, logsChecked = false;
  for (const address of [...candidates].slice(0, 20)) {
    if (!/^0x[0-9a-f]{40}$/i.test(address)) continue;
    if (!searchChecked) {
      const search = await json(context, `/api/v2/search?q=${encodeURIComponent(address)}`);
      const found = search.items?.find((item) => item.address_hash?.toLowerCase() === address.toLowerCase() && (item.is_smart_contract_address || item.type === 'contract'));
      if (found) {
        await navigate(page, `/search-results?q=${encodeURIComponent(address)}&redirect=false`);
        const row = page.locator('tr').filter({ has: page.locator(`a[href*="${address}"]`) }).first();
        await row.waitFor();
        await eventually(async () => row.locator('use[href*="#contracts/"]').count(), 'Search result lacks contract marker');
        report.checks.push({ feature: 'contract-search-marker', dataSource: 'real-api', address, apiType: found.type, contractFlag: found.is_smart_contract_address });
        await page.screenshot({ path: `${output}/search-contract-real.png`, fullPage: true });
        searchChecked = true;
      }
    }
    if (!logsChecked) {
      const logs = await json(context, `/api/v2/addresses/${address}/logs`);
      const log = logs.items?.find((item) => item.transaction_hash && item.block_timestamp);
      if (log) {
        await navigate(page, `/address/${address}?tab=logs`);
        await page.getByText('Timestamp', { exact: true }).first().waitFor();
        // Select Unix in the first log's timestamp control to compare the exact API value.
        const timestamp = page.getByText('Timestamp', { exact: true }).first();
        const grid = timestamp.locator('xpath=ancestor::*[following-sibling::*[1]//button[@aria-label="Toggle time format"]][1]');
        const timestampContainer = grid.locator('xpath=following-sibling::*[1]');
        await timestampContainer.getByRole('button', { name: 'Toggle time format' }).click();
        await page.getByRole('option', { name: 'Unix', exact: true }).click();
        assert.ok((await timestampContainer.innerText()).includes(String(Math.floor(Date.parse(log.block_timestamp) / 1000))));
        report.checks.push({ feature: 'event-log-timestamp', dataSource: 'real-api', address, timestamp: log.block_timestamp });
        await page.screenshot({ path: `${output}/event-log-real.png`, fullPage: true });
        logsChecked = true;
      }
    }
    if (searchChecked && logsChecked) break;
  }
  for (const [feature, checked] of [['contract-search-marker', searchChecked], ['event-log-timestamp', logsChecked]]) {
    if (!checked) report.checks.push({ feature, dataSource: 'real-api', status: 'skipped-no-matching-chain-data', inspectedContracts: Math.min(candidates.size, 20) });
  }
  await context.close();
}
async function fixtures(browser) {
  // These fixture checks prove rendering and field handling, not real chain activity.
  const context = await newContext(browser);
  const page = await context.newPage();
  trackErrors(page, 'synthetic-fixtures');
  await context.route(`**${apiHot}*`, (route) => route.fulfill({ json: { items: [], next_page_params: null } }));
  await navigate(page, '/hot-contracts');
  await page.getByText('No results', { exact: true }).waitFor();
  report.checks.push({ feature: 'hot-contracts-empty-state', dataSource: 'synthetic-response', status: 'passed' });
  const address = '0x1111111111111111111111111111111111111111';
  await context.route('**/api/v2/search?*', (route) => route.fulfill({ json: {
    items: [{ type: 'address', name: 'ColossusX UI test fixture', address_hash: address, is_smart_contract_address: true,
      is_smart_contract_verified: false, ens_info: null }], next_page_params: null,
  } }));
  await navigate(page, `/search-results?q=${address}&redirect=false`);
  const row = page.locator('tr').filter({ has: page.locator(`a[href*="${address}"]`) }).first();
  await row.waitFor();
  await eventually(async () => row.locator('use[href*="#contracts/regular"]').count(), 'New contract flag is not reflected for an address-type result');
  report.checks.push({ feature: 'contract-search-new-boolean-field', dataSource: 'synthetic-response', status: 'passed' });
  await context.close();
}
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ headless: true, args: ['--no-sandbox', '--disable-dev-shm-usage'] });
try {
  for (const mobile of [false, true]) for (const theme of ['light', 'dark']) await homepage(browser, mobile, theme);
  const context = await newContext(browser);
  for (const path of ['/legal/GPL-3.0.txt', '/legal/CC0-1.0.txt', '/legal/Inter-OFL.txt', '/source/frontend.sha256', '/api/v2/stats', '/network-info/']) {
    const response = await context.request.get(url(path));
    assert.equal(response.status(), 200, path);
    report.checks.push({ path, status: response.status(), dataSource: 'real-server' });
  }
  const checksumResponse = await context.request.get(url('/source/frontend.sha256'));
  const [ expectedHash, archive ] = (await checksumResponse.text()).trim().split(/\s+/);
  assert.match(archive, /^colossusx-frontend-2\.7\.2-[a-f0-9]+\.tar\.gz$/);
  const source = await context.request.get(url(`/source/${archive}`), { timeout: 180000 });
  assert.equal(source.status(), 200);
  assert.equal(sha256(await source.body()), expectedHash);
  report.checks.push({ feature: 'corresponding-source-checksum', archive, sha256: expectedHash, dataSource: 'real-server' });
  report.checks.push({ feature: 'indexing-status', data: await json(context, '/api/v2/main-page/indexing-status'), dataSource: 'real-api' });
  await context.close();
  await hotContracts(browser);
  await searchAndLogs(browser);
  if (process.env.UPGRADE_UI_FIXTURES !== '0') await fixtures(browser);
  assert.deepEqual(report.errors, [], 'Browser JavaScript errors');
  report.passed = true;
} catch (error) {
  report.failure = { message: error.message, stack: error.stack };
  const page = browser.contexts().flatMap((context) => context.pages()).at(-1);
  if (page) await page.screenshot({ path: `${output}/failure.png`, fullPage: true }).catch(() => {});
  throw error;
} finally {
  report.completedAt = new Date().toISOString();
  await writeFile(`${output}/report.json`, JSON.stringify(report, null, 2));
  await browser.close();
}
console.log(JSON.stringify({ profiles: report.profiles.length, checks: report.checks.length, output: `${output}/report.json`, passed: report.passed }));
