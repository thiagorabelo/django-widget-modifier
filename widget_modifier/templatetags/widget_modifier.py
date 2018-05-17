import os

from django.template import Library
from django.utils import six


register = Library()


_object_getattr = object.__getattribute__
_object_setattr = object.__setattr__


@six.python_2_unicode_compatible
class _BoundFieldProxy(object):
    __slots__ = ['_the_field', '_the_attrs']

    def __init__(self, field, attrs=None):
        try:
            # pylint: disable=W0212
            field_ = field._the_field
            attrs_ = field._the_attrs
            attrs_.update(attrs or {})
        except AttributeError:
            field_ = field
            attrs_ = attrs
            # TODO: It's always appending
            attrs_.update(field.field.widget.attrs or {})

        _object_setattr(self, '_the_field', field_)
        _object_setattr(self, '_the_attrs', attrs_)

    def __str__(self):
        original_field = self._the_field
        return original_field.__class__.__str__(self)

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        attrs_ = self._the_attrs

        if isinstance(attrs, dict):
            attrs_.update(attrs)

        return self._the_field.as_widget(widget=widget,
                                         attrs=attrs_,
                                         only_initial=only_initial)

    def __getattr__(self, name):
        field = self._the_field
        return getattr(field, name)

    def __setattr__(self, name, value):
        return _object_setattr(self._the_field, name, value)

    if os.environ.get('DEV_WIDGET_MODIFIER'):
        def __del__(self):
            print("I'm dying...")


@register.filter
def attr(field, attr_):
    try:
        attribute, value = attr_.split(':', 1)
    except ValueError:
        attribute, value = attr_, ''

    return _BoundFieldProxy(field, {attribute: value})


@register.filter
def add_class(field, classes):
    return _BoundFieldProxy(field, {'class': classes})


@register.filter
def append_class(field, classes):
    try:
        # pylint: disable=W0212
        attrs = field._the_attrs
    except AttributeError:
        attrs = field.field.attrs

    attrs['class'] = attrs.get('class', '') + ' ' + classes

    return _BoundFieldProxy(field, attrs)
