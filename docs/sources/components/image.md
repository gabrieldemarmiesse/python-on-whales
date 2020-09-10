### list


```python
docker.image.list()
```


----

### load


```python
docker.image.load(input, quiet=False)
```


----

### pull


```python
docker.image.pull(image_name, quiet=False)
```


Pull a docker image

__Arguments__

- __image_name__ `str`: The image name
- __quiet__ `bool`: If you don't want to see the progress bars.


----

### push


```python
docker.image.push(tag_or_repo, quiet=False)
```


----

### remove


```python
docker.image.remove(x)
```


----

### save


```python
docker.image.save(images, output=None)
```


----

### tag


```python
docker.image.tag(source_image, new_tag)
```


----

