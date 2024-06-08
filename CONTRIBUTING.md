# Contributing to Python-on-whales

You want to make Python-on-whales better? Great! Help is always welcomed!

In this document, we'll try to explain how this package works internally and how you can 
contribute to it.

First things first, if it's your first pull request to an open-source project, head to
https://github.com/firstcontributions/first-contributions. This guide will explain 
how to open a pull request in a github repository that you don't own.

## Building the docs

All docstring are fetched and put in templates. Everything is done in markdown, 
with the help of [mkdocstrings](https://mkdocstrings.github.io/) and
[mkdocs](https://www.mkdocs.org/).

#### First install the dependencies:

```
pip install -r docs/requirements.txt
```

#### Generate the documentation files and serve them
```
cd ./docs/
python autogen.py && mkdocs serve
```

#### Open your browser

http://localhost:8000


## Running the tests

Install all dependencies and install python-on-whales in editable mode:
```
pip install -r requirements.txt -r tests/test-requirements.txt
pip install -e ./
```

Then:

```bash
pytest -v ./tests/
```


## Exploring the codebase

The sources are in the `python_on_whales` directory. Everytime a class has something to 
do with the Docker daemon, a `client_config` attribute is there and must be passed around.

This `client_config` tells the Docker CLI how to connect to the daemon. 
You can think of it of the collection of all the arguments that are at the start of the CLI.
For example `docker -H ssh://my_user@my_ip ...`.

Each sub-component of the CLI is in a separate directory. 

#### Component structure

The structure is the following for calling `docker image ...`.

`ImageCLI` is in charge of calling the `docker image` commande. This class appears when you call
```python
from python_on_whales import docker
print(docker.image)
```
`ImageCLI` is in `python_on_whales/components/image/cli_wrapper.py`.

`Image` is in charge of holding all the metadata of a Docker image and has all 
the attributes that you could find by doing `docker image inspect ...`.

It has some methods for convenience. For example:

```python
from python_on_whales import docker

my_ubuntu = docker.pull("ubuntu")

my_ubuntu.remove()
# is the same as
docker.image.remove(my_ubuntu)
```

Since `Image` has all the information you can find with `docker image inspect ...`, we need 
to parse the json output. All parsing models are found in `python_on_whales/components/image/models.py`.

## Some coding rules that are not enforced by the CI:

#### Create a diff that only changes the visual representation of the code
Do not make a diff just to change the code style of something. This diff will get rejected if you do it.
As an example, those kind of diff will get rejected during code reviews:

```diff
- my_list += other_list
+ my_list.extends(other_list)

- if my_list == []:
+ if len(my_list) == 0:

- for i in range(10):
-     if ...:
-         my_list.append(...)
+ my_list = [... for i in range(10) if ...]
```

If the diff lowers the complexity of the statement by using less operations/functions, then it's ok. For 
example, this kind of diff is welcome:

```
- for element in my_list:
-     old_list.append(element)
+ old_list.extends(my_list)
```

This is to ensure that, as maintainers, we have a little code to review as possible. The first programmer
who writes a line of code chooses the style. If you need to change a line for another reason than the code style,
then you can change the code style.

#### Do not modify a mutable argument of a function, unless it's `self`

Because it's usually unexpected for the caller and causes unexpected side-effects

Not ok:
```python
def do_something(input_list):
    input_list.append(...)
    ...
```
if you really need it, either:
* Copy the input argument so that the caller doesn't have any side effect `ìnput_list = copy(input_list)`
* Make a class and a method `self.input_list.append(...)`

#### All methods should have types in their signature (arguments and return type)
You don't have to type the local variables.

If you believe a reviewer asked you to comply to a rule that wasn't specified here or in the CI, feel free to raise an issue. There should be no implicit rule when reviewing.
