import os
import re
import logging
import pypandoc
from hashlib import md5
from .definitions import Note, Group
from .database import File, Topic, Card


# Regex match everything between div tags, but minimally.
div_pat = re.compile('<div>(.+?)</div>', flags=re.DOTALL)

# Path of the lua filter that extracts blockquotes. The filter could have been written in python, but
# Pandoc actually includes the whole lua stack which means it can run the faster lua code.
FILTER_PATH = os.path.join(os.path.dirname(__file__), 'filters/blockquotes.lua')

# str.translate() is a very fast function that lets you transform strings according to a lookup table.
# The tables below removes spaces, replaces - with _, and lowercases, all at once.
DELETE = str.maketrans('', '', '0123456789-_')
SPACEANDLOWERCASE = str.maketrans(' -ABCDEFGHIJKLMNOPQRSTUVWXYZ', '__abcdefghijklmnopqrstuvwxyz')


def extract_cards(path, topic):
    notes = []
    filtered_file = pypandoc.convert_file(source_file=path, format='markdown',
                                          to='markdown', extra_args=['--lua-filter={}'.format(FILTER_PATH)])
    for s in div_pat.findall(filtered_file):
        # TODO Add support for multiple faces. The commented block below is an attempt at this.
        # pairs = re.split(pattern='\s*-{3,}\s*', string=s)
        # faces = []
        # for p in pairs:
        #     faces.extend(p.strip().replace('\r\n', '\n').split('\n\n', 1))
        # notes.append(Note(name=faces[0], faces=faces))

        # Simpler version
        front, back = s.strip().replace('\r\n', '\n').split('\n\n', 1)
        hsh = md5()
        hsh.update((front+back).encode('utf8'))
        notes.append(Card(file_path=path, topic=topic, hash=str(hsh.hexdigest()), front=front, back=back, halflife=0))
    return notes


def read_notes(path):
    if not os.path.exists(path):
        raise Exception("Given path {} does not exist".format(path))

    folder, curr_dir = os.path.split(path)
    current_group = Group(name=curr_dir, children=dict())

    for p in os.listdir(path):
        fullp = os.path.join(path, p).replace('\\', '/')

        if os.path.isdir(fullp):
            logging.info('Discovered folder {}'.format(fullp))
            current_group.children[p] = read_notes(fullp)
        else:
            name, ext = os.path.splitext(p)

            if ext == '.md':
                print('Discovered markdown file {}'.format(fullp))
                notes = extract_cards(fullp)
                current_group.children[name] = Group(name=name, children={n.name: n for n in notes})
    return current_group


def walk_notes(dir):
    if not os.path.exists(dir):
        raise Exception("Given path {} does not exist".format(dir))
    dir = os.path.realpath(dir)
    topics, md_files = [Topic(name='root', path=dir, parent_path=dir)], []

    for path, folders, files in os.walk(dir):
        parent_path = os.path.realpath(path)

        topics.extend([Topic(
            name=filter_name(f),
            parent_path=parent_path,
            path=os.path.join(path, f))
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


def read_notes2(path):
    if not os.path.exists(path):
        raise Exception("Given path {} does not exist".format(path))

    # folder, curr_dir = os.path.split(path)
    notes = []

    for p in os.listdir(path):
        fullp = os.path.join(path, p).replace('\\', '/')

        if os.path.isdir(fullp):
            logging.info('Discovered folder {}'.format(fullp))
            notes.extend(read_notes2(fullp))
        else:
            name, ext = os.path.splitext(p)

            if ext == '.md':
                print('Discovered markdown file {}'.format(fullp))
                notes.extend(extract_cards(fullp))
    return notes


def parse_files(md_files):
    notes = []
    for f in md_files:
        notes.extend(extract_cards(f.path, topic=f.topic))
    return notes


