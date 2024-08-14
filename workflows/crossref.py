# Copyright 2020 Curtin University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Author: Aniek Roelofs, James Diprose

# Modifications copyright (C) 2024 Nick Haupka


import os
import json
import gzip
import requests
import functools
import shutil
import pickle
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


class CrossrefSnapshot:

    def __init__(self,
                 download_path: str,
                 transform_path: str,
                 snapshot_date: list[int] = None,
                 filename: str = 'crossref.json'):

        self.filename = filename
        self.download_path = download_path
        self.transform_path = transform_path

        if not snapshot_date:
            self.snapshot_date = self.get_latest_snapshot_date()

        if Path(download_path).exists() and Path(download_path).is_dir():
            os.rmdir(self.download_path)

        os.makedirs(download_path, exist_ok=False)

        if Path(transform_path).exists() and Path(transform_path).is_dir():
            os.rmdir(self.transform_path)

        os.makedirs(transform_path, exist_ok=False)

    SNAPSHOT_URL = 'https://api.crossref.org/snapshots/monthly/{year}/{month:02d}/all.json.tar.gz'

    @property
    def api_token(self):
        api_token = os.environ['CROSSREF_PLUS_API_TOKEN']
        return api_token

    @staticmethod
    def get_latest_snapshot_date() -> list[int]:

        page = requests.get('https://api.crossref.org/snapshots/monthly/latest/')

        soup = BeautifulSoup(page.content, 'html.parser')

        a = soup.find('a', href=True)

        year = int(re.search(r'\d{4}', a['href']).group(0))

        month = int(re.search(r'(?<=/)\d{2}(?=/)', a['href']).group(0))

        return [year, month]

    def download(self):

        year, month = self.snapshot_date

        url = self.SNAPSHOT_URL.format(year=year, month=month)

        header = {'Crossref-Plus-API-Token': f'Bearer {self.api_token}'}

        with requests.get(url, headers=header, stream=True) as response:
            with open(self.download_path + '/' + self.filename, 'wb') as file:
                response.raw.read = functools.partial(response.raw.read, decode_content=False)
                shutil.copyfileobj(response.raw, file)

    def transform_file(self, input_file_path: str, output_file_path: str):

        with gzip.open(input_file_path, mode='r') as input_file:
            input_data = json.load(input_file)

            output_data = []
            for item in input_data['items']:

                transformed_item = self.transform_item(item)

                output_data.append(transformed_item)

            CrossrefSnapshot.write_file(output_data, output_file_path)

    @staticmethod
    def write_file(data, output_file_path: str):

        with gzip.open(output_file_path, mode='wb') as output_file:
            result = [json.dumps(record, ensure_ascii=False).encode('utf-8') for record in data]
            for line in result:
                output_file.write(line + bytes('\n', encoding='utf8'))

    @staticmethod
    def transform_item(item):
        if isinstance(item, dict):
            new = {}
            for k, v in item.items():

                if k == 'DOI':
                    k = 'doi'

                if k == 'URL':
                    k = 'url'

                if k == 'ISBN':
                    k = 'isbn'

                if k == 'ORCID':
                    k = 'orcid'

                if k == 'title':
                    if isinstance(v, list) and len(v) >= 1:
                        v = v[0]

                if k == 'container-title':
                    if isinstance(v, list) and len(v) >= 1:
                        v = v[0]

                if k == 'ISSN':
                    k = 'issn'
                    v = ','.join(list(set(v)))

                if k == 'archive':
                    v = ','.join(list(set(v)))

                if k == 'abstract':
                    if bool(item.get('abstract')):
                        v = True
                    else:
                        v = False

                if k == 'date-parts':

                    if not v:
                        v = [[]]

                    v = v[0]

                    try:

                        len_arr_date_parts = len(v)

                        if len_arr_date_parts > 0:
                            if not len(str(v[0])) == 4:
                                v = None

                        if len_arr_date_parts == 1:
                            if v[0] is None:
                                v = None
                            else:
                                v = '-'.join([str(v[0]), '1', '1'])
                                v = datetime.strptime(v, '%Y-%m-%d')

                        elif len_arr_date_parts == 2:
                            v = '-'.join([str(v[0]), str(v[1]), '1'])
                            v = datetime.strptime(v, '%Y-%m-%d')

                        elif len_arr_date_parts == 3:
                            v = '-'.join([str(v[0]), str(v[1]), str(v[2])])
                            v = datetime.strptime(v, '%Y-%m-%d')

                    except:

                        v = None

                    if v:
                        v = v.strftime('%Y-%m-%d')

                k = k.replace('-', '_')

                new[k] = CrossrefSnapshot.transform_item(v)
            return new
        elif isinstance(item, list):
            return [CrossrefSnapshot.transform_item(i) for i in item]
        else:
            return item

    def transform_snapshot(self, max_workers: int = cpu_count()):

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

    with open('/scratch/users/haupka/crossref_snapshot.pkl', 'rb') as inp:
        crossref_snapshot = pickle.load(inp)
        crossref_snapshot.transform_snapshot()
