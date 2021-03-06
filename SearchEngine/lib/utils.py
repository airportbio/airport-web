# from django.db import models
# from django.contrib import admin
from sys import path as syspath
from os import path as ospath
from django.db.models import Q
# from collections import defaultdict
from string import punctuation, whitespace
from collections import defaultdict, OrderedDict
# from django.contrib.postgres.search import TrigramSimilarity, TrigramDistance
import re
from SearchEngine.lib.custom_exceptions import NoResultException
syspath.append(ospath.join(ospath.expanduser("~"), 'airport-web'))
from SearchEngine.models import Server, WordNet, Path, Recommendation
from itertools import count, tee, chain
import asyncio


class FindSearchResult:
    def __init__(self, *args, **kwargs):
        self.keyword = kwargs['keyword'].strip('-_')
        self.selected_servers = kwargs['servers']
        self.user = kwargs['user']
        self.exact_only = kwargs['exact_only']
        self.splitted_substrings = []
        self.all_servers_count = Server.objects.count()

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
        exact_only_flag = self.exact_only == 'true'
        if exact_only_flag:
            all_words = set()
        else:
            wordnet_result = self.get_similars()
            all_words = wordnet_result['words'] & wordnet_result['similars']
        all_words = all_words.union(self.splitted_substrings)
        try:
            self.add_recommendations(all_words)
        except TypeError:
            # user is anonymouse
            pass
        all_words = {i.lower() for i in all_words}
        for name, url in self.selected_servers.items():
            for obj in Path.objects.filter(server_name=name):
                if all_words.intersection(obj.keywords):
                    yield {'path': obj.path,
                            'meta_links': obj.meta_path,
                            'metadata': obj.metadata,
                            'name': name,
                            'path_id': obj.id,
                            'url': url,
                            'exact_match': exact_only_flag or self.exact_match(obj.files, obj.path)}


    def exact_match(self, files, path):
        # return bool(set(self.splitted_substrings).intersection(keywords))
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


class Paginator:
    def __init__(self, *args, **kwargs):
        self.results = args[0]
        self.rows_number = kwargs['rows_number']
        self.range_frame = kwargs['range_frame']
        self.counter = count(1)
        self.cache = {}
        self.current = self.create_page()
    
    def create_page(self, number=False):
        if not number:
            number = next(self.counter)
        # should use deque with max_len == self.row_number
        items = [next(self.results, None) for _ in range(self.rows_number)]
        if all(i is None for i in items):
            raise NoResultException("Sorry cound't find any match for this keyword.")
        page = Page(items=items,
                    number=number,
                    range_frame=self.range_frame,
                    row_number=self.rows_number)
        self.cache[number] = page
        return page
    
    def __next__(self):
        number = next(self.counter)
        try:
            page = self.cache[number]
        except KeyError:
            print("create page {}".format(number))
            page = self.create_page(number=number)
        finally:
            return page

    def __iter__(self):
        return self
    
    def __getitem__(self, index):
        try:
            page = self.cache[index]
        except KeyError:
            page = self.create_page(index)
        else:
            print("call from cache {}".format(index))
        finally:
            self.current = page
            return page
            

    def has_other_pages(self):
        try:
            # has next pages
            cond1 = self.current.last_item is not None
            # has previous pages
            cond2 = self.current.number > 1
            return cond1 or cond2
        except IndexError:
            return True



class Page:
    def __init__(self, *args, **kwargs):
        self.number = kwargs['number']
        self.row_number = kwargs['row_number']
        self.range_frame = kwargs['range_frame']
        self.items = kwargs['items']
        self.last_item = self.items[-1]
        self.previous_page_number = max(1, self.number - (self.range_frame + 1))
        # Since the paginator is an iterator we can't use a next_page number
        # unless, always retrive pages within frame range. Actually one more
        # and one less than frame range.    
        # self.next_page_number = self.number + self.range_frame
        self.index = 0

    def __next__(self):
        try:
            result = self.items[self.index]
        except IndexError:
            self.index = 0
            raise StopIteration
        self.index += 1
        return result

    def __iter__(self):
        return self
    
    def has_previous(self):
        return self.number != 1

    def has_next(self):
        try:
            return self.last_item is not None
        except IndexError:
            return True

    def page_range(self):
        lower = max(self.number - self.range_frame, 1)
        # for a more precise result we should always cache
        # pages within the range_frame so that we can easily
        # detect wheter there are any upper pages or not
        if self.last_item is None:
            upper = self.number + 1
        else:
            upper = lower + (2*self.range_frame + 2)
        return range(lower, upper)


class Cache(OrderedDict):
    def __init__(self, *args, **kwargs):
        self.lenght = args[0]
        super(Cache, self).__init__(self, *args[1:], **kwargs)

    def __setitem__(self, key, value):
        if len(self) == self.lenght:
            self.popitem(last=False)
        super().__setitem__(key, value)
