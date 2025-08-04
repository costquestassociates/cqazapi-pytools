# cqazapi-pytools

* This is a python class providing easier access to CostQuest APIs.
* API definitions are at https://developer.costquest.com
* Documentation is available at https://apidocs.costquest.com



## Usage

To use the class, add it as a submodule to your project.
```bash
git submodule add https://github.com/costquestassociates/cqazapi-pytools
```

Then you can use it via an import. You can  then access the functions after instantiating the class.
```python
import importlib
cqpt = importlib.import_module("cqazapi-pytools")

cp = cqpt.cqazapipytools(apikey)
response = cp.apiAction('https://api.costquest.com/fabric/vintages', 'GET')
print(response)
```

To get updates, you can do so by updating the submodule in the parent repository.
```bash
git submodule update --init --remote
```

There are a few options when instantiating:
`cqazapipytools(apikey, baseurl='https://api.costquest.com', usecache=True, cachepath='cache.db')`
* Must provide a valid CostQuest API key.
* Leave baseurl as default, typically.
* `usecache` defaults to True. This means that requests will be saved in a local sqlite database to avoid making the same request again. This helps when designing a process so as to not continually make the same requests and use credits needlessly.
  * It's up to the user to manage the cache. Fabric data is stable within a vintage, so cache TTL can be nearly infinite as long as the same requests are being made.
  * The cache can become very large. Consider having different cache files for different projects. Also consider using `clearCache()` or simply dropping the sqlite file when no longer needed.
  * If `usecache` is false no local cache will be used.
* `cachepath` defaults to a file named `cache.db` in the current working directory but can be customized to any path.



## Functions

Certain functions re-use the same input parameters.
* `url` is an HTTP path.
* `method` is `GET` or `POST`.
  * If the `url` parameter does not include a root domain, the tools will automatically add on `https://api.costquest.com/` as the root.
* `vintage` is a valid YYYYMM fabric vintage. These can be identified using the `fabric/vintages` endpoint.



### apiAction

`apiAction(url, method, body)`
* `body` is a python object being of type `list` or `dict` mirroring the JSON types of `array` and `object`. If `body` is provided for a `GET` request, it should be a dictionary and will be converted to query string parameters.

Returns an API response-like object.

This is used to make a single API call.



### bulkApiAction

`bulkApiAction(url, method, in_list, maxsize, *workers)`
* `in_list` must be a list of items. It can be of any size.
* `maxsize` is the maximum number of items to request at once to a bulk/`POST` API.
* `workers` is the number of parallel requests to perform. It defaults to 4.

Returns a list.

This will break up larger bulk requests into batches as well as spawn concurrent workers to speed up retrieval.



### mergeList

`mergeList(in_list, property_name)`
* `in_list` must be of type `list` and it must contain entries of type `dict`.
* `property_name` must be a key present in all dictionaries in the `in_list`.

Returns a list of dict.

This is a poor mans "join" of data. Given a single list of dictionaries, it will combine them on the chosen property based on dictionary keys. An example of this would be passing in two lists with dictionaries at a `location_id` level that you want a single list of dictionaries with one `location_id` but all properties in the resulting dictionary for each id.



### collect

`collect(vintage, geojson)`
* `geojson` is a valid GeoJSON object.

Returns a list of all fabric `uuid`s that fall within the given geojson object.



### attach

`attach(vintage, in_list, fields, *layer)`
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

To address the challenge of dealing with disparate data, the `opt_tolerance` value defaults to 0.5 and can be set between 0 and 1. At 0, no optimization to preserve credits is performed and the process will be the fastest. At 1, the process optimizes to preserve as many credits as possible by calling the `GET` variant of the `locate` API leading to slow run times but less credit usage.



### match

`match(vintage, in_list, workers=16)`
* `in_list` is a list with a format of either `[{'sourcekey':'unique id','text':'unparsed address'}]` or `[{'sourcekey':'unique id','house_number':'house_number','road':'road','unit':'unit','city':'city','state':'state','postcode':'postcode'}]`.

Returns a list of dict.

Performs address matching. Note that the `in_list` can be components or a full address.