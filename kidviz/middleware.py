import logging
import os
import tempfile
from tempfile import SpooledTemporaryFile

from botocore.exceptions import ClientError
from django.core.files.storage import default_storage

from storages.utils import setting


logger = logging.getLogger('s3file')


def _get_file(self):
    if self._file is None:
        self._file = SpooledTemporaryFile(
            max_size=self._storage.max_memory_size,
            suffix=".S3Boto3StorageFile",
            dir=setting("FILE_UPLOAD_TEMP_DIR")
        )
        if 'r' in self._mode:
            self._is_dirty = False
            self._file.seek(0)
    return self._file


def _set_file(self, value):
    self._file = value


class S3FileMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = request.POST.getlist('s3file', [])
        for field_name in file_fields:
            paths = request.POST.getlist(field_name, [])
            request.FILES.setlist(field_name, list(self.get_files_from_storage(paths)))

        return self.get_response(request)

    @staticmethod
    def get_files_from_storage(paths):
        """Return S3 file where the name does not include the path."""
        for path in paths:

            f = default_storage.open(path)
            f.name = os.path.basename(path)

            # Set custom file property to prevent download from S3 on read()
            f._get_file = _get_file
            f._set_file = _set_file
            f.__class__.file = property(_get_file, _set_file)

            try:
                yield f
            except ClientError:
                logger.exception("File not found: %s", path)
