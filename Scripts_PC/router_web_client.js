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
    `${process.env.LOCALAPPDATA}\\Vivaldi\\Application\\vivaldi.exe`,
    `${process.env.LOCALAPPDATA}\\Programs\\Opera\\opera.exe`,
  ].filter(Boolean);

  return candidates.find((candidate) => fs.existsSync(candidate));
}

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

  const executablePath = findBrowserExecutable();
  if (!executablePath) {
    throw new Error('No se encontro navegador Chromium existente. Define ROUTER_MONITOR_BROWSER con la ruta del navegador.');
  }

  const browser = await chromium.launch({ executablePath, headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(`${baseUrl}/login.html`, { waitUntil: 'networkidle', timeout: 30000 });
    await page.fill('#user_name', username);
    await page.fill('#loginpp', password);
    await page.click('#login_btn');
    await page.waitForURL(/main\.html/, { timeout: 30000 });
    await page.waitForTimeout(2000);

    const result = await page.evaluate(async () => {
      const deviceInfo = await $post('get_device_info', null, 'nocheck');
      const sysValues = await $post('get_value_by_xmlnode', {
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
      const portNum = parseInt(deviceInfo.port_num) || 4;
      const mainSSIDIdx58G = parseInt(deviceInfo.MainSSIDIndex_58G) || 5;

      const output = {
        authenticated: true,
        ModelName: sysValues.model || deviceInfo.devicetype || 'N/A',
        SoftwareVersion: sysValues.firmware || 'N/A',
        WANAccessType: wanType,
        uptime: sysValues.uptime || '0',
        cpu_usage: sysValues.cpu_usage || '0',
        mem_total: sysValues.mem_total || '0',
        mem_free: sysValues.mem_free || '0',
        pon_reg_state: sysValues.pon_state || '',
        loid_reg_state: sysValues.reg_state || '',
        ponBytesSent: '0',
        ponBytesReceived: '0',
      };

      // Query LAN port counters
      const lanObj = {
        url: 'LANDevice.1.LANEthernetInterfaceConfig.',
        num: portNum,
        node: {
          Status: 'Status',
          X_FH_LinkSpeed: 'X_FH_LinkSpeed',
          BytesSent: 'Stats.BytesSent',
          BytesReceived: 'Stats.BytesReceived',
          PacketsSent: 'Stats.PacketsSent',
          PacketsReceived: 'Stats.PacketsReceived',
        }
      };
      const lanResp = await $post('get_xml_childnode_value', lanObj);
      if (lanResp && lanResp.data) {
        for (const port of lanResp.data) {
          const idx = port.child_node_idx;
          output[`lan${idx}_status`] = port.Status || '';
          output[`lan${idx}_speed`] = port.X_FH_LinkSpeed || '';
          output[`lan${idx}_bytes_sent`] = port.BytesSent || '0';
          output[`lan${idx}_bytes_received`] = port.BytesReceived || '0';
          output[`lan${idx}_packets_sent`] = port.PacketsSent || '0';
          output[`lan${idx}_packets_received`] = port.PacketsReceived || '0';
        }
      }

      // Query WiFi 2.4GHz SSID counters (indices 1-4)
      const wifi24SsidObj = {
        url: 'WiFi.SSID.',
        index: '1-4',
        node: {
          Enable: 'Enable',
          SSID: 'SSID',
          BytesSent: 'Stats.BytesSent',
          BytesReceived: 'Stats.BytesReceived',
          PacketsSent: 'Stats.PacketsSent',
          PacketsReceived: 'Stats.PacketsReceived',
        }
      };
      const wifi24Ssids = await $post('get_xml_childnode_value', wifi24SsidObj);
      if (wifi24Ssids && wifi24Ssids.data && wifi24Ssids.data.length > 0) {
        let totalBytesSent = 0;
        let totalBytesReceived = 0;
        let totalPacketsSent = 0;
        let totalPacketsReceived = 0;
        for (let i = 0; i < wifi24Ssids.data.length; i++) {
          const ssid = wifi24Ssids.data[i];
          output[`wifi24_ssid_${i+1}`] = ssid.SSID || '';
          totalBytesSent += parseInt(ssid.BytesSent || '0', 10) || 0;
          totalBytesReceived += parseInt(ssid.BytesReceived || '0', 10) || 0;
          totalPacketsSent += parseInt(ssid.PacketsSent || '0', 10) || 0;
          totalPacketsReceived += parseInt(ssid.PacketsReceived || '0', 10) || 0;
        }
        output.wifi24_bytes_sent = String(totalBytesSent);
        output.wifi24_bytes_received = String(totalBytesReceived);
        output.wifi24_packets_sent = String(totalPacketsSent);
        output.wifi24_packets_received = String(totalPacketsReceived);
      }

      // Query WiFi 5GHz SSID counters
      try {
        const wifi5SsidObj = {
          url: 'WiFi.SSID.',
          index: `${mainSSIDIdx58G}-${mainSSIDIdx58G + 3}`,
          node: {
            Enable: 'Enable',
            SSID: 'SSID',
            BytesSent: 'Stats.BytesSent',
            BytesReceived: 'Stats.BytesReceived',
            PacketsSent: 'Stats.PacketsSent',
            PacketsReceived: 'Stats.PacketsReceived',
          }
        };
        const wifi5Ssids = await $post('get_xml_childnode_value', wifi5SsidObj);
        if (wifi5Ssids && wifi5Ssids.data && wifi5Ssids.data.length > 0) {
          let totalBytesSent = 0;
          let totalBytesReceived = 0;
          let totalPacketsSent = 0;
          let totalPacketsReceived = 0;
          for (let i = 0; i < wifi5Ssids.data.length; i++) {
            const ssid = wifi5Ssids.data[i];
            output[`wifi5_ssid_${i+1}`] = ssid.SSID || '';
            totalBytesSent += parseInt(ssid.BytesSent || '0', 10) || 0;
            totalBytesReceived += parseInt(ssid.BytesReceived || '0', 10) || 0;
            totalPacketsSent += parseInt(ssid.PacketsSent || '0', 10) || 0;
            totalPacketsReceived += parseInt(ssid.PacketsReceived || '0', 10) || 0;
          }
          output.wifi5_bytes_sent = String(totalBytesSent);
          output.wifi5_bytes_received = String(totalBytesReceived);
          output.wifi5_packets_sent = String(totalPacketsSent);
          output.wifi5_packets_received = String(totalPacketsReceived);
        }
      } catch (e) {
        // 5GHz query may fail if MainSSIDIndex_58G is wrong; will scrape from UI as fallback
      }

      // Query WiFi radio channels
      try {
        const radioObj = {
          url: 'WiFi.Radio.',
          num: 2,
          node: {
            ChannelsInUse: 'ChannelsInUse',
            OperatingStandards: 'OperatingStandards',
          }
        };
        const radioResp = await $post('get_xml_childnode_value', radioObj);
        if (radioResp && radioResp.data && radioResp.data.length >= 2) {
          output.wifi24_channel = radioResp.data[0].ChannelsInUse || '';
          output.wifi24_standard = radioResp.data[0].OperatingStandards || '';
          output.wifi5_channel = radioResp.data[1].ChannelsInUse || '';
          output.wifi5_standard = radioResp.data[1].OperatingStandards || '';
        }
      } catch (e) {}

      // Query optical info based on PON mode
      const ponMode = parseInt(deviceInfo.pon_mode);
      if (ponMode < 3) {
        try {
          const optical = await $post('get_value_by_xmlnode', {
            txpower: 'WANDevice.1.X_FH_EponInterfaceConfig.1.TXPower',
            rxpower: 'WANDevice.1.X_FH_EponInterfaceConfig.1.RXPower',
            voltage: 'WANDevice.1.X_FH_EponInterfaceConfig.1.SupplyVottage',
            bias: 'WANDevice.1.X_FH_EponInterfaceConfig.1.BiasCurrent',
            temp: 'WANDevice.1.X_FH_EponInterfaceConfig.1.TransceiverTemperature',
          });
          output.txpower = (optical.txpower || '').toString().replace(' dBm', '');
          output.rxpower = (optical.rxpower || '').toString().replace(' dBm', '');
          output.supplyvottage = (optical.voltage || '').toString().replace(' V', '');
          output.biascurrent = (optical.bias || '').toString().replace(' mA', '');
          output.transceivertemperature = (optical.temp || '').toString().replace(' ℃', '').replace(' C', '');
        } catch (e) {}
      } else {
        try {
          const optical = await $post('get_value_by_xmlnode', {
            txpower: 'WANDevice.1.X_FH_GponInterfaceConfig.1.TXPower',
            rxpower: 'WANDevice.1.X_FH_GponInterfaceConfig.1.RXPower',
            voltage: 'WANDevice.1.X_FH_GponInterfaceConfig.1.SupplyVottage',
            bias: 'WANDevice.1.X_FH_GponInterfaceConfig.1.BiasCurrent',
            temp: 'WANDevice.1.X_FH_GponInterfaceConfig.1.TransceiverTemperature',
          });
          output.txpower = (optical.txpower || '').toString().replace(' dBm', '');
          output.rxpower = (optical.rxpower || '').toString().replace(' dBm', '');
          output.supplyvottage = (optical.voltage || '').toString().replace(' V', '');
          output.biascurrent = (optical.bias || '').toString().replace(' mA', '');
          output.transceivertemperature = (optical.temp || '').toString().replace(' ℃', '').replace(' C', '');
        } catch (e) {}
      }

      output.NOTA = 'Firmware RP3084+ autenticado via navegador. Datos via API: ' + Object.keys(output).filter(k => k.startsWith('lan') || k.startsWith('wifi')).length + ' contadores de trafico localizados. Total PON no expuesto por el firmware.';
      return output;
    });

    // Fallback: scrape optical info from UI if API returned empty
    if (!result.txpower && !result.rxpower) {
      await page.evaluate(() => { location.hash = '#/status/opticalInfo/opticalInfo'; });
      await page.waitForTimeout(2500);
      const opticalText = await page.evaluate(() => document.body.innerText);
      result.txpower = extractMetric(opticalText, 'Transmitted Power').replace(' dBm', '').trim();
      result.rxpower = extractMetric(opticalText, 'Received Power').replace(' dBm', '').trim();
      result.transceivertemperature = extractMetric(opticalText, 'Operating Temperature').replace(' ℃', '').trim();
      result.supplyvottage = extractMetric(opticalText, 'Supply Voltage').replace(' V', '').trim();
      result.biascurrent = extractMetric(opticalText, 'Bias Current').replace(' mA', '').trim();
    }

    // Fallback: scrape 5GHz wifi from UI if API didn't return counters
    if (!result.wifi5_bytes_sent && !result.wifi5_bytes_received) {
      await page.evaluate(() => { location.hash = '#/status/wifiStatus/wifiStatus_5g'; });
      await page.waitForTimeout(2500);
      const wifi5Text = await page.evaluate(() => document.body.innerText);
      result.wifi5_ssid_1 = extractMetric(wifi5Text, 'SSID1 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
      result.wifi5_ssid_2 = extractMetric(wifi5Text, 'SSID2 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
      result.wifi5_packets_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Packets Count'));
      result.wifi5_bytes_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Bytes Count'));
      result.wifi5_packets_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Packets Count'));
      result.wifi5_bytes_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Bytes Count'));
      result.wifi5_channel = extractMetric(wifi5Text, 'Frequency (Channel)').trim();
    }

    // Fallback: scrape 2.4GHz wifi from UI if API didn't return counters
    if (!result.wifi24_bytes_sent && !result.wifi24_bytes_received) {
      await page.evaluate(() => { location.hash = '#/status/wifiStatus/wifiStatus'; });
      await page.waitForTimeout(2500);
      const wifi24Text = await page.evaluate(() => document.body.innerText);
      result.wifi24_ssid_1 = extractMetric(wifi24Text, 'SSID1 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
      result.wifi24_ssid_2 = extractMetric(wifi24Text, 'SSID2 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
      result.wifi24_packets_received = normalizeNumberString(extractMetric(wifi24Text, 'Received Packets Count'));
      result.wifi24_bytes_received = normalizeNumberString(extractMetric(wifi24Text, 'Received Bytes Count'));
      result.wifi24_packets_sent = normalizeNumberString(extractMetric(wifi24Text, 'Sent Packets Count'));
      result.wifi24_bytes_sent = normalizeNumberString(extractMetric(wifi24Text, 'Sent Bytes Count'));
      result.wifi24_channel = extractMetric(wifi24Text, 'Frequency (Channel)').trim();
    }

    console.log(JSON.stringify({ success: true, data: result }));
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.log(JSON.stringify({ success: false, error: error.message }));
  process.exit(1);
});
