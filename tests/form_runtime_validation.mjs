import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

const cases = [
  {path: 'index.html', button: 'cba-submit', success: 'cba-success', error: 'cba-error', values: {company: 'Example Co', email: 'buyer@example.com', context: 'A draft supply agreement.'}, product: 'Contract Breakpoint'},
  {path: 'execution-breakpoint-protection/index.html', button: 'ebp-submit', success: 'ebp-success', error: 'ebp-error', values: {'ebp-name': 'Buyer', 'ebp-email': 'buyer@example.com', 'ebp-company': 'Example Co', 'ebp-exposure': 'Notice', 'ebp-deadline': '', 'ebp-context': 'Notice is due shortly.'}, product: 'EBP'},
  {path: 'earnings-breakpoint-analysis/index.html', button: 'eba-submit', success: 'eba-success', error: 'eba-error', values: {'eba-organisation': 'Example Fund', 'eba-email': 'credit@example.com', 'eba-role': 'Credit director', 'eba-use-case': 'Pre-deal', 'eba-assessment': 'Single name', 'eba-context': 'Reviewing charter-backed cash flow.'}, product: 'EBA'},
];

function scriptFrom(path) {
  const html = fs.readFileSync(new URL(`../${path}`, import.meta.url), 'utf8');
  return [...html.matchAll(/<script(?: [^>]*)?>([\s\S]*?)<\/script>/g)].at(-1)[1];
}

async function exercise(testCase, accepted) {
  let listener;
  let payload;
  const elements = {};
  for (const [id, value] of Object.entries(testCase.values)) elements[id] = {value, style: {display: ''}};
  for (const id of [testCase.button, testCase.success, testCase.error]) elements[id] = {textContent: '', disabled: false, style: {display: ''}};
  elements[testCase.button].addEventListener = (_event, callback) => { listener = callback; };
  const context = {
    window: {location: {hash: ''}},
    document: {getElementById: id => elements[id]},
    alert: message => { throw new Error(`unexpected alert: ${message}`); },
    console: {warn() {}},
    fetch: async (_url, options) => {
      payload = JSON.parse(options.body);
      return {ok: true, json: async () => ({success: accepted})};
    },
  };
  vm.runInNewContext(scriptFrom(testCase.path), context);
  await listener.call(elements[testCase.button]);
  assert.equal(payload.product, testCase.product);
  assert.equal(payload.email, testCase.values.email ?? testCase.values['ebp-email'] ?? testCase.values['eba-email']);
  assert.equal(elements[testCase.success].style.display, accepted ? 'block' : 'none');
  assert.equal(elements[testCase.error].style.display, accepted ? 'none' : 'block');
  assert.equal(elements[testCase.button].disabled, accepted);
}

for (const testCase of cases) {
  await exercise(testCase, true);
  await exercise(testCase, false);
}

console.log('form runtime validation passed');
