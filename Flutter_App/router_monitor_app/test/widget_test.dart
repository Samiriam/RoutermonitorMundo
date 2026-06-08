import 'package:flutter_test/flutter_test.dart';

import 'package:router_monitor/main.dart';

void main() {
  testWidgets('loads monitor app shell', (WidgetTester tester) async {
    await tester.pumpWidget(const RouterMonitorApp());

    expect(find.text('Monitor GPON'), findsOneWidget);
  });
}
