# -*- coding: utf-8 -*-
from django.db.models import fields
from django_testdata import generators


class AutoFixture(object):
    overwrite_defaults = False
    follow_fks = False
    generate_fks = False

    none_chance = 0.2

    field_to_generator = {
        fields.BooleanField: generators.BooleanGenerator,
        fields.DateField: generators.DateGenerator,
        fields.IntegerField: generators.IntegerGenerator,
        fields.PositiveIntegerField: generators.PositiveIntegerGenerator,
        fields.IPAddressField: generators.IPAddressGenerator,
    }

    def __init__(self, model,
            field_values=None, none_chance=None,
            overwrite_defaults=None, follow_fks=None, generate_fks=None):
        '''
        Parameters:
            ``model``: 

            ``field_values``: A dictionary with field names of ``model`` as
                keys. Values may be static values that are assigned to the
                field or a ``Generator`` instance that generates a value on the
                fly.

            ``overwrite_defaults``: All default values of fields are preserved
                by default. If set to ``True``, default values will be
                generated by a matching ``Generator``.
        '''
        self.model = model
        self.field_values = field_values or {}
        if none_chance is not None:
            self.none_chance = none_chance
        if overwrite_defaults is not None:
            self.overwrite_defaults = overwrite_defaults
        if follow_fks is not None:
            self.follow_fks = follow_fks
        if generate_fks is not None:
            self.generate_fks = generate_fks

    def get_generator(self, field):
        '''
        Get a field and return value generator.
        To ignore the field, return ``None``.
        '''
        if isinstance(field, fields.AutoField):
            return None
        if field.default is not fields.NOT_PROVIDED and \
            not self.overwrite_defaults:
                return None
        kwargs = {}
        if field.null:
            kwargs['none_chance'] = self.none_chance
        if field.choices:
            return generators.ChoicesGenerator(choices=field.choices, **kwargs)
        elif isinstance(field, fields.EmailField):
            return generators.EmailGenerator(max_length=field.max_length, **kwargs)
        elif isinstance(field, fields.CharField):
            if field.blank:
                min_length = 0
            else:
                min_length = 1
            return generators.StringGenerator(
                min_length=min_length,
                max_length=field.max_length)
        elif isinstance(field, fields.DecimalField):
            return generators.DecimalGenerator(
                decimal_places=field.decimal_places,
                max_digits=field.max_digits)
        # DateTimeField is checked here explicitly because its a subclass of
        # DateTimeField and would cause problems if used in the
        # field_to_generator dictionary
        if isinstance(field, fields.DateTimeField):
            return generators.DateTimeGenerator(**kwargs)
        if isinstance(field, fields.BigIntegerField):
            return generators.IntegerGenerator(
                min_value=-field.MAX_BIGINT - 1,
                max_value=field.MAX_BIGINT,
                **kwargs)
        for field_class, generator in self.field_to_generator.items():
            if isinstance(field, field_class):
                return generator(**kwargs)
        return None

    def create(self, count=1, commit=True):
        '''
        Create and return ``count`` model instances.
        '''
        object_list = []
        for i in xrange(count):
            instance = self.model()
            for field in instance._meta.fields:
                generator = self.get_generator(field)
                if generator is None:
                    continue
                value = generator.get_value()
                setattr(instance, field.name, value)
            if commit:
                instance.save()
            object_list.append(instance)
        return object_list