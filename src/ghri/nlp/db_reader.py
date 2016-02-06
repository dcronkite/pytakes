from ghri.db_reader import *


class NLPdevResources(NLPdevWrapper):
    def get_negex_triggers(self, version=''):
        negexes = self.execute_return("""
                            SELECT negex
                                  ,type
                              FROM W_res_negexTriggers%s
                            """ % version)
        return negexes

