import glob
import json
from string import punctuation
import re

regex = re.compile("[{}]".format(re.escape(punctuation)))
for f_name in glob.glob('*.json'):
    print(f_name)
    with open(f_name) as f:
        jf = json.load(f)
        new = [{'path': d['path'],
                'files': d['files'],
                'keywords': list(set(d['keywords']).union(regex.split(d['path'])[1:]))}
        for d in jf]
    with open('new/' + f_name, 'w') as f:
        json.dump(new, f, indent=4)