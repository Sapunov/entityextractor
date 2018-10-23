import json
import os

from intervaltree import IntervalTree


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
PROPERTIES_FILENAME = 'properties.json'


class BaseModel:

    def __init__(self):

        with open(os.path.join(CURRENT_DIR, PROPERTIES_FILENAME)) as fid:
            self.props = json.load(fid)

        self.parsers = {} # grammar -> parser

    @property
    def model_name(self):

        return self.props['name']

    @property
    def model_version(self):

        return self.props['version']

    def coverage(self, text, spans):

        if not spans:
            return 0

        filled = sum((_.get('end', 0) - _.get('start', 0)) for _ in spans)
        filled = filled if filled > 0 else 1

        return round(filled / len(text), 2)

    def get_nonoverlapping_matches(self, text):

        intervals = IntervalTree()
        matches = []
        nonoverlapping_matches = []

        for grammar, parser in self.parsers.items():
            for match in parser.findall(text):
                start, stop = match.span
                matches.append((stop - start, grammar, match))

        matches.sort(key=lambda it: it[0], reverse=True)

        for _, grammar, match in matches:
            start, stop = match.span
            if not intervals[start:stop]:
                intervals[start:stop] = True
                nonoverlapping_matches.append((grammar, match))

        return nonoverlapping_matches
