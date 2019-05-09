import json
import inspect
from collections import OrderedDict


class Pipe(object):
    """Pipe object should be defined so as to receive pairs of stacks corresponding to foci and mitochondria that need
    to be analyzed in the same way. All parameters and processes to be run should be defined and Pipe should be called
    for each pair, maybe even instanced in different interpreters to multiprocess."""

    def __init__(self, funcs=None):

        self.funcs = []
        self.add_function(funcs)

    def add_function(self, func):
        """Adds a function or list of function to the pipeline list."""
        if func is None:
            return
        if not isinstance(func, (list, tuple)):
            func = [func]
        func = [this_func if isinstance(this_func, AdaptedFunction) else AdaptedFunction(this_func)
                for this_func in func]
        self.funcs.extend(func)

    def concatenate_pipeline(self, pipeline):
        """It would be interesting to add this functionality and correct the __add__ magic function"""

    def _get_result(self, func_id, result_id):
        """Internal function to get the result from other function"""
        return self.funcs[func_id].result['result'][result_id]

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

        if subscriber_func_id <= provider_func_id:
            raise ValueError('Provider function must happen before subscriber function')

        subcriber_params = list(self.funcs[subscriber_func_id].vars)

        subscriber_func_parameter = subcriber_params[subscriber_func_parameter]

        self.funcs[subscriber_func_id].vars[subscriber_func_parameter] = \
            "self._get_result(%s, %s)" % (provider_func_id, provider_func_result)

    def run(self):
        for function in self.funcs:
            for parameter in function.vars:
                if isinstance(function.vars[parameter], str) and "_get_result" in function.vars[parameter]:
                    function.vars[parameter] = eval(function.vars[parameter])
            print('Executing: ')
            print(function)
            function.execute()

    def __add__(self, b):
        self.add_function(b)

    def __repr__(self):
        to_print = 'This pipeline has the following functions:\n\n'
        for n, function in enumerate(self.funcs):
            to_print += 'Function id: ' + str(n) + '\n'
            to_print += str(function) + '\n\n'

        return to_print


class AdaptedFunction(object):
    """Adapted Functions should be able to take the same parameters between different instances so as to be able to list
     them and run them one after the other. Extra parameters should be saved some way. There should be a way to print
     them and characterize them in order to dump the analysis made in Pipe."""

    def __init__(self, func):
        self.func = func
        self.name = func.__name__
        self.vars = self._get_func_parameters(func)
        self.result = {'result': [None], 'executed': False}

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

        result = eval(caller)
        self.result['result'] = result if isinstance(result, (list, tuple)) else [result]
        self.result['executed'] = True

    def __repr__(self):
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
