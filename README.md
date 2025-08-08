# cqazapi-pytools

* This is a python class providing easier access to CostQuest APIs.
* API definitions are at https://developer.costquest.com
* API documentation is available at https://apidocs.costquest.com

## Issues, Bugs, and Feature Requests

Please create an issue on this GitHub repository.



## Installation

Installation can be by either adding the repository as a submodule to an existing repository, or by cloning the repository.

### Option 1: Submodule

To use the class, add it as a submodule to your project.
```bash
git submodule add https://github.com/costquestassociates/cqazapi-pytools cqazapipytools
```

To get updates, you can do so by updating the submodule in the parent repository.
```bash
git submodule update --init --remote
```

### Option 2: Clone

If you prefer, simply clone the repository.

```bash
git clone https://github.com/costquestassociates/cqazapi-pytools cqazapipytools
```



### Usage

Usage is as simple as importing and then instantiating.
```python
from cqazapipytools import *
with cqazapipytools(apikey) as cp:
  response = cp.apiAction('fabric/vintages', 'GET')
print(response)
```

There are a few options when instantiating:
`cqazapipytools(apikey, baseurl='https://api.costquest.com/', cachepath=None)`
* Must provide a valid CostQuest API key.
* Leave baseurl as default, typically.
* `cachepath` defines the path to a cache file. Example being `cachepath='C:\Temp\cache.db'` on windows or `cachepath='~/cache.db'` on linux.
  * Will be created if the file does not exist, but the directory must pre-exist.
  * This means that requests will be saved in a local sqlite database to avoid making the same request again. This helps when designing a process so as to not continually make the same requests and use credits needlessly.
  * It's up to the user to manage the cache. Fabric data is stable within a vintage, so TTL can typically be long.
  * If input data stays the same, PyTools will attempt to sort and make similar requests to increase cache hits. If the input data changes, there may be no cache hits. Single requests to `GET` endpoints are more likely to generate cache hits.
  * The cache can become very large. Consider having different cache files for different projects. Also consider using `clearCache()` or simply dropping the sqlite file when no longer needed.
  * If `usecache=False` for the `apiaction()` or `bulkApiAction()` functions that particular request or set of requests will skip caching, otherwise the global `usecache` setting will be used which is set to True when `cachepath` is provided.



## Functions

Certain functions re-use the same input parameters.
* `url` is an HTTP path.
  * If the `url` parameter does not include a root domain, the tools will automatically add on `baseurl` as the root.
* `method` is `GET` or `POST`.
* `vintage` is a valid YYYYMM fabric vintage. These can be identified using the `fabric/vintages` endpoint.
* `workers` is how many concurrent threads can be used to perform requests.



### apiAction

`apiAction(url, method, body, usecache=None)`
* `body` is a python object being of type `list` or `dict` mirroring the JSON types of `array` and `object`. If `body` is provided for a `GET` request, it should be a dictionary and will be converted to query string parameters.

Returns an API response-like object.

This is used to make a single API call.



### bulkApiAction

`bulkApiAction(url, method, in_list, maxsize, *workers, *usecache)`
* `in_list` must be a list of items. It can be of any size.
* `maxsize` is the maximum number of items to request at once to a bulk/`POST` API.

Returns a list.

This will break up larger bulk requests into batches as well as spawn concurrent workers to speed up retrieval.



### mergeList

`mergeList(in_list, property_name)`
* `in_list` must be of type `list` and it must contain entries of type `dict`.
* `property_name` must be a key present in all dictionaries in the `in_list`.

Returns a list of dict.

This is a poor mans "join" of data. Given a single list of dictionaries, it will combine them on the chosen property based on dictionary keys. An example of this would be passing in two lists with dictionaries at a `location_id` level that you want a single list of dictionaries with one `location_id` but all properties in the resulting dictionary for each id.

**IMPORTANT:** Because it uses dictionary hashing to find unique values for the `property_name`, it will result in a loss of records if the value of `property_name` is not unique - only one result will end up reflected in the result. 



### flattenList

`flattenList(in_list)`
* `in_list` must be of type `list` and it must contain entries of type `dict`.

Returns a list of dict.

This will attempt to crudely flatten the data if there are complex objects provided (nested lists, dicts) into a list of dict.



### csvRead

`csvRead(filepath)`
* `filepath` is a path to a CSV file.

Returns a list of dict.



### csvWrite

