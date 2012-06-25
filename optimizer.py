import os
import os.path
import shlex
import subprocess
import sys
import shutil
import tempfile
from flask import current_app
from util import RegistryMetaclass

class Optimizer(object):
    """
    Super-class for optimizers
    """

    __metaclass__ = RegistryMetaclass(
        clazz=lambda: Optimizer, attribute='optimize',
        desc='an optimizer implementation')
    
    input_placeholder = "__INPUT__"
    output_placeholder = "__OUTPUT__"
    

    def _replace_placeholders(self, command, input, output):
        """
        Replaces the input and output placeholders in a string with actual parameter values
        """
        return command.replace(Optimiser.input_placeholder, input).replace(Optimiser.output_placeholder, output)
        
        
    def optimize(self, path, output=None):
        """
        Optimizes an image
        """
        raise NotImplementedError()
        
        
    def _run(args):
        try:
            retcode = subprocess.call(args, stdout=self.stdout.opened, stderr=self.stderr.opened)
        except OSError:
            logging.error("Error executing command %s. Error was %s" % (command, OSError))

        if retcode != 0:
            # gifsicle seems to fail by the file size?
            os.unlink(output_file_name)
        else :
            if not self.list_only:
                # compare file sizes if the command executed successfully
                self._keep_smallest_file(self.input, output_file_name)
            else:
                self._list_only(self.input, output_file_name)

                
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
    id = 'png'
    
    @classmethod
    def get_commands(cls, quiet=False):
        if kwargs.get('quiet') == True:
            pngcrush = 'pngcrush -rem alla -brute -reduce -q "__INPUT__" "__OUTPUT__"'
        else:
            pngcrush = 'pngcrush -rem alla -brute -reduce "__INPUT__" "__OUTPUT__"'
            
        return ('pngnq -n 256 -o "__OUTPUT__" "__INPUT__"', pngcrush)
        
    def optimize(self, **kwargs):
        commands = cls.get_commands(kwargs.get('quiet'))
        
        for command in commands:
            args = shlex.split(command)
            
            _run(args)
            
        
        
class JPGOptimizer(Optimizer):
    id = 'jpg'
    
    @classmethod
    def get_commands(cls, strip_meta=True):
        if kwargs.get('strip_meta'):
            return ('jpegtran -outfile "__OUTPUT__" -optimise -copy none "__INPUT__"',
                'jpegtran -outfile "__OUTPUT__" -optimise -progressive "__INPUT__"')
        else:
            return ('jpegtran -outfile "__OUTPUT__" -optimise -copy all "__INPUT__"',
                'jpegtran -outfile "__OUTPUT__" -optimise -progressive -copy all "__INPUT__"')

    def optimize(self, **kwargs):
        commands = cls.get_commands(kwargs.get('strip_meta'))
        
        # for the first iteration, return the first command
        if self.iterations == 0:
            self.iterations += 1
            return self.commands[0]
        elif self.iterations == 1:
            self.iterations += 1

            # for the next one, only return the second command if file size > 10kb
            if os.path.getsize(self.input) > 10000:
                if self.quiet == False:
                    logging.warning("File is > 10kb - will be converted to progressive")
                return self.commands[1]

        return False