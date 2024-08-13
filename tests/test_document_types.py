import pytest
import os
import shutil
from workflows.document_types import DocumentTypeSnapshot


class TestDocumentTypeSnapshot:

    @pytest.fixture
    def document_type_snapshot(self):
        snapshot = DocumentTypeSnapshot(
            model_path='model.pkl',
            download_path='test_files_document_types',
            transform_path='document_type_transform'
        )
        yield snapshot
        shutil.rmtree('document_type_transform', ignore_errors=True)

    def test_page_counter(self, document_type_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert document_type_snapshot.page_counter(page_str) == 10

    def test_has_abstract(self, document_type_snapshot):

        abstract_str = 'This is an abstract.'
        assert document_type_snapshot.has_abstract(abstract_str) == 1

    def test_write_file(self, document_type_snapshot):

        output_file = os.path.join('document_type_transform', 'document_type_sample.jsonl.gz')

        data = dict(
            doi='',
            label='research_discourse',
            proba=0.93
        )

        document_type_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, document_type_snapshot):

        input_file = os.path.join('test_files_document_types', 'document_type_sample.jsonl.gz')

        output_file = os.path.join('document_type_transform', 'document_type_sample.jsonl.gz')

        document_type_snapshot.transform_file(input_file, output_file)

        assert os.path.exists(output_file)

    def test_transform_snapshot(self, document_type_snapshot):

        input_file = os.path.join('test_files_document_types', 'document_type_sample.jsonl.gz')

        output_file = os.path.join('document_type_transform', 'document_type_sample.jsonl.gz')

        shutil.copyfile(input_file, output_file)

        document_type_snapshot.transform_snapshot()

        assert os.path.exists(output_file)
