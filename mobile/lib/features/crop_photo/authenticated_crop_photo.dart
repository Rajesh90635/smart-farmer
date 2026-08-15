import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show Uint8List;
import 'package:provider/provider.dart';

import 'crop_photo_repository.dart';

class AuthenticatedCropPhoto extends StatefulWidget {
  final String photoId;
  final bool thumbnail;
  final double? width;
  final double? height;
  final BoxFit fit;

  const AuthenticatedCropPhoto({
    super.key,
    required this.photoId,
    this.thumbnail = false,
    this.width,
    this.height,
    this.fit = BoxFit.cover,
  });

  @override
  State<AuthenticatedCropPhoto> createState() => _AuthenticatedCropPhotoState();
}

class _AuthenticatedCropPhotoState extends State<AuthenticatedCropPhoto> {
  late Future<Uint8List> _future;

  @override
  void initState() {
    super.initState();
    _future = context.read<CropPhotoRepository>().fetchPhotoBytes(widget.photoId, thumbnail: widget.thumbnail);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<Uint8List>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return SizedBox(
            width: widget.width,
            height: widget.height,
            child: const Center(child: CircularProgressIndicator(strokeWidth: 2)),
          );
        }
        if (snapshot.hasError || !snapshot.hasData) {
          return SizedBox(
            width: widget.width,
            height: widget.height,
            child: const Icon(Icons.broken_image, color: Colors.grey),
          );
        }
        return Image.memory(snapshot.data!, width: widget.width, height: widget.height, fit: widget.fit);
      },
    );
  }
}
