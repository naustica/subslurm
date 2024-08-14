import pytest
import os
import shutil
from bq_utils import (delete_files_from_bucket,
                      download_file_from_bucket,
                      download_files_from_bucket)


class TestBqUtils:

    test_dir = os.path.abspath(os.path.dirname(__file__))

    @pytest.fixture
    def directory(self):
        os.makedirs(os.path.join(self.test_dir, 'google_cloud'), exist_ok=False)
        yield 'directory'
        shutil.rmtree(os.path.join(self.test_dir, 'google_cloud'), ignore_errors=True)

    @pytest.mark.skip(reason='TODO')
    def test_delete_files_from_bucket(self):
        delete_files_from_bucket(bucket_name='bigschol',
                                 gcb_dir='test')

    @pytest.mark.skip(reason='TODO')
    def test_download_file_from_bucket(self, directory):
        download_file_from_bucket(bucket_name='bigschol',
                                  gcb_dir='test',
                                  file_path=os.path.join(self.test_dir, 'google_cloud'),
                                  file_name='000000000000.jsonl')

    @pytest.mark.skip(reason='TODO')
    def test_download_files_from_bucket(self, directory):
        download_files_from_bucket(bucket_name='bigschol',
                                   gcb_dir='test',
                                   file_path=os.path.join(self.test_dir, 'google_cloud'))
