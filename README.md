# cqazapi-pytools

* This is a python class providing easier access to CostQuest APIs.
* The APIs are documented at https://developer.costquest.com
* Documentation is available at https://costquestassociates.github.com/cqazapi-documentation

## Usage

To use the class, add it as a submodule to your project.
```bash
git submodule add https://github.com/costquestassociates/cqazapi-pytools
```

Then you can use it via an import.
```python
ch = importlib.import_module("cqazapi-pytools")
```

After that, you can access the functions. The functions of most interest are

### apiAction
`apiAction()`
This is used to make a single API call.

### apiBulkAction
`apiBulkAction()`
This will break up larger bulk requests into manageable parts as well as spawn concurrent workers to speed up retrieval.

### mergeList
`mergeList()`
This is a poor mans "join" of data. Given a single list of dictionaries, it will combine them on the chosen key.