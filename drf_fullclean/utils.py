def remove_many_to_many(serializer, validated_data, **kwargs):
    for field in serializer.Meta.model._meta.many_to_many:
        if field.name in validated_data:
            del validated_data[field.name]
    return validated_data