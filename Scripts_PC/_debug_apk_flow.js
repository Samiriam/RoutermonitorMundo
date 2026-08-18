// Diagnostico: replica el flujo de la APK (login WebView RP3084+) contra el router
// y captura si $post existe y que error devuelve get_device_info.
const { chromium } = require('playwright');
const fs = require('fs');

function findBrowserExecutable() {
  const candidates = [
    process.env.ROUTER_MONITOR_BROWSER,
    'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
    'C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe',
    `${process.env.LOCALAPPDATA}\\BraveSoftware\\Brave-Browser\\Application\\brave.exe`,
    'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
    'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    `${process.env.LOCALAPPDATA}\\Microsoft\\Edge\\Application\\msedge.exe`,
  ].filter(Boolean);
  return candidates.find((candidate) => fs.existsSync(candidate));
}

(async () => {
  const routerIp = process.argv[2] || '192.168.1.1';
  const username = process.argv[3] || 'user';
  const password = process.argv[4] || 'user1234';
  const baseUrl = `http://${routerIp}`;

  const executablePath = findBrowserExecutable();
  if (!executablePath) throw new Error('No se encontro navegador Chromium.');

  const browser = await chromium.launch({ executablePath, headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
  });
  const page = await context.newPage();

  page.on('response', (resp) => {
    if (resp.url().includes('/fh_api')) {
      console.log(`[HTTP ${resp.status()}] ${resp.url().slice(0, 120)}`);
    }
  });

  try {
    // 1) Login igual que la APK (y el helper de escritorio)
    await page.goto(`${baseUrl}/login.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.fill('#user_name', username);
    await page.fill('#loginpp', password);
    await page.click('#login_btn');
    await page.waitForURL(/main\.html/, { timeout: 30000 });
    console.log('\n[OK] Login exitoso -> main.html');

    // 2) Espera 2s (igual que la APK 1.3.1+6)
    await page.waitForTimeout(2000);

    // 3) Verifica $post
    const diag = await page.evaluate(() => {
      const out = {
        href: location.href,
        title: document.title,
        typeof_window_post: typeof window.$post,
        typeof_global_post: typeof $post,
        typeof_dollar_global: typeof $,
        post_keys: (typeof window.$post === 'function') ? Object.getOwnPropertyNames(window.$post).slice(0, 20) : null,
      };
      return out;
    });
    console.log('\n[DIAG] Funciones globales:', JSON.stringify(diag, null, 2));

    // 4) Intenta la consulta igual que la APK y captura el error real
    const query = await page.evaluate(async () => {
      try {
        if (typeof $post !== 'function') {
          return { success: false, step: 'no-post', error: `$post = ${typeof $post}` };
        }
        const deviceInfo = await $post('get_device_info', null, 'nocheck');
        return { success: true, step: 'get_device_info', deviceInfo };
      } catch (e) {
        return {
          success: false,
          step: 'get_device_info',
          error: e && (e.message || e.name || String(e)),
          stack: e && e.stack ? e.stack.slice(0, 500) : '',
          type: typeof e,
        };
      }
    });
    console.log('\n[QUERY] get_device_info:', JSON.stringify(query, null, 2).slice(0, 3000));
  } catch (e) {
    console.log('\n[FAIL]', e.message);
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.log('[FATAL]', e.message);
  process.exit(1);
});
