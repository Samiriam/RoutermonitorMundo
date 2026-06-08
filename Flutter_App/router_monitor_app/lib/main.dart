import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:intl/intl.dart';
import 'package:share_plus/share_plus.dart';

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
        _recordTrafficSample(data);
        setState(() {
          routerData = data;
          lastUpdate = DateTime.now();
          isLoading = false;
        });
      } else {
        setState(() {
          errorMessage = "Error: ${response.statusCode}";
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        errorMessage = "No se pudo conectar al router\nVerifica la IP y credenciales";
        isLoading = false;
      });
    }
  }

  void _recordTrafficSample(Map<String, dynamic> data) {
    final now = DateTime.now();
    final sent = _parseInt(data['ponBytesSent']);
    final received = _parseInt(data['ponBytesReceived']);
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
        'source': 'ponBytesSent/ponBytesReceived',
        'note': 'Calculado desde contadores del router entre lecturas; no mide trafico del celular.',
        'currentMbps': currentRate?.toJson(),
        'minTotalMbps': minRate?.toJson(),
        'maxTotalMbps': maxRate?.toJson(),
      },
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
      ..writeln('Enviado: ${_formatBytes(_parseInt(routerData['ponBytesSent']))}')
      ..writeln('Recibido: ${_formatBytes(_parseInt(routerData['ponBytesReceived']))}')
      ..writeln('')
      ..writeln('Ancho de banda observado desde el router')
      ..writeln('Actual: ${currentRate == null ? 'N/A' : _formatMbps(currentRate!.totalMbps)}')
      ..writeln('Minimo sesion: ${minRate == null ? 'N/A' : _formatMbps(minRate!.totalMbps)}')
      ..writeln('Maximo sesion: ${maxRate == null ? 'N/A' : _formatMbps(maxRate!.totalMbps)}')
      ..writeln('')
      ..writeln('JSON')
      ..writeln(const JsonEncoder.withIndent('  ').convert(report));

    await Share.share(buffer.toString(), subject: 'Reporte Monitor GPON $routerIp');
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
      body: RefreshIndicator(
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
                  _buildInfoRow(
                    "Enviado",
                    _formatBytes(_parseInt(routerData['ponBytesSent'])),
                    color: Colors.orange,
                  ),
                  _buildInfoRow(
                    "Recibido",
                    _formatBytes(_parseInt(routerData['ponBytesReceived'])),
                    color: Colors.green,
                  ),
                  _buildInfoRow(
                    "Total",
                    _formatBytes(
                      _parseInt(routerData['ponBytesSent']) +
                      _parseInt(routerData['ponBytesReceived']),
                    ),
                    color: Colors.blue,
                  ),
                ]),

                const SizedBox(height: 16),

                _buildSection("ANCHO DE BANDA EXPERIMENTAL", Icons.speed, [
                  _buildInfoRow("Fuente", "Contadores GPON del router"),
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
