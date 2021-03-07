# Contributing to Python-on-whales

You want to make Python-on-whales better? Great! Help is always welcomed!

In this document, we'll try to explain how this package works internally and how you can 
contribute to it.

First things first, if it's your first pull request to an open-source project, head to
https://github.com/firstcontributions/first-contributions. This guide will explain 
how to open a pull request in a github repository that you don't own.

## Building the docs

All docstring are fetched and put in templates. Everything is done in markdown, 
with the help of [keras-autodoc](https://gabrieldemarmiesse.github.io/keras-autodoc/) and
[mkdocs](https://www.mkdocs.org/).

#### First install the dependencies:

```
pip install keras-autodoc mkdocs
```

#### Generate the documentation files and serve them
```
cd ./docs/
python autogen.py && mkdocs generate
```

### Open your browser

http://localhost:8000
