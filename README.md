# drf-fullclean
![PyPI - Version](https://img.shields.io/pypi/v/drf-fullclean)
![PyPI - Downloads](https://img.shields.io/pypi/dm/drf-fullclean)

**Call django Model.full_clean(exclude=None, validate_unique=True) when invoke serializer.is_valid() of ModelSerializer**


## Installation
```
pip install drf-fullclean
```

## Usage
```
from drf_fullclean.serializers import FullCleanModelSerializer

class MyModelSerializerClass(FullCleanModelSerializer):
  class Meta:
      model = MyModel
      fields = '__all__
```

```
s = MyModelSerializerClass(data=request.POST)
s.is_valid(raise_exception=True)
s.save()
```
When you call `s.is_valid(raise_exception=True)` this method invoke also Model.full_clean() method.

**The validation FAIL IF Model.full_clean() FAIL.**

## API
`is_valid()` is extended with Model.full_clean() api.

```
is_valid(self, raise_exception=False, exclude=None, validate_unique=True, extra_include=None, *args, **kwargs)
```
  + [raise_exception=False](https://www.django-rest-framework.org/api-guide/serializers/#raising-an-exception-on-invalid-data)
  + [exclude=None](https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean)
  + [validate_unique=True](https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean)
  + [extra_include=None](https://github.com/giuseppenovielli/drf-fullclean/discussions/4)
  


