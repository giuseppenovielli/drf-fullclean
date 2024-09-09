from django.conf import settings
from django.forms.models import model_to_dict

def remove_many_to_many(serializer, validated_data, **kwargs):
    for field in serializer.Meta.model._meta.many_to_many:
        if field.name in validated_data:
            del validated_data[field.name]
    return validated_data


# DEBUG
def print_debug(message):
    drf_full_clean = getattr(settings, 'DRF_FULL_CLEAN', {})
    if not drf_full_clean.get('DEBUG', False):
        return
    print('\nDRF_FULL_CLEAN -> {}'.format(message))
    
    
def instance_to_dict(instance):
    value_to_dict = None
    try:
        value_to_dict = model_to_dict(instance)
    except:
        try:
            value_to_dict = instance.__dict__
        except:
            pass
    return value_to_dict