import json
import inspect
from collections import OrderedDict


class Pipe(object):
    """Pipe object should be defined so as to receive pairs of stacks corresponding to foci and mitochondria that need
    to be analyzed in the same way. All parameters and processes to be run should be defined and Pipe should be called
    for each pair, maybe even instanced in different interpreters to multiprocess."""

    def __init__(self, funcs=None):

        self.funcs = OrderedDict()
        self.add_function(funcs)
        self.verbose = False

    def add_function(self, func):
        """Adds a function or list of function to the pipeline list."""
        if func is None:
            return
        if not isinstance(func, (list, tuple)):
            func = [func]
        func = [this_func if isinstance(this_func, AdaptedFunction) else AdaptedFunction(this_func)
                for this_func in func]
        for this_func in func:
            self._add_function(this_func.func_id, this_func)

    def _add_function(self, func_id, adap_func):

        ids = list(self.funcs.keys())
        if func_id in ids:
            n = 0
            new_func_id = '_'.join([func_id, str(n)])
            while new_func_id in ids:
                n += 1
                new_func_id = '_'.join([func_id, str(n)])
            func_id = new_func_id

        self.funcs.update({func_id: adap_func})

    def change_func_id(self, new_name, old_name):
        if new_name in self.funcs.keys():
            raise ValueError('New function id already taken')
        if old_name not in self.funcs.keys():
            raise ValueError('Old function id does not exist')
        self.funcs = OrderedDict([(new_name if k == old_name else k, v) for k, v in self.funcs.items()])

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
        provider_func_id : id
            index of the function providing the parameter
        subscriber_func_id : id
            index of the function with the new parameter
        provider_func_result : int, default=0
            index of the result to pass on to the subscribing function
        subscriber_func_parameter : int, default=0
            index of the parameter from the subscribing function"""

        if list(self.funcs).index(subscriber_func_id) <= list(self.funcs).index(provider_func_id):
            raise ValueError('Provider function must happen before subscriber function')

        subscriber_params = list(self.funcs[subscriber_func_id].vars)

        subscriber_func_parameter = subscriber_params[subscriber_func_parameter]

        self.funcs[subscriber_func_id].vars[subscriber_func_parameter] = \
            "self._get_result(%s, %s)" % (provider_func_id, provider_func_result)

    def run(self):
        for function_key in self.funcs:
            function = self.funcs[function_key]
            for parameter in function.vars:
                if isinstance(function.vars[parameter], str) and "_get_result" in function.vars[parameter]:
                    function.vars[parameter] = eval(function.vars[parameter])

            if self.verbose:
                print('Executing: ')
                print(function)

            function.execute()

    def to_dict(self):
        all_functions_dict = {}
        for function_key in self.funcs:
            all_functions_dict[function_key] = self.funcs[function_key].to_dict()
        return all_functions_dict

    def to_json(self):
        return json.dumps(self.to_dict())

    def dump(self, path):
        with open(str(path), "w") as write_file:
            json.dump(self.to_dict(), write_file)

    def __add__(self, b):
        self.add_function(b)

    def __repr__(self):
        to_print = 'This pipeline has the following functions:\n\n'
        for function_key in self.funcs:
            to_print += 'Function id: ' + str(function_key) + '\n'
            to_print += str(self.funcs[function_key]) + '\n\n'

        return to_print

    def __getitem__(self, item):
        return self.funcs[item]

    def __rshift__(self, other):
        if not isinstance(other, AdaptedFunction):
            raise TypeError('You can only add Adapted functions with this method. Use make_connection method for more '
                            'specific cases')

        last_function_key = list(self.funcs.keys())[-1]
        self.add_function(other)
        new_function_key = list(self.funcs.keys())[-1]

        self.make_connection(last_function_key, new_function_key)


class AdaptedFunction(object):
    """Adapted Functions should be able to take the same parameters between different instances so as to be able to list
     them and run them one after the other. Extra parameters should be saved some way. There should be a way to print
     them and characterize them in order to dump the analysis made in Pipe."""

    def __init__(self, func, func_id=None):
        self.func = func
        self.name = func.__name__
        self.func_id = self.name if func_id is None else func_id
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

        result = self.func(**self.vars)
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

    def __getitem__(self, item):
        return self.vars[item]

    def __setitem__(self, key, value):
        self.vars[key] = value
