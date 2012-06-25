# -*- coding:utf-8 -*-
"""
    flask.ext.optimize
    ~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Optimize module

    :copyright: (c) 2012 by Ian White.
    :license: BSD, see LICENSE for more details.
"""
import os
import os.path
import shlex
import subprocess
import sys
import shutil
import tempfile
import Image
from contextlib import contextmanager
from flask import current_app

_default_config = {
    'DEFAULT_DEST': 'min',
    'IMAGE_EXTENSIONS': ['jpg', 'jpeg', 'png', 'gif'],
    'STRIP_META': True
}

# Find the stack on which we want to store the optimizer.
# Starting with Flask 0.9, the _app_ctx_stack is the correct one,
# before that we need to use the _request_ctx_stack.
try:
    from flask import _app_ctx_stack as stack
except ImportError:
    from flask import _request_ctx_stack as stack


class OptimizerIndeterminableError(Exception):
    pass

class Optimize(object):

    def __init__(self, app=None):
        if app is not None:
            self.app = app
            self.init_app(self.app)
        else:
            self.app = None

    def init_app(self, app):
        for key, value in _default_config.items():
                    app.config.setdefault('OPTIMIZE_' + key, value)
        
        app.optimize = self
        
    def smush(self, file, output=None):
        """
        Optimizes a file
        """
        
        key = self.get_image_format(file)
        
        optimizer = get_optimizer(key)
        
        if not optimizer: 
            raise OptimizerIndeterminableError()
            
        optimizer.squish(file, output)
            
    def get_image_format(self, path):
        try:
            img = Image.open(path)
            current_app.logger.debug(path + ", " + img.format + ", " + ("%dx%d" % img.size) + ", " + img.mode)

            return img.format
        except IOError:
            current_app.logger.debug("Unable to determine file format ")
            
            






def common_path_prefix(paths, sep=os.path.sep):
    """os.path.commonpath() is completely in the wrong place; it's
    useless with paths since it only looks at one character at a time,
    see http://bugs.python.org/issue10395

    This replacement is from:
        http://rosettacode.org/wiki/Find_Common_Directory_Path#Python
    """
    def allnamesequal(name):
        return all(n==name[0] for n in name[1:])
    bydirectorylevels = zip(*[p.split(sep) for p in paths])
    return sep.join(x[0] for x in takewhile(allnamesequal, bydirectorylevels))


@contextmanager
def working_directory(path):
    """A context manager which changes the working directory to the given
    path, and then changes it back to its previous value on exit.

    Filters will often find this helpful.
    """
    prev_cwd = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(prev_cwd)


def make_option_resolver(clazz=None, attribute=None, classes=None,
                         allow_none=True, desc=None):
    """Returns a function which can resolve an option to an object.

    The option may given as an instance or a class (of ``clazz``, or
    duck-typed with an attribute ``attribute``), or a string value referring
    to a class as defined by the registry in ``classes``.

    This support arguments, so an option may look like this:

        cache:/tmp/cachedir

    If this must instantiate a class, it will pass such an argument along,
    if given. In addition, if the class to be instantiated has a classmethod
    ``make()``, this method will be used as a factory, and will be given an
    Environment object (if one has been passed to the resolver). This allows
    classes that need it to initialize themselves based on an Environment.
    """
    assert clazz or attribute or classes
    desc_string = ' to %s' % desc if desc else None

    def instantiate(clazz, env, *a, **kw):
        # Create an instance of clazz, via the Factory if one is defined,
        # passing along the Environment, or creating the class directly.
        if hasattr(clazz, 'make'):
            # make() protocol is that if e.g. the get_manifest() resolver takes
            # an env, then the first argument of the factory is the env.
            args = (env,) + a if env is not None else a
            return clazz.make(*args, **kw)
        return clazz(*a, **kw)

    def resolve_option(option, env=None):
        the_clazz = clazz() if callable(clazz) and not isinstance(option, type) else clazz

        if not option and allow_none:
            return None

        # If the value has one of the support attributes (duck-typing).
        if attribute and hasattr(option, attribute):
            if isinstance(option, type):
                return instantiate(option, env)
            return option

        # If it is the class we support.
        if the_clazz and isinstance(option, the_clazz):
            return option
        elif isinstance(option, type) and issubclass(option, the_clazz):
            return instantiate(option, env)

        # If it is a string
        elif isinstance(option, basestring):
            parts = option.split(':', 1)
            key = parts[0]
            arg = parts[1] if len(parts) > 1 else None
            if key in classes:
                return instantiate(classes[key], env, *([arg] if arg else []))

        raise ValueError('%s cannot be resolved%s' % (option, desc_string))
    resolve_option.__doc__ = """Resolve ``option``%s.""" % desc_string

    return resolve_option

            
            
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






            
class Optimizer(object):
    """
    Super-class for optimizers
    """

    __metaclass__ = RegistryMetaclass(
        clazz=lambda: Optimizer, attribute='squish',
        desc='an optimizer implementation')
    
    input_placeholder = "__INPUT__"
    output_placeholder = "__OUTPUT__"
    
    
    def __init__(self, **kwargs):
        # the number of times the _get_command iterator has been run
        self.quiet = kwargs.get('quiet')
        self.stdout = Scratch()
        self.stderr = Scratch()
    

    def _replace_placeholders(self, command, input, output):
        """
        Replaces the input and output placeholders in a string with actual parameter values
        """
        return command.replace(Optimizer.input_placeholder, input).replace(Optimizer.output_placeholder, output)
        
        
    def squish(self, path, output=None):
        """
        Optimizes an image
        """
        raise NotImplementedError()
        
        
    def _run(self, args):
        try:
            # retcode = subprocess.call(args, stdout=self.stdout.opened, stderr=self.stderr.opened)
            retcode = subprocess.call(args)
        except OSError:
            current_app.logger.error("Error executing command %s. Error was %s" % (command, OSError))

        if retcode != 0:
            # gifsicle seems to fail by the file size?
            # os.unlink(output)
            return False
        else :
            return True

                
    def _keep_smallest_file(self, input, output):
        """
        Compares the sizes of two files, and discards the larger one
        """
        input_size = os.path.getsize(input)
        output_size = os.path.getsize(output)

        # save the smaller file to the output path
        if (output_size > input_size):
            try:
                shutil.copyfile(input, output)
            except IOError:
                current_app.logger.error("Unable to copy %s to %s: %s" % (input, output, IOError))

        # delete the output file
        os.unlink(output)
        
