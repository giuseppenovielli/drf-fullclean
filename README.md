# drf-fullclean
Call django model full_clean() when validate ModelSerializer

## Installation
```
pip install drf-fullclean
```

## Usage
```
s = ModelSerializerClass(data=request.POST)
s.is_valid(raise_exception=True)
s.save()
```
When you call `s.is_valid(raise_exception=True)` this method invoke also Model.full_clean() method.

The validation FAIL IF Model.full_clean() FAIL.

## API
`is_valid()` is extended with model.full_clean() api.

```
serializer_obj.is_valid(self, raise_exception=False, include=None, validate_unique=True, *args, **kwargs)
```
  + [raise_exception=False](https://www.django-rest-framework.org/api-guide/serializers/#raising-an-exception-on-invalid-data)
  + [validate_unique=True](https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean)
  + [include=None](https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean)
    + This parameter accept a type of `dict`: `{'model_field_name' : instance_obj}` and perform `exclude=None` method to Model.full_clean() api.
    + If you want to perform `Model.full_clean()` you must have the model instance with ALL FIELD POPULATED.
    + Into some scenario, for example, when you try to save nested instance, some ForeignKey are None. So before validate you must create an instance of this ForeignKey without save into db and pass it into `include=None` parameter. This action exclude it, by `Model.full_clean()` validation, but not from `Model.clean()` method. A ForeignKey with pk=None can't be validated by `Model.clean_field()` method.
  


