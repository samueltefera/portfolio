import os
import subprocess
import tempfile
from zipfile import ZipFile
import json
import pika
from pymongo import MongoClient
from gridfs import GridFS
from bson.objectid import ObjectId
# Connect to MongoDB and GridFS
client = MongoClient("host.minikube.internal", 27017)
db_videos = client['videos']
db_mp3s = client['mp3s']
fs_videos = GridFS(db_videos)
fs_mp3s = GridFS(db_mp3s)



def separate_audio(ch, method, properties, body):
    # Get the message payload
    payload = json.loads(body)

    # Get the video_fid from the payload
    video_fid = payload['video_fid']

    # Get the file from MongoDB using GridFS
    with fs_videos.get(ObjectId(video_fid)) as file:
        # Get the separated sources as WAV files
        with tempfile.TemporaryDirectory() as tmpdir:
            filename = os.path.join(tmpdir, f"{video_fid}.wav")
            with open(filename, 'wb') as f:
                f.write(file.read())

            # Call Spleeter to separate the audio
            cmd = ['spleeter', 'separate', '-p', 'spleeter:2stems', '-o', tmpdir, filename]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as err:
                # Handle the error here, e.g. by logging it and returning an error response
                print(f'Error: {err}')
                return

            filename_without_ext, ext = os.path.splitext(filename)
            # Compress the separated files into a ZIP archive

            zip_path = os.path.join(tmpdir, 'audio.zip')
            with ZipFile(zip_path, 'w') as zip_file:
                for stem in ['vocals', 'accompaniment']:
                    stem_path = os.path.join(tmpdir, filename_without_ext, f'{stem}.wav')
                    zip_file.write(stem_path, f'{stem}.wav')

            # Save the ZIP archive to MongoDB using GridFS
            with open(zip_path, 'rb') as zip_file:
                fid = fs_mp3s.put(zip_file)


            print(f'Audio separated for video_fid: {video_fid}')
            payload["mp3_fid"] = str(fid)
        
            try:
                ch.basic_publish(
                    exchange="",
                    routing_key=os.environ.get("MP3_QUEUE"),
                    body=json.dumps(payload),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                    ),
                )
            except Exception as err:
                return err

    # Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)


def consume_queue():
    # Connect to the queue and start consuming messages
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=separate_audio
    )

    print("Waiting for messages. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    consume_queue()
