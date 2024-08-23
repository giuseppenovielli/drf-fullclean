from rest_framework import serializers

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from django.core.exceptions import ValidationError as DjangoValidationError, FieldDoesNotExist

from django.forms.models import model_to_dict

# DEBUG
def print_debug(message):
    drf_full_clean = getattr(settings, 'DRF_FULL_CLEAN', {})
    if not drf_full_clean.get('DEBUG', False):
        return
    print(message)

class FullCleanModelSerializer(serializers.ModelSerializer):
    """
    Giuseppe Novielli 2024 (Copyright) 
    https://www.github.com/giuseppenovielli/ 
    
    https://www.django-rest-framework.org/community/3.0-announcement/#differences-between-modelserializer-validation-and-modelform
    https://github.com/encode/django-rest-framework/discussions/7850#discussioncomment-8380135
    """
    def is_valid(self, raise_exception=False, exclude=None, validate_unique=True, extra_include=None, *args, **kwargs):
        print_debug('\nFullCleanModelSerializer is_valid -> {}'.format(self.Meta.model)) 
        
        is_valid = super().is_valid(raise_exception=raise_exception)
        if not is_valid:
            return is_valid

        return self.is_valid_model(raise_exception=raise_exception, 
                                   exclude=exclude, validate_unique=validate_unique, 
                                   extra_include=extra_include, 
                                   *args, **kwargs)
        
    
    def is_valid_model(self, raise_exception=False, exclude=None, validate_unique=True, extra_include=None, *args, **kwargs):
        if extra_include and not isinstance(extra_include, dict):
            raise TypeError('Expected dict for argument "extra_include", but got: %r' % extra_include)
        
        obj = self.model_instance(self.Meta.model, self.validated_data, self.instance, self.partial, extra_include, **kwargs)
        
        print('Instance to FullClean -> {}'.format(model_to_dict(obj)))
        if obj:
            errors = self.model_validation(obj, exclude, validate_unique, extra_include, **kwargs)
        else:
            raise Exception('Nested serializers are not supported.')
        
        if errors and raise_exception:
            raise serializers.ValidationError(detail=errors)
        return not errors
    
    
    #
    
    #INSTANCE
    def model_instance(self, model_class, validated_data, instance=None, partial=False, extra_include=None, **kwargs):
        if not instance:
            return self.model_instance_create(model_class, validated_data, extra_include, **kwargs)
        return self.model_instance_update(model_class, validated_data, instance, partial, extra_include, **kwargs)
    
    
    def model_instance_create(self, model_class, validated_data, extra_include=None, **kwargs):

        try:
            i = model_class(**validated_data)
        except:
            return
        
        #Add fields value that are not in validated_data
        if extra_include:
            for key,value in extra_include.items():
                setattr(i, key, value)
                
        return i
        
    
    
    def model_instance_update(self, model_class, validated_data, instance, partial=False, extra_include=None, **kwargs):
        try:
            for field in instance._meta.fields:
                if field.name not in validated_data:
                    continue
                setattr(instance, field.name, validated_data[field.name])
        except:
            return
        
        #Add fields value that are not in validated_data
        if extra_include:
            for key,value in extra_include.items():
                setattr(instance, key, value)
        return instance
        
    
    #
    
    #VALIDATION
    def _get_validation_exclusions(self, instance=None):
        """
        Return a list of field names to exclude from model validation.
        https://github.com/encode/django-rest-framework/blob/2.4.8/rest_framework/serializers.py#L939C5-L956C26
        """
        # cls = self.opts.model
        cls = self.Meta.model
        opts = cls._meta.concrete_model._meta
        exclusions = [field.name for field in opts.fields + opts.many_to_many]

        for field_name, field in self.fields.items():
            field_name = field.source or field_name
            if (
                field_name in exclusions
                and not field.read_only
                and (field.required or hasattr(instance, field_name))
                and not isinstance(field, serializers.Serializer)
            ):
                exclusions.remove(field_name)
        return exclusions
    
    
    def model_validation_method(self, object, exclude=None, validate_unique=True, extra_include=None, **kwargs):        
        fields_to_exclude = self._get_validation_exclusions(self.instance)
        print_debug('serializer fields excluded -> {}'.format(fields_to_exclude))
        
        if exclude:
            fields_to_exclude.extend(exclude)
        
        print_debug('model exclude -> {}'.format(exclude))
        
        if extra_include:
            for key, value in extra_include.items():
                try:
                    field = object._meta.get_field(key)
                    fields_to_exclude.append(key)
                    
                    if (
                            field.is_relation 
                            and 
                            bool(field.validators) 
                            and 
                            (
                                value.pk is None 
                                or 
                                value.id is None
                            )
                        ):
                        raise Exception('Unsupported validation! Field {} is a relation that contains validators that needs the database id. \
                            Try to move validations\'s logic into clean() method, but analize object\'s fields instead make a query to the database, \
                            that validators need'.format(key))
                        
                except FieldDoesNotExist:
                    pass
        
        exclude = list(set(fields_to_exclude))
        print_debug('model full_clean exclude final -> {}'.format(exclude))
        
        l = []
        if extra_include:
            for key, value in extra_include.items():
                l.append({key: model_to_dict(value)})
        print_debug('extra include -> {}'.format(l))
            
        object.full_clean(exclude=exclude, validate_unique=validate_unique)
        
        
        
        
    def model_validation(self, object, exclude=None, validate_unique=True, extra_include=None, **kwargs):
        try:
            self.model_validation_method(object, exclude, validate_unique, extra_include, **kwargs)
        except DjangoValidationError as exc:
            return serializers.as_serializer_error(exc)