import { defineConfig, devices } from '@playwright/test';
import { existsSync } from 'node:fs';
import path from 'node:path';

const releasePort = 8765;
const repositoryRoot = path.resolve('..');
const localPython = path.join(repositoryRoot, '.agent-work', 'ci-venv', 'Scripts', 'python.exe');
const pythonCommand = process.platform === 'win32' && existsSync(localPython) ? localPython : 'python';

export default defineConfig({
  testDir: './playwright',
  timeout: 30_000,
  fullyParallel: true,
  reporter: process.env.CI ? [['dot'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: process.env.BASE_URL ?? `http://127.0.0.1:${releasePort}`,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  webServer: process.env.BASE_URL ? undefined : {
    command: `${pythonCommand} -m hcmcalc.api.main --host 127.0.0.1 --port ${releasePort} --static-dir frontend/dist`,
    cwd: repositoryRoot,
    env: { PYTHONPATH: path.join(repositoryRoot, 'src') },
    url: `http://127.0.0.1:${releasePort}/api/v1/health`,
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