`csvwrite(filepath, in_list)`
* `filepath` is a path to a CSV file. Will be overwritten if exists.
* `in_list` is a list of dict. If the dict contains additional objects (list, dict) they will be modified using the `flattenList()` function.



### collect

`collect(vintage, geojson)`
* `geojson` is a valid GeoJSON object.

Returns a list of all fabric `uuid`s that fall within the given geojson object.



### attach

`attach(vintage, in_list, fields, *layer, *workers)`
* `in_list` is a list of form `['uuid1','uuid2']`.
* `fields` is a list of fields to attach of form `['location_id','latitude','longitude']`.
* `layer` is the layer type, it defaults to `locations`. Valid layers can be identified using the `fabric/layers` endpoint.

Returns a list of dict.

Attaches data attributes to a list of `uuid`s.



### locate

`locate(vintage, in_list, *opt_tolerance, *parceldistancem, *neardistancem)`
* `in_list` is a list of form `[{'sourcekey':'unique id','latitude':0,'longitude':0}]`.
* `opt_tolerance` is a value between 0 and 1. It defaults to 0.5.
* `parceldistancem` see API documentation.
* `neardistancem` see API documentation.

Returns a list of dict.

Automatically breaks up data into manageable geographic areas for calling the `locate` API across varying geographic areas.

#### Locate Usage Details
Since the `locate` API can only operate on data that spans less than 10,000 square kilometers there is a trade off when breaking up data spatially. The locate function within these tools will assign data to h3_4's and then bulk process within each of those. This works very well for densely clustered data, but poorly for sparse disparate data.

To address the challenge of dealing with disparate data, the `opt_tolerance` value defaults to 0.5 and can be set between 0 and 1. At 0, no optimization to preserve credits is performed and the process will make the fewest requests. At 1, the process optimizes to preserve as many credits as possible by calling the `GET` variant of the `locate` API. The fastest setting will vary based on the geographic distribution of the input data.



### match

`match(vintage, in_list, *workers)`
* `in_list` is a list with a format of either `[{'sourcekey':'unique id','text':'unparsed address'}]` or `[{'sourcekey':'unique id','house_number':'house_number','road':'road','unit':'unit','city':'city','state':'state','postcode':'postcode'}]`.

Returns a list of dict.

Performs address matching. Note that the `in_list` can be components or a full address.



## Demo Examples

### Data Pull
```python
from cqazapipytools import *
with cqazapipytools(os.environ['CQAPIKEY']) as cp:
    geojson = cp.apiAction('geosvc/libgetgeo/tiger/2020/counties?id=01001','GET')
    collect = cp.collect('202412',geojson)
    attach = cp.attach('202412',in_list=collect,fields=['location_id','latitude','longitude','address_primary','postal_code'])
    cp.csvWrite('demo_data_output.csv',attach)
```

### Address Matching
```python
from cqazapipytools import *
with cqazapipytools(os.environ['CQAPIKEY'], cachepath='cache.db') as cp:
    addresses = cp.csvRead('demo_match_input.csv')
    match = cp.match('202506',addresses)
    cp.csvWrite('demo_match_output.csv',match)
```

### Address Matching
```python
from cqazapipytools import *
with cqazapipytools(os.environ['CQAPIKEY'], cachepath='cache.db') as cp:
    addresses = cp.csvRead('demo_match_input.csv')
    match = cp.match('202506',addresses)
    cp.csvWrite('demo_match_output.csv',match)
```

### Locate Coordinates
```python
from cqazapipytools import *
with cqazapipytools(os.environ['CQAPIKEY']) as cp:
    coordinates = cp.csvRead('demo_locate_input.csv')
    locate = cp.locate('202506', coordinates)
    cp.csvWrite('demo_locate_output.csv', cp.mergeList(locate + coordinates, 'sourcekey'))
```

### Coverage Pull
```python
from cqazapipytools import *
with cqazapipytools(os.environ['CQAPIKEY'], cachepath='cache.db') as cp:
    geojson = cp.apiAction('geosvc/libgetgeo/tiger/2020/counties?id=01001','GET')
    collect = cp.collect('202412',geojson)
    attach = cp.attach('202412',in_list=collect,fields=['location_id'])
    coverage = cp.bulkApiAction('coverage/bdcfixed?vintage=202412', 'POST', [a['location_id'] for a in attach], 1000)
    cp.csvWrite('demo_coverage_output.csv', coverage)
```