import {defineConfig,devices} from '@playwright/test';
export default defineConfig({
  testDir:'./tests/e2e',
  fullyParallel:true,
  forbidOnly:!!process.env.CI,
  retries:process.env.CI?1:0,
  workers:process.env.CI?2:undefined,
  reporter:process.env.CI?'github':'list',
  use:{baseURL:'http://127.0.0.1:5173',trace:'retain-on-failure'},
  projects:[{name:'chromium',use:{...devices['Desktop Chrome']}}],
  webServer:[
    {command:'php -S 127.0.0.1:8000 -t server/public server/public/router.php',url:'http://127.0.0.1:8000/api/v1/status',reuseExistingServer:!process.env.CI,timeout:45000},
    {command:'npm run dev -- --host 127.0.0.1',url:'http://127.0.0.1:5173',reuseExistingServer:!process.env.CI,timeout:60000}
  ]
});
