import pytest
import os
import shutil
from workflows.document_types import DocumentTypeSnapshot


class TestDocumentTypeSnapshot:

    @pytest.fixture
    def document_type_snapshot(self):
        snapshot = DocumentTypeSnapshot(
            model_path='model.pkl',
            download_path='test_files',
            transform_path='transform'
        )
        yield snapshot
        shutil.rmtree('transform', ignore_errors=True)

    def test_page_counter(self, document_type_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert document_type_snapshot.page_counter(page_str) == 10

    def test_has_abstract(self, document_type_snapshot):

        abstract_str = 'This is an abstract.'
        assert document_type_snapshot.has_abstract(abstract_str) == 1

    def test_write_file(self, document_type_snapshot):

        filename = 'test.jsonl.gz'
        filepath = 'transform'

        output_file = os.path.join(filepath, filename)

        data = dict(
            doi='',
            label='research_discourse',
            proba=0.93
        )

        document_type_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

    def test_transform_file(self, document_type_snapshot):

        filename = 'test.jsonl.gz'
        filepath = 'transform'

        output_file = os.path.join(filepath, filename)

        document_type_snapshot.transform_file('test_files/test.jsonl.gz', output_file)

        assert os.path.exists(output_file)
