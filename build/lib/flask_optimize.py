# -*- coding:utf-8 -*-
"""
    flask.ext.optimize
    ~~~~~~~~~~~~~~~~~~~~~~~

    Flask-Optimize module

    :copyright: (c) 2012 by Ian White.
    :license: BSD, see LICENSE for more details.
"""
from flask import current_app
from optimizer import get_optimizer

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
        
        # self.smusher = smush.Smush(strip_jpg_meta=app.config['SMUSH_STRIP_META'], exclude=app.config['SMUSH_EXCLUDE_EXTENSIONS'], list_only=app.config['SMUSH_LIST_ONLY'], quiet=True, identify_mime=True)
        
        app.optimize = self
        
    def optimize(self, file, output=None):
        """
        Optimizes a file
        """
        key = self.get_image_format(file)
            
    def get_image_format(path):
        try:
            img = Image.open(path)
            current_app.logger.debug(path + ", " + img.format + ", " + ("%dx%d" % img.size) + ", " + img.mode)

            return img.format
        except IOError:
            current_app.logger.debug("Unable to determine file format ")