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
        filename = 'crossref_sample.json.gz'
        filepath = 'crossref_transform'

        output_file = os.path.join(filepath, filename)

        data = dict()

        crossref_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, crossref_snapshot):

        filename = 'crossref_sample.json.gz'
        filepath = 'crossref_transform'

        output_file = os.path.join(filepath, filename)

        crossref_snapshot.transform_file('test_files_crossref/crossref_sample.json.gz', output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, crossref_snapshot):

        filename = 'crossref_sample.json.gz'
        filepath = 'crossref_transform'

        output_file = os.path.join(filepath, filename)

        shutil.copyfile('test_files_crossref/crossref_sample.json.gz', output_file)

        crossref_snapshot.transform_snapshot()

        assert os.path.exists(output_file)