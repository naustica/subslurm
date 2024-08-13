import pytest
import os
import shutil
from workflows.crossref import CrossrefSnapshot


class TestCrossrefSnapshot:

    @pytest.fixture
    def crossref_snapshot(self):
        snapshot = CrossrefSnapshot(
            snapshot_date=[2024, 7],
            download_path='crossref_download',
            transform_path='crossref_transform'
        )
        yield snapshot
        shutil.rmtree('crossref_download', ignore_errors=True)
        shutil.rmtree('crossref_transform', ignore_errors=True)

    def test_write_file(self, crossref_snapshot):

        output_file = os.path.join('crossref_transform', 'crossref_sample.json.gz')

        data = dict()

        crossref_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, crossref_snapshot):

        input_file = os.path.join('test_files_crossref', 'crossref_sample.json.gz')

        output_file = os.path.join('crossref_transform', 'crossref_sample.json.gz')

        crossref_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, crossref_snapshot):
        input_file = os.path.join('test_files_crossref', 'crossref_sample.json.gz')

        output_file = os.path.join('crossref_transform', 'crossref_sample.json.gz')

        shutil.copyfile(input_file, output_file)

        crossref_snapshot.transform_snapshot()

        assert os.path.exists(output_file)