# cqazapi-pytools

* This is a python class providing easier access to CostQuest APIs.
* API definitions are at https://developer.costquest.com
* Documentation is available at https://costquestassociates.github.io/cqazapi-documentation



## Usage

To use the class, add it as a submodule to your project.
```bash
git submodule add https://github.com/costquestassociates/cqazapi-pytools
```

Then you can use it via an import. After that, you can access the functions after instantiating the class.
```python
import importlib
cqpt = importlib.import_module("cqazapi-pytools")

cp = cqpt.cqazapipytools(apikey)
response = cp.apiAction('https://api.costquest.com/fabric/vintages', 'GET')
print(response)
```

To update the submodule
```bash
git submodule update --init --remote
```



## Functions

### apiAction

`apiAction(url, method, body)`

This is used to make a single API call.

* `method` is `GET` or `POST`.
* `body` is a python object being of type `list` or `dict` mirroring the JSON types of `array` and `object`.


### apiBulkAction

`apiBulkAction(url, method, in_list, *maxsize, *workers)`

This will break up larger bulk requests into manageable parts as well as spawn concurrent workers to speed up retrieval.

* `in_list` must be a list of items. It can be of any size.
* `maxsize` is the maximum number of items to request at once to an API. It defaults to 1,000.
* `workers` is the number of parallel requests to perform. It defaults to 4.


### mergeList

`mergeList(in_list, property_name)`

This is a poor mans "join" of data. Given a single list of dictionaries, it will combine them on the chosen property based on dictionary keys.

* `in_list` must be of type `list` and it must contain entries of type `dict`.
* `property_name` must be a key present in all dictionaries in the `in_list`.

An example of this would be passing in two lists with dictionaries at a `location_id` level that you want a single list of dictionaries with one location_id but all properties in the resulting dictionary for each id.


### collect

`collect(vintage, geojson)`

Returns all fabric `uuids` that fall within the given geojson object.


### attach

`attach(vintage, in_list, fields)`

Attaches fabric data to a list of ids.