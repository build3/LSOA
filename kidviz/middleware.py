import logging
import os

from botocore.exceptions import ClientError
from django.core.files.storage import default_storage

logger = logging.getLogger('s3file')


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

        # A bunch of monkey-patched methods to override
        # S3Boto3StorageFile and S3Boto3Storage to copy
        # file from temporary storage directly on S3 instead
        # of downloading and re-uploading it.
        def _dummy_get_file(self):
            """
            Return S3 Bucket object instead of file contents
            """
            if hasattr(self, '_use_dummy_s3_methods'):
                return self.obj
            else:
                # Call original method
                return self._get_file()

        def _dummy_save_content(self, obj, content, parameters):
            """
            If passed an S3.Object with bucket_name and key,
            issue copy instead of upload_fileobj. Otherwise,
            revert to original method, so this doesn't break
            the storage.
            """
            if hasattr(content, 'bucket_name'):
                obj.copy({
                    'Bucket': content.bucket_name,
                    'Key': content.key
                })
            else:
                self._old_save_content(obj, content, parameters)

        for path in paths:
            f = default_storage.open(path)
            f.name = os.path.basename(path)

            # Set a flag so that we can decide whether to pass
            # a call to an original method instead
            f._use_dummy_s3_methods = True

            # Override file getter to return S3.Object
            f.__class__.file = property(
                _dummy_get_file,
                f.__class__._set_file
            )
            # Override _save_content to copy instead of re-upload
            # and save the old method for use in other cases
            default_storage.__class__._old_save_content = default_storage.__class__._save_content
            default_storage.__class__._save_content = _dummy_save_content

            try:
                yield f
            except ClientError:
                logger.exception("File not found: %s", path)
