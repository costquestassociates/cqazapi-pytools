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



## Functions

### apiAction

`apiAction(url, method, body)`

This is used to make a single API call.

* `method` is `GET` or `POST`.
* `body` is a python object being of type `list` or `dict` mirroring the JSON types of `array` and `object`.


### bulkApiAction

`bulkApiAction(url, method, in_list, *maxsize, *workers)`

This will break up larger bulk requests into manageable parts as well as spawn concurrent workers to speed up retrieval.

* `in_list` must be a list of items. It can be of any size.
* `maxsize` is the maximum number of items to request at once to an API. It defaults to 1,000.
* `workers` is the number of parallel requests to perform. It defaults to 4.


### mergeList

`mergeList(in_list, property_name)`

This is a poor mans "join" of data. Given a single list of dictionaries, it will combine them on the chosen property based on dictionary keys.

* `in_list` must be of type `list` and it must contain entries of type `dict`.
* `property_name` must be a key present in all dictionaries in the `in_list`.

An example of this would be passing in two lists with dictionaries at a `location_id` level that you want a single list of dictionaries with one `location_id` but all properties in the resulting dictionary for each id.


### collect

`collect(vintage, geojson)`

Input format: Valid GeoJSON.

Returns a list of all fabric `uuid`s that fall within the given geojson object.


### attach

`attach(vintage, in_list, fields, *layer)`

Input format: `['uuid1','uuid2']`

Returns a list of dict.

Attaches data attributes to a list of `uuid`s.

`layer` defaults to `locations`.


### locate

`locate(vintage, in_list, fields, *opt_tolerance, *parceldistancem, *neardistancem)`

Input format: `[{'sourcekey':'unique id','latitude':0,'longitude':0}]`

Returns a list of dict.

Automatically breaks up data into manageable geographic areas for calling the `locate` API across varying geographic areas.

Since the `locate` API can only operate on data that spans less than 10,000 square kilometers there is a trade off when breaking up data spatially. The locate function within these tools will assign data to h3_4's and then bulk process within each of those. This works very well for densely clustered data, but poorly for sparse disparate data.

To address the challenge of dealing with disparate data, the `opt_tolerance` value defaults to 0.5 and can be set between 0 and 1. At 0, no optimization to preserve credits is performed and the process will be the fastest. At 1, the process optimizes to preserve as many credits as possible by calling the `GET` variant of the `locate` API leading to slow run times but less credit usage.


### match

`match(vintage, in_list, maxsize=10, workers=16)`

Input format: Either `[{'sourcekey':'unique id','text':'unparsed address'}]` or `[{'sourcekey':'unique id','house_number':'house_number','road':'road','unit':'unit','city':'city','state':'state','postcode':'postcode'}]`

Returns a list of dict.

Performs address matching. Note that the `in_list` can be components or a full address.