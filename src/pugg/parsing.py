import os
import re
import logging
import pypandoc
from bs4 import BeautifulSoup
from time import time
from hashlib import md5
from .database import File, Topic, Card


# Regex match everything between div tags, but minimally.
# TODO replace with built-in HTML parser
div_pat = re.compile('<div class="card">(.+?)</div>', flags=re.DOTALL)

# Path of the lua filter that extracts blockquotes. The filter could have been written in python, but
# Pandoc actually includes the whole lua stack which means it can run the faster lua code.
FILTER_PATH = os.path.join(os.path.dirname(__file__), 'filters/blockquotes.lua')

# str.translate() is a very fast function that lets you transform strings according to a lookup table.
# The tables below removes spaces, replaces - with _, and lowercases, all at once.
DELETE = str.maketrans('', '', '0123456789-_')
SPACEANDLOWERCASE = str.maketrans(' -ABCDEFGHIJKLMNOPQRSTUVWXYZ', '__abcdefghijklmnopqrstuvwxyz')


def walk_notes(dir):
    if not os.path.exists(dir):
        raise Exception("Given path {} does not exist".format(dir))
    dir = os.path.realpath(dir)
    prefix_len = len(dir) + 1  # ignore the first part of the path when creating topic paths
    topics, md_files = [Topic(name='root', real_path=dir, path='', parent_path='')], []
    for path, folders, files in os.walk(dir):

        real_path = os.path.realpath(path)
        parent_path = filter_name(real_path[prefix_len:])

        topics.extend([Topic(
            name=filter_name(f),
            parent_path=parent_path,
            real_path=real_path,
            path=os.path.join(parent_path, filter_name(f)))
            for f in folders])

        # topics.extend([Topic(
        #     name=filter_name(f.split('.')[0]),
        #     parent_path=parent_path,
        #     path=os.path.join(path, f))
        #     for f in files])

        md_files.extend([File(
            name=filter_name(f),
            topic_path=parent_path,
            last_read=os.path.getmtime(os.path.join(path, f)),
            path=os.path.join(path, f))
            for f in files if f.split('.')[-1] == 'md'])

    return topics, md_files


def filter_name(s):
    return s.translate(DELETE).strip().translate(SPACEANDLOWERCASE)


def read_notes(path):
    if not os.path.exists(path):
        raise Exception("Given path {} does not exist".format(path))

    # folder, curr_dir = os.path.split(path)
    notes = []

    for p in os.listdir(path):
        fullp = os.path.join(path, p).replace('\\', '/')

        if os.path.isdir(fullp):
            logging.info('Discovered folder {}'.format(fullp))
            notes.extend(read_notes(fullp))
        else:
            name, ext = os.path.splitext(p)

            if ext == '.md':
                print('Discovered markdown file {}'.format(fullp))
                notes.extend(extract_cards(fullp))
    return notes


def parse_files(md_files):
    notes = []
    for f in md_files:
        notes.extend(extract_cards(f.path, topic_path=f.topic_path))
    return notes


def extract_cards(path, topic_path):
    notes = []
    filtered_file = pypandoc.convert_file(source_file=path, format='markdown',
                                          to='html', extra_args=['--mathjax', '--lua-filter={}'.format(FILTER_PATH)])

    # TODO 'Real path' attributes of files are not portable, change this to be relative to root dir, or move database
    #  some local cache so its system specific.
    soup = BeautifulSoup(filtered_file, features='html.parser')

    # Prepend any image link with /tempview/, this allows the card HTML to access assets
    for img in soup.findAll('img'):
        if 'src' in img.attrs:
            img['src'] = '/assets' + os.path.join(os.path.dirname(path), img['src'])

    for tag in soup.children:
        if tag.name=='div' and 'class' in tag.attrs and 'card' in tag.attrs['class']:
            for i, c in enumerate(tag.contents):
                if c.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
                    c.attrs = {}  # pandoc generates ids for every header, removing saves space

                    # TODO replace() in python is slow, try this in a pandoc filter?
                    # Markdown preview enhanced uses \bm for bold symbols, replace this with something MathJax
                    # can understand
                    front = repr(c).replace('\\bm{', '\\boldsymbol{')
                    back = ''.join('<br />' if d=='\n' else repr(d).replace('\\bm{', '\\boldsymbol{') for d in tag.contents[i+1:])

                    hsh = md5()
                    hsh.update((front+back).encode('utf8'))
                    notes.append(Card(file_path=path,
                                      topic_path=topic_path,
                                      hash=str(hsh.hexdigest()),
                                      front=front,
                                      back=back,
                                      halflife=0,
                                      last_reviewed=int(time())))
                    break
    return notes

