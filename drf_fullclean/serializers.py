# -*- coding: utf-8 -*-
"""
Giuseppe Novielli 2024 (Copyright) 
https://www.github.com/giuseppenovielli/ 

https://www.django-rest-framework.org/community/3.0-announcement/#differences-between-modelserializer-validation-and-modelform
https://github.com/encode/django-rest-framework/discussions/7850#discussioncomment-8380135
"""
from copy import deepcopy

from django.utils.translation import ugettext_lazy as _
from django.db.models.fields.reverse_related import ManyToManyRel

from django.core.exceptions import ValidationError as DjangoValidationError, FieldDoesNotExist
from rest_framework import serializers

from .utils import instance_to_dict, print_debug, remove_many_to_many
                    

class FullCleanModelSerializer(serializers.ModelSerializer):
    def is_valid(self, raise_exception=False, exclude=None, validate_unique=True, extra_include=None, *args, **kwargs):
        """
        Invoke ModelSerializer.is_valid() and call Model.full_clean()

        Args:
            raise_exception (bool, optional): https://www.django-rest-framework.org/api-guide/serializers/#raising-an-exception-on-invalid-data Defaults to False.
            exclude (list, optional): https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean Defaults to None.
            validate_unique (bool, optional): https://docs.djangoproject.com/en/3.2/ref/models/instances/#django.db.models.Model.full_clean Defaults to True.
            extra_include (dict, optional): https://github.com/giuseppenovielli/drf-fullclean/discussions/4 Defaults to None.

        Returns:
            bool: Return True if valid, False otherwise
        """
        print_debug('FullCleanModelSerializer is_valid -> {}'.format(self.Meta.model)) 
        
        is_valid = super().is_valid(raise_exception=raise_exception)
        if not is_valid:
            return is_valid

        is_valid = self.is_valid_model(raise_exception=raise_exception, 
                                   exclude=exclude, validate_unique=validate_unique, 
                                   extra_include=extra_include, 
                                   *args, **kwargs)

        print_debug('---------')
        return is_valid
        
    
    def is_valid_model(self, raise_exception=False, exclude=None, validate_unique=True, extra_include=None, *args, **kwargs):
        if extra_include and not isinstance(extra_include, dict):
            raise TypeError('Expected dict for argument "extra_include", but got: %r' % extra_include)
        
        self._instance_fullclean = None
        
        obj = self.model_instance(self.Meta.model, self.get_validated_data(), self.get_instance_update_to_fullclean(), self.partial, extra_include, **kwargs)
        
        print_debug('is_valid_model -> Instance To FullClean -> {} -- {}'.format(type(obj), instance_to_dict(obj)))
        errors = self.model_validation(obj, exclude, validate_unique, extra_include, **kwargs)
        
        if errors and raise_exception:
            raise serializers.ValidationError(detail=errors)
        return not errors
    
    
    #
    
    # Validated Data
    def get_validated_data(self):
        validated_data = deepcopy(self.validated_data)
        validated_data = remove_many_to_many(self, validated_data)
        return validated_data
    #
    
    #INSTANCE
    def get_instance_update_to_fullclean(self):
        if self._instance_fullclean:
            return self._instance_fullclean
        
        i = self.instance
        if not i:
            return 
        
        # Not use the original instance, the layer FullCleanModelSerializer is completely trasparent, not modifying the original instances
        self._instance_fullclean = i = deepcopy(i)
        return i

    
    def model_instance(self, model_class, validated_data, instance=None, partial=False, extra_include=None, **kwargs):
        print_debug('model_instance -> validated_data -> {}'.format(validated_data))
        if not instance:
            return self.model_instance_create(model_class, validated_data, extra_include, **kwargs)
        return self.model_instance_update(model_class, validated_data, instance, partial, extra_include, **kwargs)
    
    
    def add_extra_include_to_instance(self, instance, extra_include, **kwargs):
        if not instance:
            return
        
        #Add fields value that are not in validated_data
        if extra_include:
            for key,value in extra_include.items():
                
                # Skip ManyToManyRel
                field = instance._meta.get_field(key)
                if isinstance(field, ManyToManyRel):
                    continue
                
                setattr(instance, key, value)
                
        return instance
    
    # CREATE
    def create_instance(self, model_class, validated_data, **kwargs):
        return model_class(**validated_data)
    
    
    def model_instance_create(self, model_class, validated_data, extra_include=None, **kwargs):
        i = self.create_instance(model_class, validated_data)
        i = self.add_extra_include_to_instance(i, extra_include)    
        return i
        
    
    # UPDATE
    def update_instance(self, instance, validated_data, partial=False, **kwargs):
        if not instance:
            return
        
        for field in instance._meta.fields:
            if field.name not in validated_data:
                continue
            setattr(instance, field.name, validated_data[field.name])
        return instance
            
        
    
    def model_instance_update(self, model_class, validated_data, instance, partial=False, extra_include=None, **kwargs):
        i = self.update_instance(instance, validated_data, partial, **kwargs)
        i = self.add_extra_include_to_instance(i, extra_include, **kwargs)
        return i
    
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
    
    def get_can_include_field(self, field, value):
        # Check if a field with value can be added to instance
        if isinstance(field, ManyToManyRel):
            return True
        
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
                that validators need'.format(field.name))
        return True
                  
    
    def can_remove_field_from_excluded_list(self, field, value):
        if not field.is_relation:
            return True
        
        # Check if a field is a relation with a database id, can be removed from excluded list
        return value.pk and value.id   
    
                        
    def get_exclude(self, instance, exclude=None, extra_include=None, **kwargs):
        fields_to_exclude = self._get_validation_exclusions(self.get_instance_update_to_fullclean())
        print_debug('get_exclude -> serializer fields excluded -> {}'.format(fields_to_exclude))
        
        print_debug('get_exclude -> model exclude -> {}'.format(exclude))
        if exclude:
            fields_to_exclude.extend(exclude)
        
        
        if extra_include:
            for key, value in extra_include.items():
                try:
                    field = instance._meta.get_field(key)
                    
                    can_include = self.get_can_include_field(field, value)
                    if not can_include:
                        continue
                    
                    can_remove_field_from_excluded_list = self.can_remove_field_from_excluded_list(field, value)
                    if not can_remove_field_from_excluded_list:
                        fields_to_exclude.append(key)
                    else:
                        try:
                            fields_to_exclude.remove(key)
                        except ValueError:
                            pass  # do nothing!
                        
                except FieldDoesNotExist:
                    pass
        
        exclude = list(set(fields_to_exclude))
        print_debug('get_exclude -> model full_clean exclude final -> {}'.format(exclude))
        
        return exclude
    
    def model_validation_method(self, instance, exclude=None, validate_unique=True, extra_include=None, **kwargs):
        l = []
        if extra_include:
            for key, value in extra_include.items():
                l.append({key: instance_to_dict(value)})
        print_debug('model_validation_method -> extra include -> {}'.format(l))
        
        
        exclude = self.get_exclude(instance, exclude, extra_include, **kwargs)
        
        print_debug('model_validation_method -> Invoke Model.full_clean() -> {} -- {}'.format(type(instance), instance_to_dict(instance)))
        instance.full_clean(exclude=exclude, validate_unique=validate_unique)
        
        
        
    def model_validation(self, object, exclude=None, validate_unique=True, extra_include=None, **kwargs):
        try:
            self.model_validation_method(object, exclude, validate_unique, extra_include, **kwargs)
        except DjangoValidationError as exc:
            return serializers.as_serializer_error(exc)