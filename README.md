# drf-fullclean
![PyPI - Version](https://img.shields.io/pypi/v/drf-fullclean)
![PyPI - Downloads](https://img.shields.io/pypi/dm/drf-fullclean)

**Call django Model.full_clean(exclude=None, validate_unique=True) when invoke serializer.is_valid() of ModelSerializer**

### Django Rest Framework 3 Design
https://www.django-rest-framework.org/community/3.0-announcement/#differences-between-modelserializer-validation-and-modelform
### Differences between ModelSerializer validation and ModelForm.
> This change also means that we no longer use the .full_clean() method on model instances, but instead perform all validation explicitly on the serializer. This gives a cleaner separation, and ensures > that there's no automatic validation behavior on ModelSerializer classes that can't also be easily replicated on regular Serializer classes.

### Discussions
https://github.com/encode/django-rest-framework/discussions/7850

## Warning!
1. One ModelSerializer -> Use this library.
2. Multiple ModelSerializer -> [PLEASE READ ME](https://github.com/giuseppenovielli/drf-fullclean/discussions/4)

## Installation
```
pip install drf-fullclean
```

## Configuration
Add the following code into settings.py
```
DRF_FULL_CLEAN = {
    "DEBUG" : False #set True if you want to see debug print
}
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
  


