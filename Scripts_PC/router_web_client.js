const { chromium } = require('playwright');

function extractMetric(text, label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = text.match(new RegExp(`${escaped}\\s+([^\\n]+)`));
  return match ? match[1].trim() : '';
}

function normalizeNumberString(value) {
  return (value || '').replace(/,/g, '').trim();
}

async function main() {
  const routerIp = process.argv[2] || '192.168.1.1';
  const username = process.argv[3] || 'user';
  const password = process.argv[4] || 'user1234';
  const baseUrl = `http://${routerIp}`;

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(`${baseUrl}/login.html`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.fill('#user_name', username);
    await page.fill('#loginpp', password);
    await page.click('#login_btn');
    await page.waitForURL(/main\.html/, { timeout: 30000 });
    await page.waitForTimeout(1500);

    const result = await page.evaluate(async () => {
      const deviceInfo = await $post('get_device_info', null, 'nocheck');
      const values = await $post('get_value_by_xmlnode', {
        uptime: 'DeviceInfo.UpTime',
        cpu_usage: 'DeviceInfo.ProcessStatus.CPUUsage',
        mem_total: 'DeviceInfo.MemoryStatus.Total',
        mem_free: 'DeviceInfo.MemoryStatus.Free',
        model: 'DeviceInfo.ModelName',
        firmware: 'DeviceInfo.SoftwareVersion',
        pon_state: 'X_FH_PON_MANAGE.reginfo.pon_link_state',
        reg_state: 'X_FH_PON_MANAGE.reginfo.loid_reg_state'
      });

      const wanType = deviceInfo.pon_mode === 5 ? 'XGSPON' : `PON mode ${deviceInfo.pon_mode}`;

      return {
        authenticated: true,
        ModelName: values.model || deviceInfo.devicetype || 'N/A',
        SoftwareVersion: values.firmware || 'N/A',
        WANAccessType: wanType,
        uptime: values.uptime || '0',
        cpu_usage: values.cpu_usage || '0',
        mem_total: values.mem_total || '0',
        mem_free: values.mem_free || '0',
        pon_reg_state: values.pon_state || '',
        loid_reg_state: values.reg_state || '',
        ponBytesSent: '0',
        ponBytesReceived: '0',
        NOTA: 'Firmware RP3084+ autenticado via navegador. Los contadores GPON y datos opticos siguen sin nodo confirmado en esta version.',
        raw_device_info: deviceInfo,
        raw_value_nodes: values
      };
    });

    await page.evaluate(() => {
      location.hash = '#/status/opticalInfo/opticalInfo';
    });
    await page.waitForTimeout(2500);
    const opticalText = await page.evaluate(() => document.body.innerText);

    await page.evaluate(() => {
      location.hash = '#/status/wifiStatus/wifiStatus_5g';
    });
    await page.waitForTimeout(2500);
    const wifi5Text = await page.evaluate(() => document.body.innerText);

    result.txpower = extractMetric(opticalText, 'Transmitted Power').replace(' dBm', '').trim();
    result.rxpower = extractMetric(opticalText, 'Received Power').replace(' dBm', '').trim();
    result.transceivertemperature = extractMetric(opticalText, 'Operating Temperature').replace(' ℃', '').trim();
    result.supplyvottage = extractMetric(opticalText, 'Supply Voltage').replace(' V', '').trim();
    result.biascurrent = extractMetric(opticalText, 'Bias Current').replace(' mA', '').trim();

    result.wifi5_ssid_1 = extractMetric(wifi5Text, 'SSID1 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
    result.wifi5_ssid_2 = extractMetric(wifi5Text, 'SSID2 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
    result.wifi5_packets_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Packets Count'));
    result.wifi5_bytes_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Bytes Count'));
    result.wifi5_packets_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Packets Count'));
    result.wifi5_bytes_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Bytes Count'));
    result.wifi5_channel = extractMetric(wifi5Text, 'Frequency (Channel)').trim();

    result.NOTA = 'Firmware RP3084+ autenticado via navegador. Se recuperan datos reales de sistema, optica y contadores WiFi 5 GHz; los contadores GPON totales siguen sin nodo confirmado en esta version.';

    console.log(JSON.stringify({ success: true, data: result }));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.log(JSON.stringify({ success: false, error: error.message }));
  process.exit(1);
});
