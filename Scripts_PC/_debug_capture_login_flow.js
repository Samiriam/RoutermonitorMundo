const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  page.on('request', (request) => {
    if (!request.url().includes('/fh_api')) {
      return;
    }
    console.log('REQUEST', JSON.stringify({
      method: request.method(),
      url: request.url(),
      headers: request.headers(),
      postData: request.postData(),
    }));
  });

  page.on('response', async (response) => {
    if (!response.url().includes('/fh_api')) {
      return;
    }
    let body = '';
    try {
      body = await response.text();
    } catch (error) {
      body = `<unavailable: ${error.message}>`;
    }
    console.log('RESPONSE', JSON.stringify({
      url: response.url(),
      status: response.status(),
      headers: response.headers(),
      body: body.slice(0, 1000),
    }));
  });

  await page.goto('http://192.168.1.1/login.html', { waitUntil: 'networkidle', timeout: 30000 });
  await page.fill('#user_name', 'user');
  await page.fill('#loginpp', 'user1234');
  await page.click('#login_btn');
  await page.waitForTimeout(5000);

  await browser.close();
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
