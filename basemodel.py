import json
import os

from intervaltree import IntervalTree


CURRENT_DIR = os.path.abspath(os.path.dirname(__file__))
PROPERTIES_FILENAME = 'properties.json'


class BaseModel:
    '''Базовая модель
    '''

    def __init__(self):
        '''Конструктор
        '''

        with open(os.path.join(CURRENT_DIR, PROPERTIES_FILENAME)) as fid:
            self.props = json.load(fid)

        self.parsers = {} # grammar -> parser

        # Processors
        self.postprocess_all_facts = []
        self.postprocess_fact = []

    @property
    def model_name(self):
        '''Возвращает имя подели из properties.json
        '''

        return self.props['name']

    @property
    def model_version(self):
        '''Возвращает версию модели из properties.json
        '''

        return self.props['version']

    def coverage(self, text, spans):
        '''Возращает процент использованных символов (от 0 до 1)
        '''

        if not spans:
            return 0

        filled = sum(span[1] - span[0] for span in spans)
        filled = filled if filled > 0 else 1

        return round(filled / len(text), 2)

    def get_nonoverlapping_matches(self, text):
        '''Возвращает список matches с непересекающимися spans.
           Применяет сразу все грамматики, перечисленные в self.parsers
        '''

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

    def get_fact_dict(self, grammar, fact_json, start, stop):

        return {
            'grammar': grammar,
            'fact': fact_json,
            'span': {
                'start': start,
                'end': stop
            }
        }

    def get_facts(self, text):

        facts = []
        # Так как можно один факт раскладыать на несколько,
        # то при расчете coverage нужно брать только исходные
        # spans
        spans = []

        for grammar, match in self.get_nonoverlapping_matches(text):
            facts.append(self.get_fact_dict(
                grammar,
                match.fact.as_json,
                match.span[0],
                match.span[1]))
            spans.append((match.span[0], match.span[1]))

        # Postprocess all facts each time
        for func in self.postprocess_all_facts:
            func(facts)

        # Postprocess each fact
        for i, fact in enumerate(facts):
            for func in self.postprocess_fact:
                new_fact = func(fact)
                if new_fact:
                    facts[i] = new_fact

        return (facts, spans)


    def extract(self, text):

        facts, source_spans = self.get_facts(text)

        return {
            'model_name': self.model_name,
            'model_version': self.model_version,
            'raw': text,
            'coverage': self.coverage(text, source_spans),
            'facts': facts
        }
