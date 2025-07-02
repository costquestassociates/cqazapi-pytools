import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed

class cqazapipytools:

    def __init__(self, apikey, baseurl = 'https://api.costquest.com/'):
        self.apikey = apikey
        self.baseurl = baseurl

    def apiAction(self, url, method, in_json):
        starttime = time.time()
        adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504]))
        session = requests.Session()
        session.mount('https://', adapter)
        session.headers['apikey'] = self.apikey
        if method == 'GET':
            response = requests.get(url)
        if method == 'POST':
            response = requests.post(url, json=in_json)
        if response.status_code != 200:
            raise Exception(f'API request failed with status code {response.status_code} and message {response.text}')
        endtime = time.time()
        session.close()
        print(f"API request to {url} succeeded in {str(float(endtime-starttime))}s")
        return response.json()

    def bulkApiAction(self, url, method, in_list, maxsize=1000, workers=4):
        results = []
        if len(in_list) < maxsize:
            results = self.apiAction(url, method, in_list)
        else:
            chunks = self.chunkList(in_list, maxsize)
            q = queue.Queue()
            for chunk in chunks:
                q.put(chunk)
            def worker():
                while True:
                    try:
                        chunk = q.get(block=False)
                        result = self.apiAction(url, method, chunk)
                        results.extend(result)
                        q.task_done()
                    except queue.Empty:
                        break
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = [executor.submit(worker) for _ in range(workers)]
                for future in as_completed(futures):
                    future.result()
        return results

    def chunkList(self, list, size):
        return [list[i:i + size] for i in range(0, len(list), size)]

    def mergeList(self, in_list, property_name):
        merged_dict = {}
        all_keys = set()
        for item in in_list:
            key = item.get(property_name)
            if key is not None:
                all_keys.update(item.keys())
                if key not in merged_dict:
                    merged_dict[key] = {property_name: key}
        for item in in_list:
            key = item.get(property_name)
            if key is not None:
                for k in all_keys:
                    if k in item:
                        merged_dict[key][k] = item[k]
                    elif k not in merged_dict[key]:
                        merged_dict[key][k] = None
        return list(merged_dict.values())

    def collect(self, vintage, geojson):
        results = []
        def doCollect(geojson):
            curr_result = self.apiAction(self.baseurl + f'fabric/{vintage}/collect2', 'POST', geojson)
            if len(curr_result['continuations']) > 0:
                for c in curr_result['continuations']:
                    doCollect(c['body'])
            else:
                results.extend(curr_result['data'])
        doCollect(geojson)
        return list(set(results))