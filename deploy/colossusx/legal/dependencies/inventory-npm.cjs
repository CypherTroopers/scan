/* Read-only installed npm package metadata inventory. It does not determine legal compatibility. */
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const roots = (process.env.INVENTORY_ROOTS || '/app/node_modules').split(':');
const entries = [];
const visited = new Set();
function scanPackage(dir) {
  let real;
  try { real = fs.realpathSync(dir); } catch { return; }
  if (visited.has(real)) return;
  visited.add(real);
  const file = path.join(dir, 'package.json');
  let pkg;
  try { pkg = JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return; }
  const legalFiles = [];
  for (const name of fs.readdirSync(dir).sort()) {
    if (!/^(licen[sc]e|copying|copyright|notice|third.party)([.\-_ ]|$)/i.test(name)) continue;
    const loc = path.join(dir, name);
    if (!fs.statSync(loc).isFile()) continue;
    const data = fs.readFileSync(loc);
    legalFiles.push({ file: name, sha256: crypto.createHash('sha256').update(data).digest('hex'), text: data.toString('utf8') });
  }
  entries.push({ name: pkg.name || null, version: pkg.version || null, path: dir,
    declaredLicense: pkg.license || pkg.licenses || null,
    repository: pkg.repository || null, homepage: pkg.homepage || null,
    private: pkg.private || false, legalFiles });
  scanModules(path.join(dir, 'node_modules'));
}
function scanModules(dir) {
  if (!fs.existsSync(dir)) return;
  for (const name of fs.readdirSync(dir).sort()) {
    if (name.startsWith('.')) continue;
    const loc = path.join(dir, name);
    if (!fs.statSync(loc).isDirectory()) continue;
    if (name.startsWith('@')) {
      for (const child of fs.readdirSync(loc).sort()) scanPackage(path.join(loc, child));
    } else scanPackage(loc);
  }
}
for (const root of roots) scanModules(root);
entries.sort((a,b) => a.path.localeCompare(b.path));
process.stdout.write(JSON.stringify({ schema: 'colossusx-installed-npm-license-inventory-v1', roots,
  scope: 'Installed npm manifests and top-level license/notice files, including nested node_modules; not every bundled code or native/OS dependency.',
  packages: entries }, null, 2) + '\n');
