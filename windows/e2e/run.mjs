import crypto from 'node:crypto';
import fs from 'node:fs/promises';
import http from 'node:http';
import net from 'node:net';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { chromium } from 'playwright';

const execFileAsync = promisify(execFile);
const PIPE_NAME = '\\\\.\\pipe\\GamblockAIProtection';
const CHECK_NAME = 'windows_extension_model_e2e';
const PIPE_TIMEOUT_MS = 5_000;
const DEFAULT_TIMEOUT_MS = 20_000;

class HarnessFailure extends Error {
  constructor(code) {
    super(code);
    this.code = code;
  }
}

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 1) {
    const value = argv[index];
    if (!value.startsWith('--')) {
      throw new HarnessFailure('invalid_argument');
    }
    const key = value.slice(2);
    const next = argv[index + 1];
    if (!next || next.startsWith('--')) {
      result[key] = true;
    } else {
      result[key] = next;
      index += 1;
    }
  }
  return result;
}

function resolvePath(value, fallback) {
  return path.resolve(value ?? fallback);
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, 'utf8'));
}

async function sha256File(filePath) {
  const digest = crypto.createHash('sha256');
  digest.update(await fs.readFile(filePath));
  return digest.digest('hex');
}

function assert(condition, code) {
  if (!condition) {
    throw new HarnessFailure(code);
  }
}

async function verifyArtifacts(appRoot, modelRoot) {
  const artifactRoot = path.join(appRoot, 'assets', 'protection');
  const manifest = await readJson(path.join(artifactRoot, 'manifest.json'));
  assert(manifest.contract_version === 'hybrid-v2', 'artifact_contract_mismatch');

  const modelPath = path.join(artifactRoot, manifest.model.path);
  const rulesPath = path.join(artifactRoot, manifest.ruleset.path);
  const fixturesPath = path.join(artifactRoot, manifest.fixtures.path);
  const [model, rules] = await Promise.all([
    readJson(modelPath),
    readJson(rulesPath),
  ]);
  const [modelSha, rulesSha, fixturesSha] = await Promise.all([
    sha256File(modelPath),
    sha256File(rulesPath),
    sha256File(fixturesPath),
  ]);

  assert(modelSha === manifest.model.sha256, 'model_asset_hash_mismatch');
  assert(rulesSha === manifest.ruleset.sha256, 'rules_asset_hash_mismatch');
  assert(fixturesSha === manifest.fixtures.sha256, 'fixture_asset_hash_mismatch');
  assert(model.version === manifest.model.version, 'model_version_mismatch');
  assert(rules.version === manifest.ruleset.version, 'ruleset_version_mismatch');
  assert(model.contract_version === manifest.contract_version, 'model_contract_mismatch');
  assert(rules.contract_version === manifest.contract_version, 'ruleset_contract_mismatch');

  const sourceOnnxPath = path.join(modelRoot, 'models', 'gamblock_logistic_regression.onnx');
  const sourceMetadataPath = path.join(modelRoot, 'models', 'gamblock_hybrid_metadata.json');
  const sourceRulesPath = path.join(modelRoot, 'models', 'gambling_keywords.json');
  const [sourceOnnxSha, sourceMetadataSha, sourceRulesSha] = await Promise.all([
    sha256File(sourceOnnxPath),
    sha256File(sourceMetadataPath),
    sha256File(sourceRulesPath),
  ]);
  assert(sourceOnnxSha === model.source_onnx_sha256, 'onnx_source_hash_mismatch');
  assert(sourceMetadataSha === model.source_metadata_sha256, 'metadata_source_hash_mismatch');
  assert(sourceRulesSha === rules.source_sha256, 'rules_source_hash_mismatch');

  return {
    model_version: model.version,
    ruleset_version: rules.version,
    model_sha256: modelSha,
    rules_sha256: rulesSha,
    fixtures_sha256: fixturesSha,
    source_onnx_sha256: sourceOnnxSha,
  };
}

