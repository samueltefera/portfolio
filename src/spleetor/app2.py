import os
import subprocess
from flask import Flask, request, jsonify
import tempfile
import base64
from zipfile import ZipFile
from pymongo import MongoClient
from gridfs import GridFS

app = Flask(__name__)

client = MongoClient()
db = client['audio_db']
fs = GridFS(db)


@app.route('/separate-audio', methods=['POST'])
def separate_audio():
    file = request.files['file']
    if not file:
        return 'No file uploaded', 400

    # Get the separated sources as WAV files
    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, file.filename)
        file.save(filename)

        # Call Spleeter to separate the audio
        cmd = ['spleeter', 'separate', '-p', 'spleeter:2stems', '-o', tmpdir, filename]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as err:
        # Handle the error here, e.g. by logging it and returning an error response
            return ({'error': str(err)}), 500
        
        filename_without_ext, ext = os.path.splitext(filename)
        # Compress the separated files into a ZIP archive
        
        zip_path = os.path.join(tmpdir, 'audio.zip')
        with ZipFile(zip_path, 'w') as zip_file:
            for stem in ['vocals', 'accompaniment']:
                stem_path = os.path.join(tmpdir, filename_without_ext, f'{stem}.wav')
                zip_file.write(stem_path, f'{stem}.wav')

        # Save the ZIP archive to MongoDB using GridFS
        with open(zip_path, 'rb') as zip_file:
            fs.put(zip_file, filename=file.filename, content_type='application/zip')

        # Return a JSON response indicating success
        return jsonify({'message': 'Audio separated successfully'}), 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)