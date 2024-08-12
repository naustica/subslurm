import pytest
import os
import shutil
from workflows.document_types import DocumentTypeSnapshot


class TestDocumentTypeSnapshot:

    @pytest.fixture
    def document_type_snapshot(self):
        snapshot = DocumentTypeSnapshot(
            model_path='./test',
            download_path='./test',
            transform_path='./test'
        )
        yield snapshot
        shutil.rmtree('./test', ignore_errors=True)

    def test_page_counter(self, document_type_snapshot):

        page_str = 'e1010.e87-e1019.e87'
        assert document_type_snapshot.page_counter(page_str) == 10

    def test_has_abstract(self, document_type_snapshot):

        abstract_str = 'This is an abstract.'
        assert document_type_snapshot.has_abstract(abstract_str) == 1

    def test_write_file(self, document_type_snapshot):

        filename = 'test.jsonl.gz'
        filepath = './test'

        output_file = os.path.join(filepath, filename)

        data = dict(
            doi='',
            label='research_discourse',
            proba=0.93
        )

        document_type_snapshot.write_file(data, output_file)

        assert os.path.exists(output_file)

