import pytest
import os
import shutil
from workflows.crossref import CrossrefSnapshot


class TestCrossrefSnapshot:

    test_dir = os.path.abspath(os.path.dirname(__file__))

    @pytest.fixture
    def crossref_snapshot(self):
        snapshot = CrossrefSnapshot(
            download_path=os.path.join(self.test_dir, 'crossref_download'),
            transform_path=os.path.join(self.test_dir, 'crossref_transform')
        )
        yield snapshot
        shutil.rmtree(os.path.join(self.test_dir, 'crossref_download'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.test_dir, 'crossref_transform'), ignore_errors=True)

    def test_get_snapshot_date(self, crossref_snapshot):

        year, month = crossref_snapshot.get_latest_snapshot_date()

        assert len(str(year)) == 4
        assert 1 <= len(str(month)) <= 2

        year, month = crossref_snapshot.snapshot_date

        assert len(str(year)) == 4
        assert 1 <= len(str(month)) <= 2

    def test_write_file(self, crossref_snapshot):

        output_file = os.path.join(self.test_dir, 'crossref_transform/crossref_sample.jsonl.gz')

        data = dict()

        crossref_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, crossref_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_crossref/crossref_sample.json.gz')

        output_file = os.path.join(self.test_dir, 'crossref_transform/crossref_sample.jsonl.gz')

        crossref_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, crossref_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_crossref/crossref_sample.json.gz')

        output_file = os.path.join(self.test_dir, 'crossref_transform/crossref_sample.jsonl.gz')

        shutil.copyfile(input_file, output_file)

        crossref_snapshot.transform_snapshot()

        assert os.path.exists(output_file)