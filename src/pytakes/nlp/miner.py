import abc


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
