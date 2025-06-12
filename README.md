# cqazapi-usertools

* This is a python class providing easier access to CostQuest APIs.
* The APIs are documented at https://developer.costquest.com
* Documentation is available at https://costquestassociates.github.com/cqazapi-documentation

## Usage

To use the class, add it as a submodule to your project.
```bash
git submodule add https://github.com/costquestassociates/cqazapi-usertools
```

Then you can use it via an import.
```python
ch = importlib.import_module("cqazapi-helpers")
```

After that, you can access the functions. There are three functions of utility:

1. `apiAction()