import 'package:flutter/material.dart';
import '../../core/config/api_config.dart';
import '../../data/services/lists_api_service.dart';

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  final _controller = TextEditingController();
  final _apiService = ListsApiService();

  bool _loading = true;
  double _addThreshold = 0.7;
  double _ignoreThreshold = 0.35;
  bool _savingConfidence = false;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _loadAll() async {
    final url = await ApiConfig.getBaseUrl();
    setState(() {
      _controller.text = url;
    });

    try {
      final settings = await _apiService.fetchConfidenceSettings();
      setState(() {
        _addThreshold = settings['add_threshold'] ?? 0.7;
        _ignoreThreshold = settings['ignore_threshold'] ?? 0.35;
      });
    } catch (_) {
      // keep defaults if backend unreachable
    }

    setState(() {
      _loading = false;
    });
  }

  Future<void> _saveUrl() async {
    final url = _controller.text.trim();
    if (url.isEmpty) return;
    await ApiConfig.setBaseUrl(url);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('URL sauvegardée — relance l\'app pour appliquer')),
      );
    }
  }

  Future<void> _saveConfidence() async {
    setState(() => _savingConfidence = true);
    final ok = await _apiService.updateConfidenceSettings(
      addThreshold: _addThreshold,
      ignoreThreshold: _ignoreThreshold,
    );
    setState(() => _savingConfidence = false);

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(ok
              ? 'Seuils de confiance enregistrés'
              : 'Erreur lors de la sauvegarde'),
        ),
      );
    }
  }

  String _pct(double v) => '${(v * 100).round()} %';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Paramètres')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // --- URL du backend ---
                  Text(
                    'URL du backend',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _controller,
                    keyboardType: TextInputType.url,
                    autocorrect: false,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                      hintText: 'http://192.168.1.X:8000',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _saveUrl,
                      child: const Text('Sauvegarder l\'URL'),
                    ),
                  ),

                  const SizedBox(height: 32),
                  const Divider(),
                  const SizedBox(height: 16),

                  // --- Seuils de confiance ---
                  Text(
                    'Seuils de confiance',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Calibrez à partir de quel niveau de confiance une action est '
                    'ajoutée automatiquement ou ignorée.',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 20),

                  // Ajouter automatiquement
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Flexible(
                        child: Text('Ajouter automatiquement (≥)'),
                      ),
                      Text(
                        _pct(_addThreshold),
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  Slider(
                    value: _addThreshold,
                    min: 0.0,
                    max: 1.0,
                    divisions: 20,
                    label: _pct(_addThreshold),
                    onChanged: (v) {
                      if (v > _ignoreThreshold) {
                        setState(() => _addThreshold = v);
                      }
                    },
                  ),

                  const SizedBox(height: 8),

                  // Ignorer
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Flexible(
                        child: Text('Ignorer (≤)'),
                      ),
                      Text(
                        _pct(_ignoreThreshold),
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                    ],
                  ),
                  Slider(
                    value: _ignoreThreshold,
                    min: 0.0,
                    max: 1.0,
                    divisions: 20,
                    label: _pct(_ignoreThreshold),
                    onChanged: (v) {
                      if (v < _addThreshold) {
                        setState(() => _ignoreThreshold = v);
                      }
                    },
                  ),

                  const SizedBox(height: 4),
                  Text(
                    'Entre les deux seuils → demande de confirmation.',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: Theme.of(context).colorScheme.secondary,
                        ),
                  ),

                  const SizedBox(height: 20),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton(
                      onPressed: _savingConfidence ? null : _saveConfidence,
                      child: _savingConfidence
                          ? const SizedBox(
                              height: 18,
                              width: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Enregistrer les seuils'),
                    ),
                  ),
                ],
              ),
            ),
    );
  }
}
