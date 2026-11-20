import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../models/chat_message.dart';
import '../models/document_info.dart';
import '../services/rag_api_service.dart';
import '../widgets/chat_bubble.dart';

class DocumentChatPage extends StatefulWidget {
  const DocumentChatPage({
    super.key,
  });

  @override
  State<DocumentChatPage> createState() =>
      _DocumentChatPageState();
}

class _DocumentChatPageState extends State<DocumentChatPage> {
  final RagApiService _api = const RagApiService();

  final TextEditingController _messageController =
      TextEditingController();

  final ScrollController _scrollController =
      ScrollController();

  final List<ChatMessage> _messages = [];

  DocumentInfo? _document;

  bool _loadingStatus = true;
  bool _uploading = false;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _loadStatus();
  }

  Future<void> _loadStatus() async {
    try {
      final document = await _api.getStatus();

      if (!mounted) {
        return;
      }

      setState(() {
        _document = document;
      });
    } catch (_) {
      // Backend may not be running yet.
    } finally {
      if (mounted) {
        setState(() {
          _loadingStatus = false;
        });
      }
    }
  }

  void _snack(
    String message, {
    bool error = false,
  }) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        behavior: SnackBarBehavior.floating,
        backgroundColor:
            error ? Colors.red.shade700 : null,
      ),
    );
  }

  Future<void> _upload() async {
    if (_uploading) {
      return;
    }

    final PlatformFile? file = await FilePicker.pickFile(
      type: FileType.custom,
      allowedExtensions: const ['pdf'],
    );

    if (file == null) {
      return;
    }

    setState(() {
      _uploading = true;
    });

    try {
      final document = await _api.uploadPdf(file);

      if (!mounted) {
        return;
      }

      setState(() {
        _document = document;
        _messages.clear();
      });

      _snack(
        '${document.filename} indexed successfully.',
      );
    } catch (error) {
      _snack(
        error
            .toString()
            .replaceFirst(
              'Exception: ',
              '',
            ),
        error: true,
      );
    } finally {
      if (mounted) {
        setState(() {
          _uploading = false;
        });
      }
    }
  }

  Future<void> _send() async {
    if (_sending || _document == null) {
      return;
    }

    final question =
        _messageController.text.trim();

    if (question.isEmpty) {
      return;
    }

    final history = List<ChatMessage>.from(
      _messages,
    );

    setState(() {
      _messages.add(
        ChatMessage(
          role: 'user',
          content: question,
        ),
      );

      _messageController.clear();
      _sending = true;
    });

    _scrollBottom();

    try {
      final result = await _api.ask(
        question: question,
        history: history,
      );

      if (!mounted) {
        return;
      }

      setState(() {
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content: result.answer,
            sources: result.sources,
          ),
        );
      });

      _scrollBottom();
    } catch (error) {
      if (!mounted) {
        return;
      }

      setState(() {
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content:
                'Request failed: '
                '${error.toString().replaceFirst(
                      'Exception: ',
                      '',
                    )}',
          ),
        );
      });

      _scrollBottom();
    } finally {
      if (mounted) {
        setState(() {
          _sending = false;
        });
      }
    }
  }

  void _scrollBottom() {
    WidgetsBinding.instance.addPostFrameCallback(
      (_) {
        if (!_scrollController.hasClients) {
          return;
        }

        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(
            milliseconds: 250,
          ),
          curve: Curves.easeOut,
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (
            context,
            constraints,
          ) {
            final desktop =
                constraints.maxWidth >= 900;

            if (desktop) {
              return Row(
                children: [
                  SizedBox(
                    width: 310,
                    child: _sidebar(),
                  ),
                  const VerticalDivider(
                    width: 1,
                  ),
                  Expanded(
                    child: _chatArea(),
                  ),
                ],
              );
            }

            return Column(
              children: [
                _mobileHeader(),
                const Divider(
                  height: 1,
                ),
                Expanded(
                  child: _chatArea(),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _sidebar() {
    return Container(
      color: Colors.white,
      padding: const EdgeInsets.all(22),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              CircleAvatar(
                backgroundColor:
                    Color(0xFFEDEBFF),
                child: Icon(
                  Icons.auto_awesome,
                  color: Color(0xFF625BF6),
                ),
              ),
              SizedBox(width: 10),
              Column(
                crossAxisAlignment:
                    CrossAxisAlignment.start,
                children: [
                  Text(
                    'Document AI',
                    style: TextStyle(
                      fontWeight:
                          FontWeight.w700,
                      fontSize: 17,
                    ),
                  ),
                  Text(
                    'Phase 5 RAG',
                    style: TextStyle(
                      color: Color(0xFF9CA3AF),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 30),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed:
                  _uploading ? null : _upload,
              icon: const Icon(
                Icons.upload_file,
              ),
              label: Text(
                _uploading
                    ? 'Indexing...'
                    : _document == null
                        ? 'Upload PDF'
                        : 'Replace PDF',
              ),
            ),
          ),
          const SizedBox(height: 18),
          if (_loadingStatus)
            const Center(
              child:
                  CircularProgressIndicator(),
            )
          else if (_document != null)
            _documentCard(),
          const Spacer(),
          const Text(
            'Hybrid retrieval',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 5),
          const Text(
            'Semantic similarity + exact keyword matching. '
            'Sources preserve PDF page and chunk metadata.',
            style: TextStyle(
              fontSize: 11,
              height: 1.45,
              color: Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget _documentCard() {
    final document = _document!;

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7F7FA),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Column(
        crossAxisAlignment:
            CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.picture_as_pdf,
                color: Colors.red,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  document.filename,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontWeight:
                        FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            '${document.chunksCreated} chunks · '
            '${document.vectorDimension}D',
            style: const TextStyle(
              fontSize: 11,
              color: Color(0xFF6B7280),
            ),
          ),
        ],
      ),
    );
  }

  Widget _mobileHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(
        horizontal: 14,
        vertical: 10,
      ),
      child: Row(
        children: [
          const Icon(
            Icons.auto_awesome,
            color: Color(0xFF625BF6),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _document?.filename ??
                  'Document AI',
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight:
                    FontWeight.w700,
              ),
            ),
          ),
          TextButton.icon(
            onPressed:
                _uploading ? null : _upload,
            icon: const Icon(
              Icons.upload_file,
            ),
            label: const Text('PDF'),
          ),
        ],
      ),
    );
  }

  Widget _chatArea() {
    return Column(
      children: [
        Container(
          color: Colors.white,
          padding: const EdgeInsets.symmetric(
            horizontal: 22,
            vertical: 16,
          ),
          child: Row(
            children: [
              const Expanded(
                child: Column(
                  crossAxisAlignment:
                      CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Chat with your document',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight:
                            FontWeight.w700,
                      ),
                    ),
                    Text(
                      'Answers are grounded in retrieved PDF chunks.',
                      style: TextStyle(
                        fontSize: 11,
                        color:
                            Color(0xFF6B7280),
                      ),
                    ),
                  ],
                ),
              ),
              if (_messages.isNotEmpty)
                IconButton(
                  tooltip: 'Clear chat',
                  onPressed: () {
                    setState(() {
                      _messages.clear();
                    });
                  },
                  icon: const Icon(
                    Icons.delete_outline,
                  ),
                ),
            ],
          ),
        ),
        const Divider(height: 1),
        Expanded(
          child: _messages.isEmpty
              ? _emptyState()
              : ListView.builder(
                  controller:
                      _scrollController,
                  padding:
                      const EdgeInsets.all(22),
                  itemCount:
                      _messages.length +
                          (_sending ? 1 : 0),
                  itemBuilder: (
                    context,
                    index,
                  ) {
                    if (_sending &&
                        index ==
                            _messages.length) {
                      return const Align(
                        alignment:
                            Alignment.centerLeft,
                        child: Padding(
                          padding:
                              EdgeInsets.only(
                            bottom: 18,
                          ),
                          child:
                              CircularProgressIndicator(),
                        ),
                      );
                    }

                    return ChatBubble(
                      message:
                          _messages[index],
                    );
                  },
                ),
        ),
        _composer(),
      ],
    );
  }

  Widget _emptyState() {
    return Center(
      child: ConstrainedBox(
        constraints:
            const BoxConstraints(
          maxWidth: 520,
        ),
        child: Padding(
          padding: const EdgeInsets.all(28),
          child: Column(
            mainAxisSize:
                MainAxisSize.min,
            children: [
              const Icon(
                Icons.description_outlined,
                size: 52,
                color: Color(0xFF625BF6),
              ),
              const SizedBox(height: 16),
              Text(
                _document == null
                    ? 'Upload a PDF to begin'
                    : 'Your document is ready',
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight:
                      FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                _document == null
                    ? 'The backend will extract, chunk, embed, and index the PDF.'
                    : 'Try “What is PaperLab?” or ask a semantic question in different wording.',
                textAlign:
                    TextAlign.center,
                style: const TextStyle(
                  color: Color(0xFF6B7280),
                  height: 1.5,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _composer() {
    final enabled =
        _document != null && !_sending;

    return Container(
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(
        18,
        12,
        18,
        18,
      ),
      child: Row(
        crossAxisAlignment:
            CrossAxisAlignment.end,
        children: [
          Expanded(
            child: TextField(
              controller:
                  _messageController,
              enabled:
                  _document != null,
              minLines: 1,
              maxLines: 5,
              textInputAction:
                  TextInputAction.send,
              onSubmitted: (_) {
                if (enabled) {
                  _send();
                }
              },
              decoration: InputDecoration(
                hintText:
                    _document == null
                        ? 'Upload a PDF first'
                        : 'Ask about the document...',
                filled: true,
                fillColor:
                    const Color(0xFFF8F8FB),
                border: OutlineInputBorder(
                  borderRadius:
                      BorderRadius.circular(14),
                  borderSide:
                      BorderSide.none,
                ),
              ),
            ),
          ),
          const SizedBox(width: 9),
          SizedBox(
            width: 50,
            height: 50,
            child: FilledButton(
              onPressed:
                  enabled ? _send : null,
              style: FilledButton.styleFrom(
                padding: EdgeInsets.zero,
                shape:
                    RoundedRectangleBorder(
                  borderRadius:
                      BorderRadius.circular(
                    14,
                  ),
                ),
              ),
              child: const Icon(
                Icons.arrow_upward,
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }
}
