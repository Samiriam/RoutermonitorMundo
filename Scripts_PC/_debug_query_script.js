// Prueba: extrae el _newFirmwareQueryScript EXACTO de la APK (main.dart) y lo
// ejecuta contra el router para ver si el script funciona o es problema del WebView.
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

// Extrae el contenido del raw string de _newFirmwareQueryScript desde main.dart
function extractQueryScript() {
  const dart = fs.readFileSync('E:/RouterMonitor/Flutter_App/router_monitor_app/lib/main.dart', 'utf8');
  const start = dart.indexOf('String _newFirmwareQueryScript() => r');
  const rStart = dart.indexOf("'''", start);
  const rEnd = dart.indexOf("'''", rStart + 3);
  if (start < 0 || rStart < 0 || rEnd < 0) throw new Error('No se encontro _newFirmwareQueryScript');
  return dart.substring(rStart + 3, rEnd);
}

(async () => {
  const routerIp = process.argv[2] || '192.168.1.1';
  const username = process.argv[3] || 'user';
  const password = process.argv[4] || 'user1234';
  const baseUrl = `http://${routerIp}`;

  const executablePath = findBrowserExecutable();
  if (!executablePath) throw new Error('No se encontro navegador Chromium.');

  const queryScript = extractQueryScript();
  console.log('[DEBUG] QueryScript extraido, longitud:', queryScript.length, 'chars');
  console.log('[DEBUG] Inicia:', JSON.stringify(queryScript.slice(0, 80)));

  const browser = await chromium.launch({ executablePath, headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(`${baseUrl}/login.html`, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.fill('#user_name', username);
    await page.fill('#loginpp', password);
    await page.click('#login_btn');
    await page.waitForURL(/main\.html/, { timeout: 30000 });
    console.log('[OK] Login -> main.html');
    await page.waitForTimeout(2000);

    const result = await page.evaluate(queryScript);
    console.log('\n[RESULTADO]', JSON.stringify(result, null, 2).slice(0, 4000));
  } catch (e) {
    console.log('\n[FAIL]', e.message);
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.log('[FATAL]', e.message);
  process.exit(1);
});
