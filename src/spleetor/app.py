import os
import subprocess
from flask import Flask, request, jsonify
import base64
from zipfile import ZipFile
app = Flask(__name__)

@app.route('/separate-audio', methods=['POST'])
def separate_audio():
    # Get the uploaded audio file
    file = request.files['audio']

    # Save the uploaded file to disk
    file.save('audio_file.wav')

    # Call Spleeter using subprocess
    cmd = ['spleeter', 'separate', '-p', 'spleeter:2stems', '-o', 'output', 'audio_file.wav']

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        # Handle the error here, e.g. by logging it and returning an error response
        return jsonify({'error': str(e)}), 500

    # Get the separated sources as WAV files
    sources = {}
    for stem in ['vocals', 'accompaniment']:
        filename = f'output/audio_file/{stem}.wav'
        with open(filename, 'rb') as f:
            sources[stem] = base64.b64encode(f.read()).decode('utf-8')

        # Remove the temporary files
        # os.remove(filename)

    # Return the separated sources as a JSON object
    return jsonify(sources)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)