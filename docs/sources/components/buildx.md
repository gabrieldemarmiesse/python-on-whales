### bake


```python
docker.buildx.bake(targets, cache=True, load=False, pull=False, push=False)
```


----

### build


```python
docker.buildx.build(
    context_path,
    file=None,
    network=None,
    cache=True,
    platform=None,
    progress="auto",
    pull=False,
    push=False,
    target=None,
    tags=[],
)
```


A `python_on_whales.Image` is returned, even when using multiple tags.
That is because it will produce a single image with multiple tags.


----

### create


```python
docker.buildx.create(context_or_endpoint=None, use=False)
```


----

### remove


```python
docker.buildx.remove(builder)
```


----

### use


```python
docker.buildx.use(builder, default=False, global_=False)
```


----

