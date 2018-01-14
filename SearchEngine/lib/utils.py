# from django.db import models
# from django.contrib import admin
from sys import path as syspath
from os import path as ospath
from django.db.models import Q
# from collections import defaultdict
from string import punctuation, whitespace
from collections import defaultdict
# from django.contrib.postgres.search import TrigramSimilarity, TrigramDistance
import re
syspath.append(ospath.join(ospath.expanduser("~"), 'airport-web'))
from SearchEngine.models import Server, WordNet, Path, Recommendation


class FindSearchResult:
    def __init__(self, *args, **kwargs):
        self.keyword = kwargs['keyword'].strip('-_')
        self.selected_servers = kwargs['servers']
        self.user = kwargs['user']
        self.splitted_substrings = []

    def add_recommendations(self, words):
        obj, _ = Recommendation.objects.get_or_create(
            defaults={'recommendations': {}, 'user':self.user},
            user=self.user
            )
        recoms = defaultdict(int, obj.recommendations)
        for word in words:
            recoms[word] += 1

        obj.recommendations = recoms
        obj.save()

    def validate_keyword(self):
        punct = set(punctuation) - {'-', '_'}
        cond1 = len(self.keyword) > 1
        cond2 = not punct.intersection(self.keyword)

        result = cond1 and cond2
        if cond1 and cond2:
            lst = set([i for i in re.split(r'-|_', self.keyword) if i][:5])
            # all_subs = {''.join(lst[i:j]) for i in range(0, len(lst) - 2, 2)
            #            for j in range(i + 3, len(lst) + 2, 2)}
            splitted_substrings = list(lst | {self.keyword})
            if len(splitted_substrings) >= 1:
                self.splitted_substrings = splitted_substrings

        return result

    def find_result(self):
        # query = Server()
        # query.objects.filter(name__in=selected_servers)
        if not self.validate_keyword():
            raise ValueError("Invalid Keyword")
        wordnet_result = self.get_similars()
        all_words = wordnet_result['words'] & wordnet_result['similars']
        all_words = all_words.union(self.splitted_substrings)
        try:
            self.add_recommendations(all_words)
        except TypeError:
            # user is anonymouse
            pass

        return [{'path': obj.path,
                 'metadata': obj.metadata,
                 'name': name,
                 'url': url,
                 'exact_match': self.exact_match(obj.files, obj.path)}
                     for name, url in self.selected_servers.items()
                for obj in Path.objects.filter(Q(server_name=name))
                if all_words.intersection(obj.files+obj.keywords)
        ]

    
    def exact_match(self, files, path):
        return any((i in files) or (i in path) for i in self.splitted_substrings)
    
    def check_intersection(self, files_and_keywords, path, all_words):
        # this should be done in json files
        return all_words.intersection(files_and_keywords)

    def get_similars(self):
        cond1 = Q(similars__overlap=self.splitted_substrings)
        cond2 = Q(word__in=self.splitted_substrings)
        all_obj = WordNet.objects.filter(cond1 | cond2)
        words = {obj.word for obj in all_obj}
        similars = {i for obj in all_obj for i in obj.similars}
        return {'words': words, 'similars': similars}
