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

# Modifications copyright (C) 2023 Nick Haupka


import os
import json
import jsonlines
import gzip
import requests
import functools
import shutil
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count


class CrossrefSnapshot:

    def __init__(self,
                 snapshot_date: list[int],
                 filename: str,
                 download_path: str,
                 transform_path: str):

        self.snapshot_date = snapshot_date
        self.filename = filename
        self.download_path = download_path
        self.transform_path = transform_path

        os.makedirs(download_path, exist_ok=False)
        os.makedirs(transform_path, exist_ok=False)

    SNAPSHOT_URL = 'https://api.crossref.org/snapshots/monthly/{year}/{month:02d}/all.json.tar.gz'

    @property
    def api_token(self):
        api_token = os.environ['CROSSREF_PLUS_API_TOKEN']
        return api_token

    def download(self):

        year, month = self.snapshot_date

        url = self.SNAPSHOT_URL.format(year=year, month=month)

        header = {'Crossref-Plus-API-Token': f'Bearer {self.api_token}'}

        with requests.get(url, headers=header, stream=True) as response:
            with open(self.download_path + '/' + self.filename, 'wb') as file:
                response.raw.read = functools.partial(response.raw.read, decode_content=True)
                shutil.copyfileobj(response.raw, file)

    def transform_file(self, input_file_path: str, output_file_path: str):

        with open(input_file_path, mode='r') as input_file:
            input_data = json.load(input_file)

        output_data = []
        for item in input_data['items']:

            transformed_item = self.transform_item(item)

            filtered_item = self.filter_item(transformed_item)

            if filtered_item:
                output_data.append(filtered_item)

        with gzip.open(output_file_path, mode='wb') as output_file:
            json_writer = jsonlines.Writer(output_file, compact=True)
            json_writer.write_all(output_data)

    def transform_item(self, item):

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

                if k in ['approved',
                         'created',
                         'content-created',
                         'content-updated',
                         'deposited',
                         'indexed',
                         'issued',
                         'posted',
                         'accepted',
                         'published',
                         'published-print',
                         'published-online',
                         'role-start',
                         'role-end',
                         'updated',
                         'award-start',
                         'award-planned-end',
                         'award-end',
                         'end',
                         'start']:

                    v = item[k].get('date-parts')

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

                new[k] = self.transform_item(v)
            return new
        elif isinstance(item, list):
            return [self.transform_item(i) for i in item]
        else:
            return item

    @staticmethod
    def filter_item(item):

        if 'type' not in item.keys():
            return None

        if 'issued' not in item.keys():
            return None

        for k, v in item.items():
            if k == 'type' and v != 'journal-article':
                return None
            if k == 'issued':
                filter_date = datetime(2013, 1, 1)
                if v is None:
                    return None
                if v is not None:
                    if not datetime.strptime(v, '%Y-%m-%d') >= filter_date:
                        return None

        return item

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

    def clean_up(self):

        os.rmdir(self.download_path)
        os.rmdir(self.transform_path)


if __name__ == '__main__':
    crossref_snapshot = CrossrefSnapshot(snapshot_date=[2023, 11],
                                         filename='all.json',
                                         download_path='/scratch/users/haupka/download',
                                         transform_path='/scratch/users/haupka/transform')

    crossref_snapshot.transform_release()
