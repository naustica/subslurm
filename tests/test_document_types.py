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
        os.mkdir(os.path.join(self.test_dir, 'openalex_transform/updated_date=2024-07-30'))
        yield snapshot
        shutil.rmtree(os.path.join(self.test_dir, 'openalex_download'), ignore_errors=True)
        shutil.rmtree(os.path.join(self.test_dir, 'openalex_transform'), ignore_errors=True)

    def test_page_counter(self, openalex_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert openalex_snapshot.page_counter(page_str) == 10

        page_str = '101-102'
        assert openalex_snapshot.page_counter(page_str) == 2

    def test_get_label(self, openalex_snapshot):

        research_proba = 0.93
        assert openalex_snapshot.get_label(research_proba) == True # 'research_discourse'

        editorial_proba = 0.34
        assert openalex_snapshot.get_label(editorial_proba) == False # 'editorial_discourse'

    def test_write_file(self, openalex_snapshot):

        output_file = os.path.join(self.test_dir, 'openalex_transform/updated_date=2024-07-30/openalex_sample.jsonl.gz')

        data = [
            {
                'doi': '',
                'is_research': True,
                'proba': 0.93
            },
            {
                'doi': '',
                'is_research': False,
                'proba': 0.34
            }
        ]

        openalex_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, openalex_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_openalex/updated_date=2024-07-30/openalex_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'openalex_transform/updated_date=2024-07-30/openalex_sample.jsonl.gz')

        openalex_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, openalex_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_openalex/updated_date=2024-07-30/openalex_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'openalex_transform/updated_date=2024-07-30/openalex_sample.jsonl.gz')

        shutil.copyfile(input_file, output_file)

        openalex_snapshot.transform_snapshot()

        assert os.path.exists(output_file)