function pipeRequest(payload) {
  const request = {
    ...payload,
    request_id: payload.request_id ?? `windows-e2e-${Date.now()}-${Math.random()}`,
  };
  return new Promise((resolve, reject) => {
    const socket = net.createConnection(PIPE_NAME);
    let buffer = '';
    let settled = false;
    const finish = (error, value) => {
      if (settled) return;
      settled = true;
      socket.destroy();
      if (error) reject(error);
      else resolve(value);
    };
    socket.setTimeout(PIPE_TIMEOUT_MS, () => finish(new HarnessFailure('pipe_timeout')));
    socket.on('error', () => finish(new HarnessFailure('pipe_unavailable')));
    socket.on('connect', () => {
      socket.write(`${JSON.stringify(request)}\n`);
    });
    socket.on('data', (chunk) => {
      buffer += chunk.toString('utf8');
      const newline = buffer.indexOf('\n');
      if (newline < 0) return;
      const line = buffer.slice(0, newline);
      try {
        finish(null, JSON.parse(line));
      } catch {
        finish(new HarnessFailure('pipe_invalid_response'));
      }
    });
  });
}

async function requestWithRetry(payload, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (Date.now() < deadline) {
    try {
      return await pipeRequest(payload);
    } catch (error) {
      lastError = error;
      await sleep(250);
    }
  }
  throw lastError ?? new HarnessFailure('pipe_timeout');
}

async function waitFor(description, callback, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const value = await callback();
      if (value) return value;
    } catch {
      // The service can be between lifecycle states while reconnecting.
    }
    await sleep(250);
  }
  throw new HarnessFailure(description);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function fixturePage(fixture) {
  const headings = fixture.headings.map((heading) => `<h1>${escapeHtml(heading)}</h1>`).join('');
  const anchors = fixture.anchorTexts
    .map((anchor) => `<a href="/fixture-link">${escapeHtml(anchor)}</a>`)
    .join(' ');
  return `<!doctype html><html><head><title>${escapeHtml(fixture.title)}</title></head><body>${headings}<nav>${anchors}</nav></body></html>`;
}

async function startFixtureServer(fixtures) {
  const byName = new Map(fixtures.map((fixture) => [fixture.name, fixture]));
  const pages = new Map([
    ['/safe', byName.get('benign university')],
    ['/slot-gacor', byName.get('explicit gambling url')],
    ['/model-only', byName.get('dom-only gambling')],
  ]);
  for (const [name, fixture] of pages) {
    assert(fixture, `fixture_missing_${name.slice(1)}`);
  }

  const server = http.createServer((request, response) => {
    const pathname = new URL(request.url ?? '/', 'http://127.0.0.1').pathname;
    const fixture = pages.get(pathname);
    if (!fixture) {
      response.writeHead(404, { 'content-type': 'text/plain' });
      response.end('not found');
      return;
    }
    response.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
    response.end(fixturePage(fixture));
  });
  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(0, '127.0.0.1', resolve);
  });
  const address = server.address();
  assert(address && typeof address === 'object', 'fixture_server_unavailable');
  return {
    server,
    baseUrl: `http://127.0.0.1:${address.port}`,
  };
}

async function extensionId(context) {
  let workers = context.serviceWorkers();
  if (workers.length === 0) {
    await context.waitForEvent('serviceworker', { timeout: DEFAULT_TIMEOUT_MS });
    workers = context.serviceWorkers();
  }
  const workerUrl = workers[0]?.url() ?? '';
  const match = workerUrl.match(/^chrome-extension:\/\/([^/]+)/);
  assert(match, 'extension_service_worker_unavailable');
  return match[1];
}

async function launchExtension(extensionRoot, browserExecutable, profilePrefix) {
  const profileDirectory = await fs.mkdtemp(path.join(os.tmpdir(), profilePrefix));
  const options = {
    headless: false,
    args: [
      `--disable-extensions-except=${extensionRoot}`,
      `--load-extension=${extensionRoot}`,
      '--no-first-run',
      '--no-default-browser-check',
    ],
  };
  if (browserExecutable) options.executablePath = browserExecutable;
  else options.channel = 'chrome';
  const context = await chromium.launchPersistentContext(profileDirectory, options);
  return { context, profileDirectory };
}

