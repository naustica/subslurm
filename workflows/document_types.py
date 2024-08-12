import os
import json
import gzip
import pickle
from pathlib import Path
import pandas as pd
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


class DocumentTypeSnapshot:

    def __init__(self,
                 model_path: str,
                 download_path: str,
                 transform_path: str):

        self.model_path = model_path
        self.download_path = download_path
        self.transform_path = transform_path

        if Path(transform_path).exists() and Path(transform_path).is_dir():
            os.rmdir(self.transform_path)
        else:
            os.makedirs(transform_path, exist_ok=False)

    @staticmethod
    def page_counter(page_str):
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
    def has_abstract(abstract_str):
        if pd.isna(abstract_str):
            return 0
        else:
            return 1

    @staticmethod
    def write_file(data, output_file_path: str):

        with gzip.open(output_file_path, mode='wb') as output_file:
            result = [json.dumps(record, ensure_ascii=False).encode('utf-8') for record in data]
            for line in result:
                output_file.write(line + bytes('\n', encoding='utf8'))

    def transform_file(self, input_file_path: str, output_file_path: str):
        new_data = []

        with open(self.model_path, 'rb') as model_file:
            model = pickle.load(model_file)

            with gzip.open(input_file_path, 'r') as file:
                for line in file:

                    new_item = json.loads(line)
                    if isinstance(new_item, dict):

                        doi = new_item.get('doi')
                        author_count = new_item.get('author_count')
                        has_license = new_item.get('has_license')
                        is_referenced_by_count = new_item.get('is_referenced_by_count')
                        references_count = new_item.get('references_count')
                        has_funder = new_item.get('has_funder')
                        page = new_item.get('page')
                        abstract = new_item.get('has_abstract')
                        title = new_item.get('title')
                        inst_count = new_item.get('inst_count')
                        has_oa_url = new_item.get('has_oa_url')

                        page_count = DocumentTypeSnapshot.page_counter(page)
                        has_abstract = DocumentTypeSnapshot.has_abstract(abstract)
                        title_word_length = len(title.split())

                        label = model.predict_proba([[doi,
                                                      author_count,
                                                      has_license,
                                                      is_referenced_by_count,
                                                      references_count,
                                                      has_funder,
                                                      page_count,
                                                      has_abstract,
                                                      title_word_length,
                                                      inst_count,
                                                      has_oa_url]])

                        proba = label[:, 1][0]
                        if label[:, 1][0] >= 0.5:
                            label = 'research_discourse'
                        else:
                            label = 'editorial_discourse'

                        new_data.append(dict(doi=doi, label=label, proba=proba))

                DocumentTypeSnapshot.write_file(new_data, output_file_path)

    def transform_release(self, max_workers: int = cpu_count()):

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = []

            for input_file in os.listdir(self.download_path):
                output_file_path = os.path.join(self.transform_path,
                                                os.path.basename(input_file) + 'l.gz')
                future = executor.submit(self.transform_file,
                                         input_file_path=self.download_path + '/' + input_file,
                                         output_file_path=output_file_path)
                futures.append(future)

            for future in as_completed(futures):
                future.result()


if __name__ == '__main__':

    with open('/scratch/users/haupka/document_type_snapshot.pkl', 'rb') as inp:
        document_type_snapshot = pickle.load(inp)
        document_type_snapshot.transform_release()
