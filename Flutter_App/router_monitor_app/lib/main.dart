import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';
import 'package:webview_flutter/webview_flutter.dart';

void main() {
  runApp(const RouterMonitorApp());
}

class RouterMonitorApp extends StatelessWidget {
  const RouterMonitorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Monitor GPON',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1565C0),
          brightness: Brightness.dark,
        ),
        useMaterial3: true,
      ),
      home: const MonitorPage(),
    );
  }
}

class MonitorPage extends StatefulWidget {
  const MonitorPage({super.key});

  @override
  State<MonitorPage> createState() => _MonitorPageState();
}

class _MonitorPageState extends State<MonitorPage> {
  String routerIp = "192.168.1.1";
  String username = "user";
  String password = "user1234";
  String apiPath = "/cgi-bin/ajax";
  String ajaxMethod = "get_base_info";
  bool isLoading = false;
  String errorMessage = "";
  Map<String, dynamic> routerData = {};
  DateTime? lastUpdate;
  final List<TrafficSample> trafficSamples = [];
  TrafficRate? currentRate;
  TrafficRate? minRate;
  TrafficRate? maxRate;
  WebViewController? _routerWebView;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      routerIp = prefs.getString('router_ip') ?? "192.168.1.1";
      username = prefs.getString('router_user') ?? "user";
      password = prefs.getString('router_password') ?? "user1234";
      apiPath = prefs.getString('api_path') ?? "/cgi-bin/ajax";
      ajaxMethod = prefs.getString('ajax_method') ?? "get_base_info";
    });
    _fetchData();
  }

  Future<void> _saveSettings(String ip, String user, String pass, String path, String method) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('router_ip', ip);
    await prefs.setString('router_user', user);
    await prefs.setString('router_password', pass);
    await prefs.setString('api_path', path);
    await prefs.setString('ajax_method', method);
  }

  Future<void> _fetchData() async {
    setState(() {
      isLoading = true;
      errorMessage = "";
    });

    try {
      final data = await _fetchRouterData();
      _recordTrafficSample(data);
      setState(() {
        routerData = data;
        lastUpdate = DateTime.now();
        isLoading = false;
      });
    } catch (e) {
      setState(() {
        errorMessage = e.toString().replaceFirst('Exception: ', '');
        isLoading = false;
      });
    }
  }

  Future<Map<String, dynamic>> _fetchRouterData() async {
    final oldFirmwareError = await _tryFetchOldFirmware();
    if (oldFirmwareError.data != null) {
      return oldFirmwareError.data!;
    }

    try {
      return await _fetchNewFirmwareWithWebView();
    } catch (e) {
      throw Exception(
        'No se pudo consultar el router. Firmware antiguo: ${oldFirmwareError.error}. Firmware RP3084+: $e',
      );
    }
  }

  Future<_RouterFetchResult> _tryFetchOldFirmware() async {
    try {
      final headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'http://$routerIp/html/stateOverview_inter.html',
        'Accept': '*/*',
      };

      final normalizedPath = apiPath.startsWith('/') ? apiPath : '/$apiPath';
      final url = 'http://$routerIp$normalizedPath?ajaxmethod=$ajaxMethod&_=${DateTime.now().millisecondsSinceEpoch / 1000}';
      final response = await http.get(Uri.parse(url), headers: headers).timeout(
        const Duration(seconds: 10),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is Map<String, dynamic>) {
          data['firmwareMode'] = 'OLD';
          return _RouterFetchResult.data(data);
        }
      }
      return _RouterFetchResult.error('HTTP ${response.statusCode}');
    } catch (e) {
      return _RouterFetchResult.error(e.toString());
    }
  }

  Future<Map<String, dynamic>> _fetchNewFirmwareWithWebView() async {
    // Limpia la sesion anterior del router (ej: "Somebody has already logged in")
    // para que el login WebView no sea rechazado por una sesion activa previa.
    try {
      final cookieManager = WebViewCookieManager();
      await cookieManager.clearCookies();
    } catch (_) {}

    final controller = await _ensureRouterWebView();

    // Reintenta una vez recargando login.html limpio si la sesion quedo colgada
    // o si la primera carga no llego a main.html.
    var lastLoginError = '';
    for (var attempt = 0; attempt < 2; attempt++) {
      try {
        await controller.loadRequest(Uri.parse('http://$routerIp/login.html'));
        await _waitForWebViewReady(controller);
        await _waitForLoginControls(controller);

        await controller.runJavaScript(_loginScript());

        final loginOk = await _waitForWebViewLogin(controller);
        if (!loginOk) {
          lastLoginError = 'no se redirigio a main.html tras el login';
        } else {
          lastLoginError = '';
          break;
        }
      } catch (e) {
        lastLoginError = e.toString().replaceFirst('Exception: ', '');
      }
      await Future<void>.delayed(const Duration(milliseconds: 1000));
    }

    if (lastLoginError.isNotEmpty) {
      final diagnostic = await _webViewDiagnostic(controller);
      throw Exception('$lastLoginError (intento 2): $diagnostic');
    }

    // Espera de estabilizacion del framework main.html (el desktop espera 2s
    // en router_web_client.js antes de consultar). Si se consulta antes, el
    // router del colegio puede rechazar la llamada por sesion aun no activa.
    await Future<void>.delayed(const Duration(seconds: 2));

    // Verify $post is truly available before querying
    var hasPost = await controller.runJavaScriptReturningResult('typeof window.\$post === "function"');
    if (!hasPost.toString().contains('true')) {
      for (var i = 0; i < 20; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 500));
        hasPost = await controller.runJavaScriptReturningResult('typeof window.\$post === "function"');
        if (hasPost.toString().contains('true')) break;
      }
      if (!hasPost.toString().contains('true')) {
        final diagnostic = await _webViewDiagnostic(controller);
        throw Exception('\$post no disponible tras login: $diagnostic');
      }
    }

    // Consulta de datos con reintento. IMPORTANTE: el script asigna el resultado a
    // window.__routerMonitorResult (patron sincrono) porque runJavaScriptReturningResult
    // de Android WebView NO espera promesas: un IIFE async se serializa como "{}" o null.
    var lastQueryError = '';
    for (var attempt = 0; attempt < 2; attempt++) {
      await controller.runJavaScript('window.__routerMonitorResult = null;');
      await controller.runJavaScript(_newFirmwareQueryScript());

      // Poll sincrono hasta que el script asigne el resultado.
      var raw = '';
      for (var i = 0; i < 40; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 500));
        raw = (await controller.runJavaScriptReturningResult('window.__routerMonitorResult')).toString();
        if (raw.contains('success')) break;
      }

      final decoded = _decodeWebViewJson(raw);
      if (decoded is Map<String, dynamic> && decoded['success'] == true) {
        final data = Map<String, dynamic>.from(decoded['data'] as Map);
        data['firmwareMode'] = 'NEW';
        return data;
      }
      if (decoded is Map<String, dynamic>) {
        lastQueryError = decoded['error']?.toString() ?? 'sin detalle';
      } else {
        lastQueryError = 'respuesta invalida o vacia del WebView';
      }
      if (attempt == 0) {
        await controller.loadRequest(Uri.parse('http://$routerIp/main.html'));
        await _waitForWebViewReady(controller);
        await Future<void>.delayed(const Duration(seconds: 2));
      }
    }

    final diagnostic = await _webViewDiagnostic(controller);
    throw Exception('fallo en consulta de datos RP3084+ ($lastQueryError) tras login OK: $diagnostic');
  }

  Future<WebViewController> _ensureRouterWebView() async {
    if (_routerWebView != null) return _routerWebView!;

    final controller = WebViewController();
    await controller.setJavaScriptMode(JavaScriptMode.unrestricted);
    await controller.setUserAgent(
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    );

    setState(() {
      _routerWebView = controller;
    });

    // Give Android time to attach the hidden WebViewWidget before navigation.
    // Some devices need longer for the platform view to render (even hidden).
    await Future<void>.delayed(const Duration(seconds: 1));
    return controller;
  }

  Future<void> _waitForWebViewReady(WebViewController controller) async {
    for (var i = 0; i < 30; i++) {
      final state = await controller.runJavaScriptReturningResult('document.readyState');
      if (state.toString().contains('complete') || state.toString().contains('interactive')) return;
      await Future<void>.delayed(const Duration(milliseconds: 500));
    }
  }

  Future<void> _waitForLoginControls(WebViewController controller) async {
    // Wait for login form controls AND $post framework ($post exists on login page too).
    // El router del colegio (HG5853SF) puede servir una pagina de login con
    // variantes de selectores; se prueban ambos conjuntos antes de rendirse.
    for (var i = 0; i < 60; i++) {
      final ready = await controller.runJavaScriptReturningResult('''
        Boolean((document.querySelector('#user_name') &&
          document.querySelector('#loginpp') &&
          document.querySelector('#login_btn') &&
          typeof window.\$post === "function") ||
          (document.querySelector('input[type="password"]') &&
          typeof window.\$post === "function"))
      ''');
      if (ready.toString().contains('true')) return;
      await Future<void>.delayed(const Duration(milliseconds: 500));
    }

    final diagnostic = await _webViewDiagnostic(controller);
    throw Exception('controles de login RP3084+ no encontrados: $diagnostic');
  }

  Future<bool> _waitForWebViewLogin(WebViewController controller) async {
    // Wait for redirect to main.html after login
    for (var i = 0; i < 90; i++) {
      final href = await controller.runJavaScriptReturningResult('location.href');
      if (href.toString().contains('main.html')) break;
      await Future<void>.delayed(const Duration(milliseconds: 500));
    }

    final href = (await controller.runJavaScriptReturningResult('location.href')).toString();
    if (!href.contains('main.html')) return false;

    // Wait for $post to be available on main.html (JS framework loads after redirect)
    for (var i = 0; i < 40; i++) {
      final hasPost = await controller.runJavaScriptReturningResult('typeof window.\$post === "function"');
      if (hasPost.toString().contains('true')) return true;
      await Future<void>.delayed(const Duration(milliseconds: 500));
    }

    return false;
  }

  Future<String> _webViewDiagnostic(WebViewController controller) async {
    try {
      final raw = await controller.runJavaScriptReturningResult('''
        JSON.stringify({
          href: location.href,
          title: document.title,
          body: (document.body && document.body.innerText || '').slice(0, 220)
        })
      ''');
      return raw.toString();
    } catch (e) {
      return e.toString();
    }
  }

  String _loginScript() => '''
    (async () => {
      const userInput = document.querySelector('#user_name') ||
        document.querySelector('input[type="text"]');
      const passInput = document.querySelector('#loginpp') ||
        document.querySelector('input[type="password"]');
      const loginButton = document.querySelector('#login_btn') ||
        document.querySelector('button[type="submit"]') ||
        document.querySelector('.el-button--primary');
      if (!userInput || !passInput || !loginButton) {
        throw new Error('No se encontraron controles de login RP3084+');
      }

      const setValue = (element, value) => {
        const proto = Object.getPrototypeOf(element);
        const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
        if (descriptor && descriptor.set) {
          descriptor.set.call(element, value);
        } else {
          element.value = value;
        }
        element.dispatchEvent(new Event('input', { bubbles: true }));
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('blur', { bubbles: true }));
      };

      setValue(userInput, ${jsonEncode(username)});
      setValue(passInput, ${jsonEncode(password)});

      // Primary: use the router's own doLoginRequest() (reads the inputs above and
      // calls \$post('DO_WEB_LOGIN', {yhm, mm}), redirecting to main.html on result==0).
      if (typeof window.doLoginRequest === 'function') {
        try {
          window.doLoginRequest();
          return;
        } catch (e) {}
      }

      // Secondary: call router post helper directly with the exact payload login.js uses.
      if (typeof window.\$post === 'function') {
        try {
          const result = await window.\$post('DO_WEB_LOGIN', {
            yhm: ${jsonEncode(username)},
            mm: ${jsonEncode(password)}
          });
          if (result && (result.result === 0 || result.result === '0')) {
            window.location.href = '/main.html';
            return;
          }
        } catch (e) {
          // Fall back to button click below
        }
      }

      // Fallback: simulate button click
      loginButton.removeAttribute('disabled');
      loginButton.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window }));
      loginButton.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window }));
      loginButton.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
      if (typeof loginButton.onclick === 'function') loginButton.onclick();
    })();
  ''';

  dynamic _decodeWebViewJson(Object raw) {
    dynamic value = raw;
    for (var i = 0; i < 2; i++) {
      if (value is String) {
        value = json.decode(value);
      }
    }
    return value;
  }

  String _newFirmwareQueryScript() => r'''
    (async () => {
      function extractMetric(text, label) {
        const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const match = text.match(new RegExp(`${escaped}\\s+([^\\n]+)`));
        return match ? match[1].trim() : '';
      }
      function normalizeNumberString(value) {
        return (value || '').replace(/,/g, '').trim();
      }
      try {
        if (typeof $post !== 'function') {
          throw new Error('El frontend del router no expuso $post');
        }

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
          Manufacturer: deviceInfo.manufacturer || 'N/A',
          SoftwareVersion: sysValues.firmware || 'N/A',
          WANAccessType: wanType,
          uptime: sysValues.uptime || '0',
          cpu_usage: sysValues.cpu_usage || '0',
          mem_total: sysValues.mem_total || '0',
          mem_free: sysValues.mem_free || '0',
          pon_reg_state: sysValues.pon_state || '',
          loid_reg_state: sysValues.reg_state || '',
          ponBytesSent: '0',
          ponBytesReceived: '0'
        };

        const lanResp = await $post('get_xml_childnode_value', {
          url: 'LANDevice.1.LANEthernetInterfaceConfig.',
          num: portNum,
          node: {
            Status: 'Status',
            X_FH_LinkSpeed: 'X_FH_LinkSpeed',
            BytesSent: 'Stats.BytesSent',
            BytesReceived: 'Stats.BytesReceived',
            PacketsSent: 'Stats.PacketsSent',
            PacketsReceived: 'Stats.PacketsReceived'
          }
        });
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

        const wifi24Ssids = await $post('get_xml_childnode_value', {
          url: 'WiFi.SSID.',
          index: '1-4',
          node: {
            Enable: 'Enable', SSID: 'SSID', BytesSent: 'Stats.BytesSent',
            BytesReceived: 'Stats.BytesReceived', PacketsSent: 'Stats.PacketsSent',
            PacketsReceived: 'Stats.PacketsReceived'
          }
        });
        if (wifi24Ssids && wifi24Ssids.data && wifi24Ssids.data.length > 0) {
          let totalBytesSent = 0;
          let totalBytesReceived = 0;
          let totalPacketsSent = 0;
          let totalPacketsReceived = 0;
          for (let i = 0; i < wifi24Ssids.data.length; i++) {
            const ssid = wifi24Ssids.data[i];
            output[`wifi24_ssid_${i + 1}`] = ssid.SSID || '';
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

        try {
          const wifi5Ssids = await $post('get_xml_childnode_value', {
            url: 'WiFi.SSID.',
            index: `${mainSSIDIdx58G}-${mainSSIDIdx58G + 3}`,
            node: {
              Enable: 'Enable', SSID: 'SSID', BytesSent: 'Stats.BytesSent',
              BytesReceived: 'Stats.BytesReceived', PacketsSent: 'Stats.PacketsSent',
              PacketsReceived: 'Stats.PacketsReceived'
            }
          });
          if (wifi5Ssids && wifi5Ssids.data && wifi5Ssids.data.length > 0) {
            let totalBytesSent = 0;
            let totalBytesReceived = 0;
            let totalPacketsSent = 0;
            let totalPacketsReceived = 0;
            for (let i = 0; i < wifi5Ssids.data.length; i++) {
              const ssid = wifi5Ssids.data[i];
              output[`wifi5_ssid_${i + 1}`] = ssid.SSID || '';
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
        } catch (e) {}

        try {
          const radioResp = await $post('get_xml_childnode_value', {
            url: 'WiFi.Radio.',
            num: 2,
            node: { ChannelsInUse: 'ChannelsInUse', OperatingStandards: 'OperatingStandards' }
          });
          if (radioResp && radioResp.data && radioResp.data.length >= 2) {
            output.wifi24_channel = radioResp.data[0].ChannelsInUse || '';
            output.wifi24_standard = radioResp.data[0].OperatingStandards || '';
            output.wifi5_channel = radioResp.data[1].ChannelsInUse || '';
            output.wifi5_standard = radioResp.data[1].OperatingStandards || '';
          }
        } catch (e) {}

        const ponMode = parseInt(deviceInfo.pon_mode);
        const opticalPrefix = ponMode < 3
          ? 'WANDevice.1.X_FH_EponInterfaceConfig.1.'
          : 'WANDevice.1.X_FH_GponInterfaceConfig.1.';
        try {
          const optical = await $post('get_value_by_xmlnode', {
            txpower: `${opticalPrefix}TXPower`,
            rxpower: `${opticalPrefix}RXPower`,
            voltage: `${opticalPrefix}SupplyVottage`,
            bias: `${opticalPrefix}BiasCurrent`,
            temp: `${opticalPrefix}TransceiverTemperature`
          });
          output.txpower = (optical.txpower || '').toString().replace(' dBm', '');
          output.rxpower = (optical.rxpower || '').toString().replace(' dBm', '');
          output.supplyvottage = (optical.voltage || '').toString().replace(' V', '');
          output.biascurrent = (optical.bias || '').toString().replace(' mA', '');
          output.transceivertemperature = (optical.temp || '').toString().replace(' ℃', '').replace(' C', '');
        } catch (e) {}

        if (!output.txpower && !output.rxpower) {
          location.hash = '#/status/opticalInfo/opticalInfo';
          await new Promise(resolve => setTimeout(resolve, 2500));
          const opticalText = document.body.innerText;
          output.txpower = extractMetric(opticalText, 'Transmitted Power').replace(' dBm', '').trim();
          output.rxpower = extractMetric(opticalText, 'Received Power').replace(' dBm', '').trim();
          output.transceivertemperature = extractMetric(opticalText, 'Operating Temperature').replace(' ℃', '').trim();
          output.supplyvottage = extractMetric(opticalText, 'Supply Voltage').replace(' V', '').trim();
          output.biascurrent = extractMetric(opticalText, 'Bias Current').replace(' mA', '').trim();
        }

        if (!output.wifi5_bytes_sent && !output.wifi5_bytes_received) {
          location.hash = '#/status/wifiStatus/wifiStatus_5g';
          await new Promise(resolve => setTimeout(resolve, 2500));
          const wifi5Text = document.body.innerText;
          output.wifi5_ssid_1 = extractMetric(wifi5Text, 'SSID1 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
          output.wifi5_ssid_2 = extractMetric(wifi5Text, 'SSID2 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
          output.wifi5_packets_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Packets Count'));
          output.wifi5_bytes_received = normalizeNumberString(extractMetric(wifi5Text, 'Received Bytes Count'));
          output.wifi5_packets_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Packets Count'));
          output.wifi5_bytes_sent = normalizeNumberString(extractMetric(wifi5Text, 'Sent Bytes Count'));
          output.wifi5_channel = extractMetric(wifi5Text, 'Frequency (Channel)').trim();
        }

        if (!output.wifi24_bytes_sent && !output.wifi24_bytes_received) {
          location.hash = '#/status/wifiStatus/wifiStatus';
          await new Promise(resolve => setTimeout(resolve, 2500));
          const wifi24Text = document.body.innerText;
          output.wifi24_ssid_1 = extractMetric(wifi24Text, 'SSID1 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
          output.wifi24_ssid_2 = extractMetric(wifi24Text, 'SSID2 Name').replace(/\s+Enable$|\s+Disable$/, '').trim();
          output.wifi24_packets_received = normalizeNumberString(extractMetric(wifi24Text, 'Received Packets Count'));
          output.wifi24_bytes_received = normalizeNumberString(extractMetric(wifi24Text, 'Received Bytes Count'));
          output.wifi24_packets_sent = normalizeNumberString(extractMetric(wifi24Text, 'Sent Packets Count'));
          output.wifi24_bytes_sent = normalizeNumberString(extractMetric(wifi24Text, 'Sent Bytes Count'));
          output.wifi24_channel = extractMetric(wifi24Text, 'Frequency (Channel)').trim();
        }

        output.NOTA = 'Firmware RP3084+ autenticado via WebView. Contadores por LAN/WiFi; total PON no expuesto.';
        window.__routerMonitorResult = JSON.stringify({ success: true, data: output });
      } catch (error) {
        const detail = (error && (error.message || error.name || String(error))) || 'sin detalle';
        const stack = (error && error.stack) || '';
        window.__routerMonitorResult = JSON.stringify({ success: false, error: detail, stack: stack.slice(0, 400) });
      }
    })();
  ''';

  void _recordTrafficSample(Map<String, dynamic> data) {
    final now = DateTime.now();
    final trafficBytes = _trafficBytesForRate(data);
    final sent = trafficBytes.sent;
    final received = trafficBytes.received;
    final previous = trafficSamples.isNotEmpty ? trafficSamples.last : null;
    TrafficRate? rate;

    if (previous != null) {
      final seconds = now.difference(previous.timestamp).inMilliseconds / 1000;
      final sentDelta = sent - previous.sentBytes;
      final receivedDelta = received - previous.receivedBytes;

      if (seconds > 0 && sentDelta >= 0 && receivedDelta >= 0) {
        rate = TrafficRate(
          timestamp: now,
          sentMbps: sentDelta * 8 / seconds / 1000000,
          receivedMbps: receivedDelta * 8 / seconds / 1000000,
          intervalSeconds: seconds,
        );
        currentRate = rate;
        minRate = minRate == null || rate.totalMbps < minRate!.totalMbps ? rate : minRate;
        maxRate = maxRate == null || rate.totalMbps > maxRate!.totalMbps ? rate : maxRate;
      }
    }

    trafficSamples.add(TrafficSample(
      timestamp: now,
      sentBytes: sent,
      receivedBytes: received,
      rate: rate,
    ));

    if (trafficSamples.length > 200) {
      trafficSamples.removeAt(0);
    }
  }

  _TrafficBytes _trafficBytesForRate(Map<String, dynamic> data) {
    if (data['firmwareMode'] == 'NEW') {
      return _aggregateInterfaceBytes(data);
    }
    return _TrafficBytes(
      sent: _parseInt(data['ponBytesSent']),
      received: _parseInt(data['ponBytesReceived']),
    );
  }

  _TrafficBytes _aggregateInterfaceBytes(Map<String, dynamic> data) {
    var sent = 0;
    var received = 0;
    for (var i = 1; i <= 9; i++) {
      final status = data['lan${i}_status']?.toString() ?? '';
      final lanSent = _parseInt(data['lan${i}_bytes_sent']);
      final lanReceived = _parseInt(data['lan${i}_bytes_received']);
      if (status == 'Up' || lanSent > 0 || lanReceived > 0) {
        sent += lanSent;
        received += lanReceived;
      }
    }
    for (final band in ['wifi24', 'wifi5']) {
      sent += _parseInt(data['${band}_bytes_sent']);
      received += _parseInt(data['${band}_bytes_received']);
    }
    data['interfaceBytesSentTotal'] = sent.toString();
    data['interfaceBytesReceivedTotal'] = received.toString();
    return _TrafficBytes(sent: sent, received: received);
  }

  int _parseInt(dynamic value) {
    return int.tryParse(value?.toString() ?? '') ?? 0;
  }

  String _formatBytes(int bytes) {
    final gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) return '${gb.toStringAsFixed(2)} GB';
    final mb = bytes / (1024 * 1024);
    return '${mb.toStringAsFixed(2)} MB';
  }

  String _formatUptime(int seconds) {
    final dias = seconds ~/ 86400;
    final horas = (seconds % 86400) ~/ 3600;
    final minutos = (seconds % 3600) ~/ 60;
    if (dias > 0) return '${dias}d ${horas}h ${minutos}m';
    if (horas > 0) return '${horas}h ${minutos}m';
    return '${minutos}m';
  }

  String _formatNumber(int number) {
    return number.toString().replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
  }

  String _formatMbps(double value) {
    if (value >= 1000) return '${(value / 1000).toStringAsFixed(2)} Gbps';
    return '${value.toStringAsFixed(2)} Mbps';
  }

  String _formatDateTime(DateTime timestamp) {
    return DateFormat('yyyy-MM-dd HH:mm:ss').format(timestamp);
  }

  Future<void> _exportReport() async {
    if (routerData.isEmpty) {
      setState(() {
        errorMessage = "No hay datos del router para exportar";
      });
      return;
    }

    final report = {
      'exportedAt': DateTime.now().toIso8601String(),
      'router': {
        'ip': routerIp,
        'apiPath': apiPath,
        'ajaxMethod': ajaxMethod,
        'model': routerData['ModelName'],
        'manufacturer': routerData['Manufacturer'],
        'firmware': routerData['SoftwareVersion'],
      },
      'lastData': routerData,
      'bandwidthFromRouterCounters': {
        'source': routerData['firmwareMode'] == 'NEW'
            ? 'Suma LAN + WiFi 2.4 GHz + WiFi 5 GHz'
            : 'ponBytesSent/ponBytesReceived',
        'note': routerData['firmwareMode'] == 'NEW'
            ? 'Total observado por interfaces locales; no es contador WAN/GPON y puede incluir trafico interno.'
            : 'Calculado desde contadores del router entre lecturas; no mide trafico del celular.',
        'currentMbps': currentRate?.toJson(),
        'minTotalMbps': minRate?.toJson(),
        'maxTotalMbps': maxRate?.toJson(),
      },
      'interfaceCounters': _interfaceCountersForExport(),
      'samples': trafficSamples.map((sample) => sample.toJson()).toList(),
    };

    final buffer = StringBuffer()
      ..writeln('Monitor GPON - Reporte exportado')
      ..writeln('Fecha: ${_formatDateTime(DateTime.now())}')
      ..writeln('Router: $routerIp')
      ..writeln('Endpoint: $apiPath / $ajaxMethod')
      ..writeln('Modelo: ${routerData['ModelName'] ?? 'N/A'}')
      ..writeln('Fabricante: ${routerData['Manufacturer'] ?? 'N/A'}')
      ..writeln('Firmware: ${routerData['SoftwareVersion'] ?? 'N/A'}')
      ..writeln('')
      ..writeln('Trafico acumulado del router')
      ..writeln('Fuente: ${_trafficCounterSourceLabel()}')
      ..writeln('Enviado: ${_formatBytes(_displayTrafficSentBytes())}')
      ..writeln('Recibido: ${_formatBytes(_displayTrafficReceivedBytes())}')
      ..writeln('')
      ..writeln('Ancho de banda observado desde el router')
      ..writeln('Actual: ${currentRate == null ? 'N/A' : _formatMbps(currentRate!.totalMbps)}')
      ..writeln('Minimo sesion: ${minRate == null ? 'N/A' : _formatMbps(minRate!.totalMbps)}')
      ..writeln('Maximo sesion: ${maxRate == null ? 'N/A' : _formatMbps(maxRate!.totalMbps)}')
      ..writeln('')
      ..writeln('Contadores por interfaz RP3084+')
      ..write(_interfaceCountersText())
      ..writeln('')
      ..writeln('JSON')
      ..writeln(const JsonEncoder.withIndent('  ').convert(report));

    await Share.share(buffer.toString(), subject: 'Reporte Monitor GPON $routerIp');
  }

  Map<String, dynamic> _interfaceCountersForExport() {
    final counters = <String, dynamic>{};
    for (var i = 1; i <= 9; i++) {
      final status = routerData['lan${i}_status'];
      if (status == null || status.toString().isEmpty) continue;
      counters['lan$i'] = {
        'status': status,
        'speed': routerData['lan${i}_speed'],
        'sentBytes': routerData['lan${i}_bytes_sent'],
        'receivedBytes': routerData['lan${i}_bytes_received'],
      };
    }
    for (final band in ['wifi24', 'wifi5']) {
      if (routerData['${band}_bytes_sent'] == null && routerData['${band}_bytes_received'] == null) continue;
      counters[band] = {
        'ssid1': routerData['${band}_ssid_1'],
        'ssid2': routerData['${band}_ssid_2'],
        'channel': routerData['${band}_channel'],
        'standard': routerData['${band}_standard'],
        'sentBytes': routerData['${band}_bytes_sent'],
        'receivedBytes': routerData['${band}_bytes_received'],
      };
    }
    return counters;
  }

  String _interfaceCountersText() {
    final counters = _interfaceCountersForExport();
    if (counters.isEmpty) return 'N/A\n';
    final buffer = StringBuffer();
    counters.forEach((name, value) {
      final item = Map<String, dynamic>.from(value as Map);
      buffer.writeln('$name:');
      if (item['ssid1'] != null && item['ssid1'].toString().isNotEmpty) {
        buffer.writeln('  SSID: ${item['ssid1']}');
      }
      if (item['channel'] != null && item['channel'].toString().isNotEmpty) {
        buffer.writeln('  Canal: ${item['channel']}');
      }
      if (item['status'] != null) {
        buffer.writeln('  Estado: ${item['status']} ${item['speed'] ?? ''}'.trimRight());
      }
      buffer.writeln('  Enviado: ${_formatBytes(_parseInt(item['sentBytes']))}');
      buffer.writeln('  Recibido: ${_formatBytes(_parseInt(item['receivedBytes']))}');
    });
    return buffer.toString();
  }

  String _trafficCounterSourceLabel() {
    return routerData['firmwareMode'] == 'NEW'
        ? 'Suma de contadores LAN + WiFi 2.4 GHz + WiFi 5 GHz; no es WAN/GPON nativo.'
        : 'Contadores GPON nativos ponBytesSent/ponBytesReceived.';
  }

  int _displayTrafficSentBytes() {
    return routerData['firmwareMode'] == 'NEW'
        ? _parseInt(routerData['interfaceBytesSentTotal'])
        : _parseInt(routerData['ponBytesSent']);
  }

  int _displayTrafficReceivedBytes() {
    return routerData['firmwareMode'] == 'NEW'
        ? _parseInt(routerData['interfaceBytesReceivedTotal'])
        : _parseInt(routerData['ponBytesReceived']);
  }

  void _showSettingsDialog() {
    final ipController = TextEditingController(text: routerIp);
    final userController = TextEditingController(text: username);
    final passController = TextEditingController(text: password);
    final apiPathController = TextEditingController(text: apiPath);
    final ajaxMethodController = TextEditingController(text: ajaxMethod);
    bool obscurePassword = true;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text("Configurar Router"),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: ipController,
                  decoration: const InputDecoration(
                    labelText: "IP del Router",
                    hintText: "192.168.1.1",
                    prefixIcon: Icon(Icons.router),
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: userController,
                  decoration: const InputDecoration(
                    labelText: "Usuario",
                    hintText: "user",
                    prefixIcon: Icon(Icons.person),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: passController,
                  decoration: InputDecoration(
                    labelText: "Password",
                    hintText: "user1234",
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(obscurePassword ? Icons.visibility : Icons.visibility_off),
                      onPressed: () {
                        setDialogState(() {
                          obscurePassword = !obscurePassword;
                        });
                      },
                    ),
                  ),
                  obscureText: obscurePassword,
                ),
                const SizedBox(height: 8),
                Text(
                  "Credenciales se guardan localmente",
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade400),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: apiPathController,
                  decoration: const InputDecoration(
                    labelText: "Ruta API",
                    hintText: "/cgi-bin/ajax",
                    prefixIcon: Icon(Icons.api),
                  ),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: ajaxMethodController,
                  decoration: const InputDecoration(
                    labelText: "Metodo AJAX",
                    hintText: "get_base_info",
                    prefixIcon: Icon(Icons.integration_instructions),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  "Para otros routers se requiere una API que entregue campos equivalentes",
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade400),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text("Cancelar"),
            ),
            ElevatedButton.icon(
              icon: const Icon(Icons.save),
              label: const Text("Guardar"),
              onPressed: () {
                setState(() {
                  routerIp = ipController.text;
                  username = userController.text;
                  password = passController.text;
                  apiPath = apiPathController.text;
                  ajaxMethod = ajaxMethodController.text;
                  trafficSamples.clear();
                  currentRate = null;
                  minRate = null;
                  maxRate = null;
                });
                _saveSettings(routerIp, username, password, apiPath, ajaxMethod);
                Navigator.pop(context);
                _fetchData();
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Monitor GPON"),
        backgroundColor: const Color(0xFF1565C0),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchData,
            tooltip: "Actualizar",
          ),
          IconButton(
            icon: const Icon(Icons.ios_share),
            onPressed: _exportReport,
            tooltip: "Exportar reporte",
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showSettingsDialog,
            tooltip: "Configurar",
          ),
        ],
      ),
      body: Stack(
        children: [
          RefreshIndicator(
            onRefresh: _fetchData,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
              if (errorMessage.isNotEmpty)
                Card(
                  color: Colors.red.shade900,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        const Icon(Icons.error_outline, size: 48, color: Colors.white),
                        const SizedBox(height: 8),
                        Text(errorMessage, textAlign: TextAlign.center),
                        const SizedBox(height: 8),
                        Text(
                          "IP: $routerIp | User: $username",
                          style: const TextStyle(fontSize: 12, color: Colors.white70),
                        ),
                        const SizedBox(height: 8),
                        TextButton.icon(
                          icon: const Icon(Icons.settings, color: Colors.white),
                          label: const Text("Configurar", style: TextStyle(color: Colors.white)),
                          onPressed: _showSettingsDialog,
                        ),
                      ],
                    ),
                  ),
                ),

              if (isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(32),
                    child: CircularProgressIndicator(),
                  ),
                ),

              if (routerData.isNotEmpty && errorMessage.isEmpty) ...[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              "Router: $routerIp",
                              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                            ),
                            if (lastUpdate != null)
                              Text(
                                "Actualizado: ${DateFormat('HH:mm:ss').format(lastUpdate!)}",
                                style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                              ),
                          ],
                        ),
                        const Icon(Icons.router, size: 32),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 16),

                _buildSection("UPTIME", Icons.timer, [
                  _buildInfoRow("Activo desde hace", _formatUptime(_parseInt(routerData['uptime']))),
                  _buildInfoRow("Total segundos", _formatNumber(_parseInt(routerData['uptime']))),
                ]),

                const SizedBox(height: 16),

                _buildSection("TRAFICO GPON", Icons.swap_vert, [
                  if (routerData['firmwareMode'] == 'NEW')
                    _buildInfoRow(
                      "Estado RP3084+",
                      "Mostrando suma LAN/WiFi",
                      color: Colors.amber,
                    ),
                  _buildInfoRow(
                    "Enviado",
                    _formatBytes(_displayTrafficSentBytes()),
                    color: Colors.orange,
                  ),
                  _buildInfoRow(
                    "Recibido",
                    _formatBytes(_displayTrafficReceivedBytes()),
                    color: Colors.green,
                  ),
                  _buildInfoRow(
                    "Total",
                    _formatBytes(
                      _displayTrafficSentBytes() + _displayTrafficReceivedBytes(),
                    ),
                    color: Colors.blue,
                  ),
                ]),

                if (_hasInterfaceCounters()) ...[
                  const SizedBox(height: 16),
                  _buildSection("CONTADORES LAN / WIFI", Icons.device_hub, _buildInterfaceCounterRows()),
                ],

                const SizedBox(height: 16),

                _buildSection("ANCHO DE BANDA EXPERIMENTAL", Icons.speed, [
                  _buildInfoRow(
                    "Fuente",
                    routerData['firmwareMode'] == 'NEW' ? "Suma LAN/WiFi del router" : "Contadores GPON del router",
                  ),
                  _buildInfoRow("Modo", "Calculado desde dos lecturas; no es dato nativo"),
                  _buildInfoRow(
                    "Actual total",
                    currentRate == null ? 'Esperando 2 lecturas' : _formatMbps(currentRate!.totalMbps),
                    color: Colors.lightBlueAccent,
                  ),
                  _buildInfoRow(
                    "Actual subida",
                    currentRate == null ? 'N/A' : _formatMbps(currentRate!.sentMbps),
                    color: Colors.orange,
                  ),
                  _buildInfoRow(
                    "Actual bajada",
                    currentRate == null ? 'N/A' : _formatMbps(currentRate!.receivedMbps),
                    color: Colors.green,
                  ),
                  _buildInfoRow(
                    "Minimo sesion",
                    minRate == null ? 'N/A' : _formatMbps(minRate!.totalMbps),
                  ),
                  _buildInfoRow(
                    "Maximo sesion",
                    maxRate == null ? 'N/A' : _formatMbps(maxRate!.totalMbps),
                    color: Colors.amber,
                  ),
                  _buildInfoRow("Muestras", trafficSamples.length.toString()),
                ]),

                const SizedBox(height: 16),

                _buildSection("SISTEMA", Icons.memory, [
                  _buildInfoRow("CPU", "${routerData['cpu_usage'] ?? 'N/A'}%"),
                  _buildInfoRow("RAM", _formatRam(
                    _parseInt(routerData['mem_free']),
                    _parseInt(routerData['mem_total']),
                  )),
                  _buildInfoRow("Modelo", routerData['ModelName'] ?? 'N/A'),
                  _buildInfoRow("Firmware", routerData['SoftwareVersion'] ?? 'N/A'),
                ]),

                const SizedBox(height: 16),

                _buildSection("SENAL OPTICA", Icons.wifi_tethering, [
                  _buildInfoRow("Tx Power", "${routerData['txpower'] ?? 'N/A'} dBm", color: Colors.green),
                  _buildInfoRow("Rx Power", "${routerData['rxpower'] ?? 'N/A'} dBm", color: Colors.amber),
                  _buildInfoRow("Temperatura", "${routerData['transceivertemperature'] ?? 'N/A'} C"),
                  _buildInfoRow("Voltaje", "${routerData['supplyvottage'] ?? 'N/A'} V"),
                  _buildInfoRow("Corriente", "${routerData['biascurrent'] ?? 'N/A'} mA"),
                ]),

                const SizedBox(height: 16),

                _buildSection("WAN", Icons.public, [
                  _buildInfoRow("Tipo", routerData['WANAccessType'] ?? 'N/A'),
                  _buildInfoRow("PON Status", routerData['pon_reg_state'] ?? 'N/A'),
                  _buildInfoRow("TR-069", routerData['tr069ipstatus'] == '1' ? 'Activo' : 'Inactivo'),
                ]),

                const SizedBox(height: 32),

                FilledButton.icon(
                  icon: const Icon(Icons.ios_share),
                  label: const Text("Exportar logs e informacion"),
                  onPressed: _exportReport,
                ),

                const SizedBox(height: 16),

                Text(
                  "Huawei/FiberHome HG6145F - API configurable para routers compatibles",
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey.shade600, fontSize: 12),
                ),
              ],
                ],
              ),
            ),
          ),
          if (_routerWebView != null)
            Positioned(
              left: 0,
              bottom: 0,
              width: 1,
              height: 1,
              child: Opacity(
                opacity: 0.01,
                child: WebViewWidget(controller: _routerWebView!),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildSection(String title, IconData icon, List<Widget> children) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, size: 20, color: const Color(0xFF1565C0)),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const Divider(),
            ...children,
          ],
        ),
      ),
    );
  }

  bool _hasInterfaceCounters() {
    if (routerData['wifi24_bytes_sent'] != null || routerData['wifi5_bytes_sent'] != null) return true;
    for (var i = 1; i <= 9; i++) {
      if (routerData['lan${i}_status'] != null && routerData['lan${i}_status'].toString().isNotEmpty) {
        return true;
      }
    }
    return false;
  }

  List<Widget> _buildInterfaceCounterRows() {
    final rows = <Widget>[];
    for (var i = 1; i <= 9; i++) {
      final status = routerData['lan${i}_status']?.toString() ?? '';
      if (status.isEmpty) continue;
      final sent = _parseInt(routerData['lan${i}_bytes_sent']);
      final received = _parseInt(routerData['lan${i}_bytes_received']);
      if (status != 'Up' && sent == 0 && received == 0) continue;
      final speed = routerData['lan${i}_speed']?.toString() ?? '';
      rows.add(_buildInfoRow('LAN $i', '$status ${speed.isEmpty ? '' : '($speed)'}'.trim()));
      rows.add(_buildInfoRow('  Enviado', _formatBytes(sent), color: Colors.orange));
      rows.add(_buildInfoRow('  Recibido', _formatBytes(received), color: Colors.green));
    }

    rows.addAll(_buildWifiCounterRows('wifi24', 'WiFi 2.4 GHz'));
    rows.addAll(_buildWifiCounterRows('wifi5', 'WiFi 5 GHz'));
    return rows.isEmpty ? [_buildInfoRow('Contadores', 'N/A')] : rows;
  }

  List<Widget> _buildWifiCounterRows(String prefix, String label) {
    final sent = _parseInt(routerData['${prefix}_bytes_sent']);
    final received = _parseInt(routerData['${prefix}_bytes_received']);
    final channel = routerData['${prefix}_channel']?.toString() ?? '';
    final ssid = routerData['${prefix}_ssid_1']?.toString() ?? '';
    if (sent == 0 && received == 0 && channel.isEmpty && ssid.isEmpty) return [];
    return [
      _buildInfoRow(label, ssid.isEmpty ? 'Canal $channel' : '$ssid${channel.isEmpty ? '' : ' / Canal $channel'}'),
      _buildInfoRow('  Enviado', _formatBytes(sent), color: Colors.orange),
      _buildInfoRow('  Recibido', _formatBytes(received), color: Colors.green),
    ];
  }

  Widget _buildInfoRow(String label, String value, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Text(label, style: TextStyle(color: Colors.grey.shade300)),
          ),
          const SizedBox(width: 12),
          Flexible(
            child: Text(
              value,
              textAlign: TextAlign.right,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                color: color ?? Colors.white,
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatRam(int used, int total) {
    if (total == 0) return 'N/A';
    final usedMb = (total - used) / 1024;
    final totalMb = total / 1024;
    return '${usedMb.toStringAsFixed(0)} MB / ${totalMb.toStringAsFixed(0)} MB';
  }
}

class TrafficSample {
  TrafficSample({
    required this.timestamp,
    required this.sentBytes,
    required this.receivedBytes,
    this.rate,
  });

  final DateTime timestamp;
  final int sentBytes;
  final int receivedBytes;
  final TrafficRate? rate;

  Map<String, dynamic> toJson() => {
        'timestamp': timestamp.toIso8601String(),
        'sentBytes': sentBytes,
        'receivedBytes': receivedBytes,
        'rate': rate?.toJson(),
      };
}

class _RouterFetchResult {
  const _RouterFetchResult._({this.data, this.error});

  factory _RouterFetchResult.data(Map<String, dynamic> data) {
    return _RouterFetchResult._(data: data);
  }

  factory _RouterFetchResult.error(String error) {
    return _RouterFetchResult._(error: error);
  }

  final Map<String, dynamic>? data;
  final String? error;
}

class _TrafficBytes {
  const _TrafficBytes({required this.sent, required this.received});

  final int sent;
  final int received;
}

class TrafficRate {
  TrafficRate({
    required this.timestamp,
    required this.sentMbps,
    required this.receivedMbps,
    required this.intervalSeconds,
  });

  final DateTime timestamp;
  final double sentMbps;
  final double receivedMbps;
  final double intervalSeconds;

  double get totalMbps => sentMbps + receivedMbps;

  Map<String, dynamic> toJson() => {
        'timestamp': timestamp.toIso8601String(),
        'sentMbps': sentMbps,
        'receivedMbps': receivedMbps,
        'totalMbps': totalMbps,
        'intervalSeconds': intervalSeconds,
      };
}