async function pairExtension(context, token) {
  const id = await extensionId(context);
  const page = await context.newPage();
  await page.goto(`chrome-extension://${id}/options.html`, { waitUntil: 'domcontentloaded' });
  await page.locator('#token').fill(token);
  await page.locator('#save').click();
  await page.close();
}

async function closeContext(resource) {
  if (!resource) return;
  await resource.context.close().catch(() => {});
  await fs.rm(resource.profileDirectory, { recursive: true, force: true }).catch(() => {});
}

async function serviceSnapshot() {
  return requestWithRetry({ type: 'snapshot' });
}

async function waitForSensor(expected) {
  return waitFor(`sensor_${expected}`, async () => {
    const snapshot = await serviceSnapshot();
    return snapshot.sensor_status === expected ? snapshot : false;
  });
}

async function restartService(serviceName) {
  await execFileAsync('sc.exe', ['stop', serviceName], { windowsHide: true }).catch(() => {});
  await waitFor('service_stop_timeout', async () => {
    const { stdout } = await execFileAsync('sc.exe', ['query', serviceName], { windowsHide: true });
    return /STATE\s+:\s+1\s+STOPPED/.test(stdout);
  });
  await execFileAsync('sc.exe', ['start', serviceName], { windowsHide: true });
  await waitFor('service_start_timeout', async () => {
    const { stdout } = await execFileAsync('sc.exe', ['query', serviceName], { windowsHide: true });
    return /STATE\s+:\s+4\s+RUNNING/.test(stdout);
  });
}

async function waitForPath(page, expectedPath, timeoutMs = DEFAULT_TIMEOUT_MS) {
  return waitFor(`path_${expectedPath.slice(1)}`, () => {
    try {
      return new URL(page.url()).pathname === expectedPath;
    } catch {
      return false;
    }
  }, timeoutMs);
}

async function expectBlocked(page, baseUrl, route) {
  await page.goto(`${baseUrl}/safe`, { waitUntil: 'load' });
  await sleep(350);
  const startedAt = Date.now();
  await page.goto(`${baseUrl}${route}`, { waitUntil: 'load' });
  await waitForPath(page, '/safe', 15_000);
  return Date.now() - startedAt;
}

async function expectAllowed(page, baseUrl, route) {
  await page.goto(`${baseUrl}${route}`, { waitUntil: 'load' });
  await sleep(2_000);
  assert(new URL(page.url()).pathname === route, `unexpected_block_${route.slice(1)}`);
  return true;
}

async function runScenario(scenarios, name, action) {
  try {
    const details = await action();
    scenarios.push({ name, status: 'passed', details });
  } catch (error) {
    scenarios.push({ name, status: 'failed' });
    throw error;
  }
}

