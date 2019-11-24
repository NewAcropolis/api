import base64
from datetime import datetime
from io import BytesIO, StringIO
import os
import sys

from flask import current_app
from PIL import Image

from google.auth import compute_engine
from google.cloud import storage


class Storage(object):

    def __init__(self, bucket_name):
        if self.no_google_config():
            current_app.logger.info('Google credentials not available')
            return

        if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
            credentials = compute_engine.Credentials()
            self.storage_client = storage.Client(credentials=credentials, project=current_app.config['PROJECT'])
        else:
            self.storage_client = storage.Client()

        if bucket_name not in [b.name for b in self.storage_client.list_buckets()]:
            self.bucket = self.storage_client.create_bucket(bucket_name)
            current_app.logger.info('Bucket {} created'.format(self.bucket.name))
        else:
            self.bucket = self.storage_client.get_bucket(bucket_name)

    def no_google_config(self):
        return (
            not current_app.config.get('GOOGLE_APPLICATION_CREDENTIALS') and
            current_app.config['ENVIRONMENT'] == 'development')

    def upload_blob(self, source_file_name, destination_blob_name, set_public=True):
        if self.no_google_config():
            current_app.logger.info('No Google config, upload_blob: source: %s, destination: %s, public %s',
                                    source_file_name, destination_blob_name, set_public)
            return

        blob = self.bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        if set_public:
            blob.make_public()

        current_app.logger.info('File {} uploaded to {}'.format(
            source_file_name,
            destination_blob_name))

    def upload_blob_from_base64string(
        self, src_filename, destination_blob_name, base64data, content_type='image/png'
    ):
        if self.no_google_config():
            current_app.logger.info(
                'No Google config, upload_blob_from_base64string: fielname: '
                '%s, destination: %s, base64data: %s, content_type %s',
                src_filename, destination_blob_name, base64data, content_type)
            return

        blob = self.bucket.blob(destination_blob_name)

        binary = base64.b64decode(base64data)

        if 'image/' in content_type:
            self.generate_web_image(destination_blob_name, BytesIO(binary))

        blob.upload_from_string(binary, content_type=content_type)
        blob.make_public()

        binary_len = len(binary)
        current_app.logger.info('Uploaded {} file {} uploaded to {}'.format(
            sizeof_fmt(binary_len),
            src_filename,
            destination_blob_name))

    def blob_exists(self, prefix, delimiter=None):
        if self.no_google_config():
            current_app.logger.info(
                'No Google config, blob_exists: prefix: %s, delimiter: %s', prefix, delimiter)
            return

        blobs = self.bucket.list_blobs(prefix=prefix, delimiter=delimiter)
        return any(True for _ in blobs)

    def get_blob(self, image_filename):  # pragma: no cover
        blob = self.bucket.get_blob(image_filename)
        current_app.logger.info('Getting %s', image_filename)
        blob_data = blob.download_as_string()
        return blob_data

    def generate_web_images(self, year=None):
        if not year:
            year = datetime.now().strftime("%Y")

        print('Generate web images for {}/{}'.format(self.bucket.name, year))

        for blob in self.storage_client.list_blobs(self.bucket.name, prefix='{}/'.format(year), delimiter='/'):
            source_img = BytesIO()
            blob.download_to_file(source_img)
            print('Loaded {} bytes for {}'.format(sizeof_fmt(sys.getsizeof(source_img)), blob.name))
            self.generate_web_image(blob.name, source_img)

    def generate_web_image(self, filename, source_img):
        standard_img = BytesIO()
        thumbnail_img = BytesIO()

        img = Image.open(source_img)

        img.thumbnail(current_app.config.get('STANDARD_MAXSIZE'), Image.ANTIALIAS)
        img.save(standard_img, "PNG", optimize=True, quality=80)

        self.upload_web_image(
            'standard/{}'.format(filename),
            standard_img.getvalue()
        )

        img.thumbnail(current_app.config.get('THUMBNAIL_MAXSIZE'), Image.ANTIALIAS)
        img.save(thumbnail_img, "PNG", optimize=True, quality=80)

        self.upload_web_image(
            'thumbnail/{}'.format(filename),
            thumbnail_img.getvalue()
        )

    def upload_web_image(self, filename, binary, content_type='image/png'):
        blob = self.bucket.blob(filename)

        blob.upload_from_string(binary, content_type=content_type)
        blob.make_public()

        binary_len = len(binary)
        current_app.logger.info('Uploaded {} for file {}'.format(
            sizeof_fmt(binary_len),
            filename)
        )


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Gi', suffix)
