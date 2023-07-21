import json
import platform

from .base import Output


class JsonlOutput(Output):

    def __init__(self, name=None, path=None, metalabels=None,
                 types=None, hostname=None, batch_number=None, **config):
        super().__init__(name=name, **config)
        self.labels = (metalabels or []) + self.all_labels
        self.types = types
        self.hostname = hostname or platform.node()
        self.batch_number = batch_number
        self.fh = open(path / self.name, 'w')

    def writerow(self, feat, meta=None, text=None):
        length = len(text)
        data = {
            'meta': meta,
            'concept_id': feat.id,
            'concept': feat.cat,
            'captured': self._get_text(text, feat.begin, feat.end),
            'context': self._get_text(text, self._get_index(length, feat.begin - self.context_width),
                                      self._get_index(length, feat.end + self.context_width)),
            'qualifiers': {
                'certainty': feat.certainty,
                'hypothetical': feat.hypothetical,
                'historical': feat.historical,
                'other_subject': feat.other,
                'terms': feat.qualifiers,
            },
            'start_index': feat.absolute_begin,
            'end_index': feat.absolute_end,
            'tracking': {
                'hostname': self.hostname,
                'batch': self.batch_number,
            }
        }
        self.fh.write(json.dumps(data) + '\n')

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fh.close()
