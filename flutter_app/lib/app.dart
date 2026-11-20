import 'package:flutter/material.dart';

import 'screens/document_chat_page.dart';

class Phase5RagApp extends StatelessWidget {
  const Phase5RagApp({
    super.key,
  });

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Document AI',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF625BF6),
        ),
        scaffoldBackgroundColor:
            const Color(0xFFF7F7FA),
      ),
      home: const DocumentChatPage(),
    );
  }
}