async function run(options) {
  const workspaceRoot = resolvePath(options['workspace-root'], path.resolve('../..'));
  const appRoot = resolvePath(options['app-root'], path.join(workspaceRoot, 'gamblock_ai_apps'));
  const modelRoot = resolvePath(options['model-root'], path.join(workspaceRoot, 'gamblock-ai-model'));
  const extensionRoot = resolvePath(options['extension-root'], path.join(workspaceRoot, 'browser_extension'));
  const serviceName = options['service-name'] || 'GamblockAIProtection';
  const browserExecutable = options['browser-executable'];
  const artifacts = await verifyArtifacts(appRoot, modelRoot);
  const fixtures = await readJson(path.join(appRoot, 'assets', 'protection', 'hybrid-v2-fixtures.json'));
  const selfTest = await requestWithRetry({ type: 'self_test' });
  assert(selfTest.passed === true, 'windows_self_test_failed');
  assert(selfTest.model_version === artifacts.model_version, 'service_model_version_mismatch');
  assert(selfTest.ruleset_version === artifacts.ruleset_version, 'service_ruleset_version_mismatch');

  const fixtureServer = await startFixtureServer(fixtures);
  const scenarios = [];
  const latency = [];
  let validResource;
  try {
    await runScenario(scenarios, 'artifact_contract', () => ({
      model_version: artifacts.model_version,
      ruleset_version: artifacts.ruleset_version,
    }));

    const pairingToken = (await requestWithRetry({ type: 'get_pairing_token' })).pairing_token;
    assert(typeof pairingToken === 'string' && pairingToken.length === 64, 'pairing_token_unavailable');

    await runScenario(scenarios, 'invalid_pairing_rejected', async () => {
      const invalidResource = await launchExtension(extensionRoot, browserExecutable, 'gamblock-invalid-');
      try {
        await pairExtension(invalidResource.context, `${pairingToken.slice(0, -2)}00`);
        const snapshot = await waitForSensor('disconnected');
        assert(snapshot.status === 'degraded', 'invalid_pairing_not_degraded');
        return true;
      } finally {
        await closeContext(invalidResource);
      }
    });

    validResource = await launchExtension(extensionRoot, browserExecutable, 'gamblock-valid-');
    await pairExtension(validResource.context, pairingToken);
    const page = validResource.context.pages()[0] ?? await validResource.context.newPage();

    await runScenario(scenarios, 'valid_pairing_relay', async () => {
      const snapshot = await waitForSensor('connected');
      assert(snapshot.status === 'active', 'service_not_active');
      await expectAllowed(page, fixtureServer.baseUrl, '/safe');
      return true;
    });

    await runScenario(scenarios, 'benign_page_allow', async () => {
      await expectAllowed(page, fixtureServer.baseUrl, '/safe');
      return true;
    });

    await runScenario(scenarios, 'explicit_url_block', async () => {
      const duration = await expectBlocked(page, fixtureServer.baseUrl, '/slot-gacor');
      latency.push(duration);
      return true;
    });

    await runScenario(scenarios, 'dom_model_only_block', async () => {
      const duration = await expectBlocked(page, fixtureServer.baseUrl, '/model-only');
      latency.push(duration);
      return true;
    });

    await runScenario(scenarios, 'service_restart_reconnect', async () => {
      await restartService(serviceName);
      const snapshot = await waitForSensor('connected', 20_000);
      assert(snapshot.status === 'active', 'service_not_active_after_restart');
      await expectAllowed(page, fixtureServer.baseUrl, '/safe');
      return true;
    });
  } finally {
    await closeContext(validResource);
    await new Promise((resolve) => fixtureServer.server.close(resolve));
  }

  const passed = scenarios.filter((scenario) => scenario.status === 'passed').length;
  return {
    check: CHECK_NAME,
    status: 'passed',
    browser_family: 'chrome',
    build_mode: 'release',
    scenario_total: scenarios.length,
    scenario_passed: passed,
    scenarios: scenarios.map(({ name, status }) => ({ name, status })),
    model_version: artifacts.model_version,
    ruleset_version: artifacts.ruleset_version,
    model_sha256: artifacts.model_sha256,
    rules_sha256: artifacts.rules_sha256,
    fixtures_sha256: artifacts.fixtures_sha256,
    source_onnx_sha256: artifacts.source_onnx_sha256,
    intervention_samples: latency.length,
    intervention_min_ms: latency.length ? Math.min(...latency) : null,
    intervention_max_ms: latency.length ? Math.max(...latency) : null,
    raw_url_or_dom_emitted: false,
  };
}

async function main() {
  if (process.platform !== 'win32') {
    console.log(JSON.stringify({ check: CHECK_NAME, status: 'pending', reason_code: 'windows_required' }));
    return 0;
  }
  try {
    const result = await run(parseArgs(process.argv.slice(2)));
    console.log(JSON.stringify(result));
    return 0;
  } catch (error) {
    const reason = error instanceof HarnessFailure ? error.code : 'runtime_failure';
    console.log(JSON.stringify({ check: CHECK_NAME, status: 'failed', reason_code: reason }));
    return 1;
  }
}

process.exitCode = await main();
