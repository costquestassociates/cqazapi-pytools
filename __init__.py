import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry
import urllib.parse
import time
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import h3
import math
import sqlite3
import json
import os
import hashlib

class cqazapipytools:

    def __init__(self, apikey, baseurl = 'https://api.costquest.com/', usecache = True, cachepath = 'cache.db'):
        self.apikey = apikey
        self.baseurl = baseurl
        self.count = 0
        self.total = 0
        self.usecache = usecache
        self.cachepath = cachepath
        if self.usecache:
            self.createCache()
        self.listapis = self.apiAction('accountcontrol/listapis', 'GET', usecache=False)
    
    def clearCache(self):
       if os.path.exists(self.cachepath):
            os.remove(self.cachepath)
    
    def createCache(self):
        with sqlite3.connect(self.cachepath) as cn:
            cn = sqlite3.connect(self.cachepath)
            cr = cn.cursor()
            cr.execute('create table if not exists cache (hashvalue text, response text)')
            cr.execute('create index if not exists hashvalue_index on cache (hashvalue)')
            cn.commit()
    
    def saveCache(self, url, method, data, response):
        body_string = ""
        if method.upper() != 'GET':
            try:
                body_string = json.dumps(data)
            except:
                pass
        with sqlite3.connect(self.cachepath) as cn:
            cur = cn.cursor()
            cur.execute('insert into cache (hashvalue,response) values (?,?)', (self.createHash(f"{url}_{method}_{body_string}"), json.dumps(response),))
            cn.commit()

    def loadCache(self, url, method, data):
        body_string = ""
        if method.upper() != 'GET':
            try:
                body_string = json.dumps(data)
            except:
                pass
        with sqlite3.connect(self.cachepath) as cn:
            cr = cn.cursor()
            cr.execute('select response from cache where hashvalue=?', (self.createHash(f"{url}_{method}_{body_string}"),))
            r = cr.fetchone()
            if not r is None:
                return json.loads(r[0])
    
    def createHash(self, data):
        return hashlib.sha1(data.encode()).hexdigest()

    def apiAction(self, url, method, in_json=None, usecache=None):
        action_usecache = self.usecache
        if not usecache is None:
            action_usecache = usecache
        starttime = time.time()
        if 'http' not in url:
            url = f"{self.baseurl}{url}"
        if method.upper() == 'GET':
            if in_json is not None:
                if len(in_json[0]) > 0:
                    beginstr = '?'
                    if '?' in url:
                        beginstr = '&'
                    url += f"{beginstr}{urllib.parse.urlencode(in_json[0])}"
        if action_usecache:
            cache_result = self.loadCache(url, method, in_json)
            if not cache_result is None:
                endtime = time.time()
                self.count += 1
                print(f"API request ({self.count}/{self.total}) to CACHE {url} succeeded in {str(round(float(endtime-starttime),3))}s")
                return cache_result
        adapter = HTTPAdapter(max_retries=Retry(total=3, backoff_factor=1, status_forcelist=[401, 403, 500, 502, 503, 504], allowed_methods=['GET','POST']))
        session = requests.Session()
        session.mount('https://', adapter)
        session.headers['apikey'] = self.apikey
        if method.upper() == 'GET':
            response = session.get(url)
        if method.upper() == 'POST':
            response = session.post(url, json=in_json)
        if response.status_code == 429:
            retryafter = int(response.headers.get('Retry-After', 60)) + 1
            print(f'Rate limiting encountered, waiting for {retryafter}s')
            time.sleep(retryafter)
            return self.apiAction(url, method, in_json)
        elif response.status_code != 200:
            raise Exception(f'API request failed with status code {response.status_code} and message {response.text}')
        else:
            session.close()
            endtime = time.time()
            self.count += 1
            print(f"API request ({self.count}/{self.total}) to {method.upper()} {url} succeeded in {str(round(float(endtime-starttime),3))}s")
            if action_usecache:
                self.saveCache(url, method, in_json, response.json())
            return response.json()

    def bulkApiAction(self, url, method, in_list, maxsize, workers=4, usecache=None):
        self.count = 0
        results = []
        if len(in_list) == 0:
            return results
        if method == 'GET':
            maxsize = 1
        if len(in_list) < maxsize:
            results = self.apiAction(url, method, in_list)
        else:
            chunks = self.chunkList(in_list, maxsize)
            self.total = len(chunks)
            q = queue.Queue()
            for chunk in chunks:
                q.put(chunk)
            def worker():
                while True:
                    try:
                        chunk = q.get(block=False)
                        result = self.apiAction(url, method, chunk, usecache)
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

    def getCredits(self, api, operation, method):
        for a in self.listapis:
            if a['api'] == api and a['operation'] == operation and a['method'] == method:
                return a['credits']
            
    def getMaxRequest(self, api, operation):
        for a in self.listapis:
            if a['api'] == api and a['operation'] == operation and a['method'] == 'POST':
                return a['maxrequest']

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
    
    def attach(self, vintage, in_list, fields, workers=4):
        if self.getCredits('fabric','data','GET') * len(in_list) < self.getCredits('fabric','bulk','POST') * math.ceil(len(fields)/5) * math.ceil(len(in_list)/self.getMaxRequest('fabric','bulk')):
            if 'uuid' not in fields:
                fields.append('uuid')
            get_in_list = []
            for l in in_list:
                get_in_list.append({'uuid':l})
            results = self.bulkApiAction(self.baseurl + f'fabric/{vintage}/data/locations', 'GET', get_in_list, 1, workers)
            for r in results:
                for k in list(r.keys()):
                    if k not in fields:
                        r.pop(k, None)
            return results
        else:
            fieldgroups = self.chunkList(fields, 5)
            results = []
            for fg in fieldgroups:
                fields = ','.join(fg)
                results.extend(self.bulkApiAction(self.baseurl + f'fabric/{vintage}/bulk/locations?field={fields}', 'POST', in_list, self.getMaxRequest('fabric','bulk'), workers))
            return self.mergeList(results, 'uuid')
    
    def locate(self, vintage, in_list, opt_tolerance = 0.5, parceldistancem = None, neardistancem = None, workers=4):
        for loc in in_list:
            loc['h3'] = h3.latlng_to_cell(float(loc['latitude']), float(loc['longitude']), 4)
        h3_merged = in_list
        h3_unique = {}
        for r in h3_merged:
            if r['h3'] not in h3_unique.keys():
                h3_unique[r['h3']] = []
            h3_unique[r['h3']].append(r)
        print(f"Locating across {len(h3_unique)} h3_4s")
        results = []
        qs = {}
        if not parceldistancem is None:
            qs['parceldistancem'] = parceldistancem
        if not neardistancem is None:
            qs['neardistancem'] = neardistancem
        q = ''
        if len(qs) > 0:
            q = '?'
        credit_cost = self.getCredits('fabricext','locate','POST')
        single_requests = []
        for h3u in h3_unique:
            if len(h3_unique[h3u]) < credit_cost * opt_tolerance:
                for r in h3_unique[h3u]:
                    single_requests.append(r)
            else:
                results.extend(self.bulkApiAction(f"{self.baseurl}fabricext/{vintage}/locate{q}{urllib.parse.urlencode(qs)}", 'POST', h3_unique[h3u], self.getMaxRequest('fabricext','locate'), workers))
        results.extend(self.bulkApiAction(f"{self.baseurl}fabricext/{vintage}/locate{q}{urllib.parse.urlencode(qs)}", 'GET', single_requests, 1, workers))
        return results

    def match(self, vintage, in_list, workers=16):
        if len(in_list) * self.getCredits('fabricext','match','GET') < self.getCredits('fabricext','match','POST'):
            return self.bulkApiAction(f'fabricext/{vintage}/match', 'GET', in_list, 1, workers)
        else:
            return self.bulkApiAction(f'fabricext/{vintage}/match', 'POST', in_list, self.getMaxRequest('fabricext','match'), workers)