get_optimizer = Optimizer.resolve


class PNGOptimizer(Optimizer):
    id = 'PNG'
    
    @classmethod
    def get_commands(cls, quiet=False):
        if quiet:
            pngcrush = 'pngcrush -rem alla -brute -reduce -q "__INPUT__" "__OUTPUT__"'
        else:
            pngcrush = 'pngcrush -rem alla -brute -reduce "__INPUT__" "__OUTPUT__"'
            
        return ('pngnq -n 256 -o "__OUTPUT__" "__INPUT__"', pngcrush)
        
    def squish(self, path, output=None):
        commands = self.get_commands(quiet=True)
        
        # OOPS!! Need to set the "path" to the optimized image so it gets processed again on each loop
        
        for command in commands:
            command = self._replace_placeholders(command, path, output)
            args = shlex.split(command)
            
            optimized = self._run(args)
            
            if optimized:
                # compare file sizes if the command executed successfully
                self._keep_smallest_file(path, output)
        
        
class JPGOptimizer(Optimizer):
    id = 'JPEG'
    
    @classmethod
    def get_commands(cls, strip_meta=True):
        if strip_meta:
            return ('jpegtran -outfile "__OUTPUT__" -optimise -copy none "__INPUT__"',
                'jpegtran -outfile "__OUTPUT__" -optimise -progressive "__INPUT__"')
        else:
            return ('jpegtran -outfile "__OUTPUT__" -optimise -copy all "__INPUT__"',
                'jpegtran -outfile "__OUTPUT__" -optimise -progressive -copy all "__INPUT__"')

    def squish(self, path, output=None):
        commands = self.get_commands(strip_meta=True)
        
        # OOPS!! Need to set the "path" to the optimized image so it gets processed again on each loop
        
        for command in commands:
            command = self._replace_placeholders(command, path, output)
            args = shlex.split(command)
            
            optimized = self._run(args)
            
            if os.path.getsize(output) > 10000:
                current_app.logger.warning("File is > 10kb - will be converted to progressive")
                continue
            else:
                if optimized:
                    # compare file sizes if the command executed successfully
                    self._keep_smallest_file(path, output)
                break
                

                




### scratch.py
import os, sys, tempfile

class Scratch (object):
    def __init__ (self):
        tup = tempfile.mkstemp()
        self._path = tup[1]
        self._file = os.fdopen(tup[0])        
        self._file.close()

    def __del__ (self):
        if self._path != None:
            self.destruct()

    def destruct (self):
        self.close()
        os.unlink(self._path)
        self._path = None
        self._file = None

    def close (self):
        if self._file.closed == False:
            self._file.flush()
            self._file.close()

    def read (self):
        if self._file.closed == True:
            self._reopen()
        self._file.seek(0)
        return self._file.read()

    def _reopen (self):
        self._file = open(self._path, 'w+')

    def getopened (self):
        self.close()
        self._reopen()
        return self._file
    opened = property(getopened, NotImplemented, NotImplemented, "opened file - read only")

    def getfile (self):
        return self._file
    file = property(getfile, NotImplemented, NotImplemented, "file - read only")
