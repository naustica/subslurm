import pytest
import os
import shutil
from workflows.document_types import DocumentTypeSnapshot


class TestDocumentTypeSnapshot:

    test_dir = os.path.abspath(os.path.dirname(__file__))

    @pytest.fixture
    def document_type_snapshot(self):
        snapshot = DocumentTypeSnapshot(
            model_path=os.path.join(self.test_dir, 'model.pkl'),
            download_path=os.path.join(self.test_dir, 'test_files_document_types'),
            transform_path=os.path.join(self.test_dir, 'document_type_transform')
        )
        yield snapshot
        shutil.rmtree(os.path.join(self.test_dir, 'document_type_transform'), ignore_errors=True)

    def test_page_counter(self, document_type_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert document_type_snapshot.page_counter(page_str) == 10

    def test_has_abstract(self, document_type_snapshot):

        abstract_str = 'This is an abstract.'
        assert document_type_snapshot.has_abstract(abstract_str) == 1

    def test_get_label(self, document_type_snapshot):

        research_proba = 0.93
        assert document_type_snapshot.get_label(research_proba) == 'research_discourse'

        editorial_proba = 0.34
        assert document_type_snapshot.get_label(editorial_proba) == 'editorial_discourse'

    def test_write_file(self, document_type_snapshot):

        output_file = os.path.join(self.test_dir, 'document_type_transform/document_type_sample.jsonl.gz')

        data = [
            {
                'doi': '',
                'label': 'research_discourse',
                'proba': 0.93
            },
            {
                'doi': '',
                'label': 'research_discourse',
                'proba': 0.93
            }
        ]

        document_type_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, document_type_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_document_types/document_type_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'document_type_transform/document_type_sample.jsonl.gz')

        document_type_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, document_type_snapshot):

        input_file = os.path.join(self.test_dir, 'test_files_document_types/document_type_sample.jsonl.gz')

        output_file = os.path.join(self.test_dir, 'document_type_transform/document_type_sample.jsonl.gz')

        shutil.copyfile(input_file, output_file)

        document_type_snapshot.transform_snapshot()

        assert os.path.exists(output_file)