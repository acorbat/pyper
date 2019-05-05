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

        # Variables where results are saved
        self.df = pd.DataFrame()
        self.foci_labeled = None
        self.cell_segm = None
        self.mito_segm = None


    def process(self, p=None):
        """Enter foci stack and mito stack to be processed. Returns a DataFrame with the results"""

        # Organize stack accordingly for processing

        # Segment the stacks inserted
        if self.foci_labeled is None:
            self.segment()

        # Extract attributes through label_to_df
        if self.attrs is not None:
            self.df = fa.label_to_df(self.foci_labeled, cols=self.attrs,
                                     intensity_image=self.mito_segm)

        # Perform extra functions
        for func in self.funcs:
            this_df = func(self.df, self.foci_labeled, self.cell_segm, self.mito_segm)
            self.df = self.df.merge(this_df)

        return self.df

    def add_segmenter(self, segmenter):
        self.segmenter = segmenter

    def segment(self, foci_stack, mito_stack):
        self.segmenter.vars['foci_stack'] = foci_stack
        self.segmenter.vars['mito_stack'] = mito_stack
        self.foci_labeled, self.cell_segm, self.mito_segm = self.segmenter.execute()

    def renew_stack(self, foci_stack, mito_stack):
        self.df = pd.DataFrame()
        self.foci_labeled = None
        self.cell_segm = None
        self.mito_segm = None
        self.segmenter['foci_stack'] = foci_stack.copy()
        self.segmenter['mito_stack'] = mito_stack.copy()

    def add_attr(self, attrs):
        if not isinstance(attrs, list):
            attrs = list(attrs)
        self.attrs.extend(attrs)


    def add_func(self, funcs):
        if not isinstance(funcs, list):
            funcs = list(funcs)
        self.funcs.extend(funcs)


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
