def RegistryMetaclass(clazz=None, attribute=None, allow_none=True, desc=None):
    """Returns a metaclass which will keep a registry of all subclasses, keyed
    by their ``id`` attribute.

    The metaclass will also have a ``resolve`` method which can turn a string
    into an instance of one of the classes (based on ``make_option_resolver``).
    """
    def eq(self, other):
        """Return equality with config values that instantiate this."""
        return (hasattr(self, 'id') and self.id == other) or\
               id(self) == id(other)
    def unicode(self):
        return "%s" % (self.id if hasattr(self, 'id') else repr(self))

    class Metaclass(type):
        REGISTRY = {}

        def __new__(mcs, name, bases, attrs):
            if not '__eq__' in attrs:
                attrs['__eq__'] = eq
            if not '__unicode__' in attrs:
                attrs['__unicode__'] = unicode
            if not '__str__' in attrs:
                attrs['__str__'] = unicode
            new_klass = type.__new__(mcs, name, bases, attrs)
            if hasattr(new_klass, 'id'):
                mcs.REGISTRY[new_klass.id] = new_klass
            return new_klass

        resolve = staticmethod(make_option_resolver(
            clazz=clazz,
            attribute=attribute,
            allow_none=allow_none,
            desc=desc,
            classes=REGISTRY
        ))
    return Metaclass