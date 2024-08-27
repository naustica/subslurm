import os
import json
import gzip
import pickle
from pathlib import Path
import shutil
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


class OpenAlexDocumentTypesSnapshot:

    def __init__(self,
                 model_path: str,
                 download_path: str,
                 transform_path: str,
                 snapshot_date: list[int] = None):

        self.model_path = model_path
        self.download_path = download_path
        self.transform_path = transform_path
        self.snapshot_date = snapshot_date

        if Path(download_path).exists() and Path(download_path).is_dir():
            shutil.rmtree(self.download_path)

        os.makedirs(download_path, exist_ok=False)

        if Path(transform_path).exists() and Path(transform_path).is_dir():
            shutil.rmtree(self.transform_path)

        os.makedirs(transform_path, exist_ok=False)

        self.model_file = open(self.model_path, 'rb')
        self.model = pickle.load(self.model_file)

    SNAPSHOT_URL = 's3://openalex'

    @staticmethod
    def page_counter(page_str) -> int:
        page_int = 1
        if '-' in str(page_str):
            try:
                page_str = re.sub(r'(\.e)[\d]*', '', page_str)
                page_str = re.sub(r'(\.)[\d]*', '', page_str)
                page_str = re.sub(r'(?<=\d)(e)(\d)*', '', page_str)
                page_str = re.sub(r'[^\d-]', '', page_str)
                page_int = int(abs(eval(page_str)))
                if page_int != 1:
                    page_int += 1
            except:
                pass

        return page_int

    @staticmethod
    def get_label(proba: float) -> str:
        if proba >= 0.5:
            label = 'research_discourse'
            return label
        else:
            label = 'editorial_discourse'
            return label

    def transform_file(self, input_file_path: str, output_file_path: str) -> None:
        new_data = []

        with gzip.open(input_file_path, 'r') as file:
            for line in file:

                new_item = json.loads(line)
                if isinstance(new_item, dict):

                    source_type = None

                    primary_location = new_item.get('primary_location')
                    if primary_location:
                        source = primary_location.get('source')
                        if source:
                            source_type = source.get('type')

                    item_type = new_item.get('type')


                    if source_type == 'journal' and item_type == 'article':

                        openalex_id = new_item.get('id')
                        authors = new_item.get('authorships')
                        has_license = bool(new_item.get('license'))
                        is_referenced_by_count = new_item.get('cited_by_count')
                        references_works = new_item.get('referenced_works')
                        has_funder = bool(new_item.get('grants'))
                        first_page = new_item.get('biblio').get('first_page')
                        last_page = new_item.get('biblio').get('last_page')
                        has_abstract = bool(new_item.get('abstract_inverted_index'))
                        title = new_item.get('title')
                        inst_count = new_item.get('institutions_distinct_count')
                        has_oa_url = bool(new_item.get('open_access').get('is_oa'))

                        if authors:
                            author_count = len(authors)
                        else:
                            author_count = 0

                        if references_works:
                            references_count = len(references_works)
                        else:
                            references_count = 0

                        if first_page:
                            if last_page:
                                page_count = self.page_counter(str(first_page) + '-' + str(last_page))
                            else:
                                page_count = self.page_counter(str(first_page))
                        else:
                            page_count = 1

                        if title:
                            title_word_length = len(title.split())
                        else:
                            title_word_length = 0

                        if not inst_count:
                            inst_count = 0

                        probas = self.model.predict_proba([[int(author_count),
                                                       int(has_license),
                                                       int(is_referenced_by_count),
                                                       int(references_count),
                                                       int(has_funder),
                                                       int(page_count),
                                                       int(has_abstract),
                                                       int(title_word_length),
                                                       int(inst_count),
                                                       int(has_oa_url)]])

                        proba = probas[:, 1][0]

                        label = self.get_label(proba)

                        new_data.append(dict(openalex_id=openalex_id, label=label, proba=proba))

            self.write_file(new_data, output_file_path)

    @staticmethod
    def write_file(data, output_file_path: str) -> None:

        with gzip.open(output_file_path, mode='wb') as output_file:
            result = [json.dumps(record, ensure_ascii=False).encode('utf-8') for record in data]
            for line in result:
                output_file.write(line + bytes('\n', encoding='utf8'))

    def transform_snapshot(self, max_workers: int = cpu_count()) -> None:

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for directory in os.listdir(self.download_path):
                if os.path.isdir(self.download_path + '/' + directory):
                    os.makedirs(self.transform_path + '/' + directory, exist_ok=True)
                    for input_file in os.listdir(self.download_path + '/' + directory):
                        output_file_path = os.path.join(self.transform_path + '/' + directory + '/' + os.path.basename(input_file))
                        future = executor.submit(self.transform_file,
                                                 input_file_path=self.download_path + '/' + directory + '/' + input_file,
                                                 output_file_path=output_file_path)
                        futures.append(future)

            for future in as_completed(futures):
                future.result()


if __name__ == '__main__':

    with open('/scratch/users/haupka/document_type_snapshot.pkl', 'rb') as inp:
        openalex_works_snapshot = pickle.load(inp)
        openalex_works_snapshot.transform_snapshot()