// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * @see https://playwright.dev/docs/test-configuration
 */
module.exports = defineConfig({
  testDir: './e2e/tests',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 1,

  /* Opt out of parallel tests on CI for stability */
  workers: process.env.CI ? 2 : 4,

  /* Reporter to use */
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['list'],
  ],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL to use in actions like `await page.goto('/')` */
    baseURL: process.env.TEST_BASE_URL || 'http://localhost:3333',

    /* Collect trace when retrying the failed test */
    trace: 'on-first-retry',

    /* Screenshot on failure */
    screenshot: 'only-on-failure',

    /* Video recording */
    video: 'on-first-retry',

    /* Default viewport for H5 */
    viewport: { width: 375, height: 812 },

    /* Device scale factor for mobile simulation */
    deviceScaleFactor: 2,

    /* User agent for mobile */
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15',

    /* Bypass CSP to allow localStorage access */
    bypassCSP: true,

    /* Browser permissions */
    permissions: ['storage-access'],

    /* Launch options */
    launchOptions: {
      args: ['--disable-web-security', '--disable-features=IsolateOrigins,site-per-process'],
    },
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium-mobile',
      use: {
        ...devices['iPhone 13'],
        /* Use Chromium for H5 testing */
        browserName: 'chromium',
      },
    },

    /* Desktop viewport for admin/testing */
    {
      name: 'chromium-desktop',
      use: {
        browserName: 'chromium',
        viewport: { width: 1280, height: 720 },
      },
    },
  ],

  /* Run local dev server before starting the tests */
  webServer: process.env.SKIP_WEB_SERVER ? undefined : {
    command: 'npm run dev:h5',
    url: 'http://localhost:3333',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },

  /* Global timeout */
  globalTimeout: 30 * 60 * 1000, // 30 minutes

  /* Test timeout */
  timeout: 60 * 1000, // 60 seconds per test
});
