# amps/api.py

from flask import Blueprint, jsonify, request, current_app
from amps import ffmpeg_utils

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/streams', methods=['GET'])
def get_streams():
    """Returns the list of all configured streams."""
    stream_map = current_app.config.get('stream_map', {})
    return jsonify(list(stream_map.values()))

@api_bp.route('/streams/<int:stream_id>', methods=['GET'])
def get_stream(stream_id):
    """Returns a single stream by its ID."""
    stream_map = current_app.config.get('stream_map', {})
    if stream_id in stream_map:
        return jsonify(stream_map[stream_id])
    return jsonify({'error': 'Stream not found'}), 404

@api_bp.route('/streams', methods=['POST'])
def add_stream():
    """Adds a new stream to the in-memory configuration."""
    if not request.json or not all(k in request.json for k in ['name', 'source', 'ffmpeg_profile']):
        return jsonify({'error': 'Missing required fields: name, source, ffmpeg_profile'}), 400

    stream_map = current_app.config.get('stream_map', {})
    new_id = max(stream_map.keys()) + 1 if stream_map else 1

    new_stream = {
        'id': new_id,
        'name': request.json['name'],
        'source': request.json['source'],
        'ffmpeg_profile': request.json['ffmpeg_profile']
    }

    if new_stream['ffmpeg_profile'] not in current_app.config['ffmpeg_profiles']:
         return jsonify({'error': f"ffmpeg_profile '{new_stream['ffmpeg_profile']}' not found"}), 400

    stream_map[new_id] = new_stream
    return jsonify(new_stream), 201

@api_bp.route('/streams/<int:stream_id>', methods=['PUT'])
def update_stream(stream_id):
    """Updates an existing stream."""
    stream_map = current_app.config.get('stream_map', {})
    if stream_id not in stream_map:
        return jsonify({'error': 'Stream not found'}), 404

    if not request.json:
        return jsonify({'error': 'Invalid JSON body'}), 400

    update_data = request.json
    if 'ffmpeg_profile' in update_data and update_data['ffmpeg_profile'] not in current_app.config['ffmpeg_profiles']:
        return jsonify({'error': f"ffmpeg_profile '{update_data['ffmpeg_profile']}' not found"}), 400

    # Stop the old process if source or profile changes
    if 'source' in update_data or 'ffmpeg_profile' in update_data:
        ffmpeg_utils.stop_stream_process(stream_id)

    stream_map[stream_id].update(update_data)
    return jsonify(stream_map[stream_id])

@api_bp.route('/streams/<int:stream_id>', methods=['DELETE'])
def delete_stream(stream_id):
    """Deletes a stream and stops its FFmpeg process."""
    stream_map = current_app.config.get('stream_map', {})
    if stream_id in stream_map:
        ffmpeg_utils.stop_stream_process(stream_id)
        deleted_stream = stream_map.pop(stream_id)
        return jsonify({'message': 'Stream deleted successfully', 'stream': deleted_stream})
    return jsonify({'error': 'Stream not found'}), 404
