import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import urllib.parse
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import h3

class cqazapipytools:

    def __init__(self, apikey, baseurl = 'https://api.costquest.com/'):
        self.apikey = apikey
        self.baseurl = baseurl

    def apiAction(self, url, method, in_json = None):
        if 'http' not in url:
            url = f"{self.baseurl}{url}"
        starttime = time.time()
        adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504], allowed_methods=['GET','POST']))
        session = requests.Session()
        session.mount('https://', adapter)
        session.headers['apikey'] = self.apikey
        if method.upper() == 'GET':
            if in_json is not None:
                if len(in_json[0]) > 0:
                    beginstr = '?'
                    if '?' in url:
                        beginstr = '&'
                    url += f"{beginstr}{urllib.parse.urlencode(in_json[0])}"
            response = session.get(url)
        if method.upper() == 'POST':
            response = session.post(url, json=in_json)
        if response.status_code == 429:
            retryafter = int(response.headers['Retry-After']) + 1
            print(f'Rate limiting encountered, waiting for {retryafter}s')
            time.sleep(retryafter)
            return self.apiAction(url, method, in_json)
        elif response.status_code != 200:
            raise Exception(f'API request failed with status code {response.status_code} and message {response.text}')
        else:
            session.close()
            endtime = time.time()
            print(f"API request to {method.upper()} {url} succeeded in {str(round(float(endtime-starttime),3))}s")
            return response.json()

    def bulkApiAction(self, url, method, in_list, maxsize=1000, workers=4):
        if method == 'GET':
            maxsize = 1
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
                        if isinstance(result, list):
                            results.extend(result)
                        else:
                            results.append(result)
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
    
    def attach(self, vintage, in_list, fields, max_fields=5):
        fieldgroups = self.chunkList(fields, max_fields)
        results = []
        for fg in fieldgroups:
            fields = ','.join(fg)
            for r in self.bulkApiAction(self.baseurl + f'fabric/{vintage}/bulk/locations?field={fields}', 'POST', in_list):
                results.append(r)
        return self.mergeList(results, 'uuid')
    
    def locate(self, vintage, in_list, optimize_threshold = 0.5, parceldistancem = None, neardistancem = None, workers=4):
        if optimize_threshold < 1:
            credit_cost = int(self.apiAction(f"accesscontrol/getweight?{urllib.parse.urlencode({'api':'fabricext','operation':'locate','method':'POST'})}", 'GET')['credits'])
        for loc in in_list:
            loc['h3'] = h3.latlng_to_cell(float(loc['latitude']), float(loc['longitude']), 4)
        h3_merged = in_list
        h3_unique = {}
        for r in h3_merged:
            if r['h3'] not in h3_unique.keys():
                h3_unique[r['h3']] = []
            h3_unique[r['h3']].append(r)
        print(f"Locating across {len(h3_unique)} areas")
        results = []
        qs = {}
        if not parceldistancem is None:
            qs['parceldistancem'] = parceldistancem
        if not neardistancem is None:
            qs['neardistancem'] = neardistancem
        q = ''
        if len(qs) > 0:
            q = '?'
        for h3u in h3_unique:
            if len(h3_unique[h3u]) < credit_cost * optimize_threshold:
                results += self.bulkApiAction(f"{self.baseurl}fabricext/{vintage}/locate{q}{urllib.parse.urlencode(qs)}", 'GET', h3_unique[h3u], workers=workers)
            else:
                results += self.bulkApiAction(f"{self.baseurl}fabricext/{vintage}/locate{q}{urllib.parse.urlencode(qs)}", 'POST', h3_unique[h3u], workers=workers)
        return results

    def match(self, vintage, in_list, maxsize=10, workers=16):
        results = self.bulkApiAction(f'fabricext/{vintage}/match', 'POST', in_list, maxsize=maxsize, workers=workers)
        return results