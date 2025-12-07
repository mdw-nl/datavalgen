# Datavalgen

### Why?

In healthcare federated learning projects, each site typically prepares their
own dataset, and the federated algorithms assume a shared data model: same
column names, same types, same allowed values, etc. That assumption can be fragile.
Data can come from complex EHR pipelines that vary from center etc. resulting in
differences in the "format" of the data.

Due to the nature of federated learning in this context, it's hard to detect
this lack of "data homogeniety" before it might be too late (algorithm has run,
crashed, shared incorrect or privacy-breaking partial results).

It's also easier to write privacy-preserving and correct federated algorithms if
assumptions about the format of the data the algorithm will encounter can be
made.

Hence, there is a need to validate the data before it's ready for federation.
This tool aims to provide a common way of doing that. It can be given a pydantic
model and a csv, and report errors to the user locally. It can also be run as a
vantage6 "algorithm", report only the number of errors in that case.

### What is it?

It's a very simple "tool". Aim is just to make it easier for projects to
validate (and generate) their data by providing a common way of doing it – write
a pytdantic model, using `datavalgen`, package it in a docker image, etc.

So, `datavalgen` goal is to:
* Provide a familiar way of validating data against a model (pydantic) –
  Same (nice-enough) format for validation errors reporting.
* Familiar way of generating fake data
* (Maybe, future) "Standard" say of running local analysis on data

### How?

This is done by (ab)using entry-points in python. `datavalgen` will look for
[python
entry-points](https://packaging.python.org/en/latest/specifications/entry-points/)
under certain group names to find the "plugins" mentinoed below.

Plugins:
* `model`: plugins registered under this name provide a model (class, pydantic) that
  can be used to validate (`datavalgen validate`, or via vantage6) a data file.
* `factory`: can be used to generate fake data (class extending `BaseDataModelFactory`)
* `analysis`: can be used to perform additional checks (e.g. statistical checks)
  that don't make sense to inlcude as part of validation. In validation you
  probably only want to take a look at one row at the time. In analysis you can
  look at all the data at the same time (distribution of a column, mean, etc.)

The way to develop these plugins is by creating a python package and then
registring the entry points in your pyproject.toml. Something like:

```toml
# datavalgen contract: entrypoints for models and factories and homepage url
# `model` entrypoints
[project.entry-points."datavalgen.models"]
example = "datavalgen_model_example.model:DataModel"
# `factory` entrypoints
[project.entry-points."datavalgen.factories"]
example = "datavalgen_model_example.factory:DataModelFactory"
[project.urls]
Homepage = "https://github.com/mdw-nl/datavalgen-model-example"
```

Then, `datavalgen` will be able to find which models, for example, are available
for validation. In this case, it will know that `example` refers to the model
(python class) `DataModel` declared in package `datavalgen_model_example`,
module `model`.

```
$ datavalgen validate --list
List of datavalgen models installed:
  model   | package                  | homepage
  ------- | ------------------------ | --------
  example | datavalgen-model-example | https://github.com/mdw-nl/datavalgen-model-example
```
```
$ datavalgen validate -m example -d examplehere.csv
✅ No validation errors found.
```

### Dockerization

To make it easier, folks writing models for validation can package their model
and datavalgen in a docker image, so sites can just `docker run` to validate
their data. `datavalgen validate` 

The same docker image can be used for a vantage6 "task".


### Example usage

TODO
