import pytest
import os
import shutil
from workflows.document_types import OpenAlexDocumentTypesSnapshot


class TestOpenAlexDocumentTypesSnapshot:

    test_dir = os.path.abspath(os.path.dirname(__file__))

    @pytest.fixture
    def openalex_snapshot(self):
        snapshot = OpenAlexDocumentTypesSnapshot(
            model_path=os.path.join(self.test_dir, 'model.pkl'),
            download_path=os.path.join(self.test_dir, 'openalex_download'),
            transform_path=os.path.join(self.test_dir, 'openalex_transform'),
        )
        yield snapshot
        shutil.rmtree(os.path.join(self.test_dir, 'openalex_download'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.test_dir, 'openalex_transform'), ignore_errors=True)

    def test_page_counter(self, openalex_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert openalex_snapshot.page_counter(page_str) == 10

    def test_get_label(self, openalex_snapshot):

        research_proba = 0.93
        assert openalex_snapshot.get_label(research_proba) == 'research_discourse'

        editorial_proba = 0.34
        assert openalex_snapshot.get_label(editorial_proba) == 'editorial_discourse'

    def test_write_file(self, openalex_snapshot):

        output_file = os.path.join(self.test_dir, 'openalex_transform/openalex_sample.jsonl.gz')

        data = [
            {
                'doi': '',
                'label': 'research_discourse',
                'proba': 0.93
            },
            {
                'doi': '',
                'label': 'editorial_discourse',
                'proba': 0.34
            }
        ]

        openalex_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, openalex_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_openalex/openalex_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'openalex_transform/openalex_sample.jsonl.gz')

        openalex_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, openalex_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_openalex/openalex_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'openalex_transform/openalex_sample.jsonl.gz')

        shutil.copyfile(input_file, output_file)

        openalex_snapshot.transform_snapshot()

        assert os.path.exists(output_file)