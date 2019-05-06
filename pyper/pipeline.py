import json
import multiprocessing
import inspect
from collections import OrderedDict

import pandas as pd

from foci_finder import foci_analysis as fa
from foci_finder import docking as dk


class Pipe(object):
    """Pipe object should be defined so as to receive pairs of stacks corresponding to foci and mitochondria that need
    to be analyzed in the same way. All parameters and processes to be run should be defined and Pipe should be called
    for each pair, maybe even instanced in different interpreters to multiprocess."""

    def __init__(self, attrs=['label', 'centroid', 'coords', 'area'], funcs=None):

        self.funcs = funcs  # Concatenated list of functions to be run
        self.results = {}  # Dictionary to save results of each function

    def add_function(self, func):
        """Adds a function or list of function to the pipeline list."""
        self.funcs.extend(func)

    def make_connection(self, provider_func_id, subscriber_func_id,
                        provider_func_result=0, subscriber_func_parameter=0):
        """Connects the result of a provider function to the input of another subscriber function.

        Parameters
        ----------
        provider_func_id : int
            index of the function providing the parameter
        subscriber_func_id : int
            index of the function with the new parameter
        provider_func_result : int, default=0
            index of the result to pass on to the subscribing function
        subscriber_func_parameter : int, default=0
            index of the parameter from the subscribing function"""
        self.funcs[subscriber_func_id].vars[subscriber_func_parameter] = \
            self.results[provider_func_id][provider_func_result]


class AdaptedFunction(object):
    """Adapted Functions should be able to take the same parameters between different instances so as to be able to list
     them and run them one after the other. Extra parameters should be saved some way. There should be a way to print
     them and characterize them in order to dump the analysis made in Pipe."""

    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.vars = self._get_func_parameters(func)

    def _get_func_parameters(self, func):
        di = OrderedDict(inspect.signature(func).parameters)
        dic = OrderedDict([(key, value.default)
                           if value.default is not inspect._empty
                           else (key, None)
                           for key, value in di.items()])
        return dic

    def execute(self):
        """Executes function with saved parameters."""
        caller = 'self.func(' + ', '.join([str(value) for key, value in self.vars.items()]) + ')'

        return eval(caller)

    def __str__(self):
        characteristics = 'Function: ' + self.name + '\n\n'
        characteristics += '\tParameters\n\t----------\n'
        characteristics += '\t' + '\n\t'.join([str(key) + ': ' + str(value) for key, value in self.vars.items()])
        return characteristics

    def to_dict(self):
        return {'name': self.name,
                'Parameters': self.vars}

    def to_json(self):
        return json.dumps(self.to_dict())

    def dump(self, path):
        with open(str(path), "w") as write_file:
            json.dump(self.to_dict(), write_file)
