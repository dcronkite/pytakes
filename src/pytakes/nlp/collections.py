
class MinerCollection(object):

    def __init__(self):
        self.miners = []

    def add(self, miner):
        self.miners.append(miner)

    def apply(self, fn, *args, **kwargs):
        for miner in self.miners:
            fn(miner, *args, **kwargs)
