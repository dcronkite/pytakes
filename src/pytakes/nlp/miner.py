import abc
import copy
import numbers
from typing import List

from pytakes.io.base import Dictionary
from pytakes.nlp import convert
from pytakes.nlp.terms import Term, Concept
from pytakes.util.utils import flatten


class Miner(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    def clean(self, terms):
        return terms

    @abc.abstractmethod
    def mine(self, text, offset):
        return text.split()

    @abc.abstractmethod
    def postprocess(self, terms):
        return terms

    @abc.abstractmethod
    def extract(self, terms):
        return list()
