import os
import re
import logging
import pypandoc
from definitions import Note, Group


# regex match everything between div tags, but minimally.
div_pat = re.compile('<div>(.+?)</div>', flags=re.DOTALL)


def extract_notes(path):
    notes = []
    filtered_file = pypandoc.convert_file(source_file=path, format='markdown',
                                 to='markdown', extra_args=['--lua-filter=filter.lua'])
    for s in div_pat.findall(filtered_file):
        pairs = re.split(pattern='\s*-{3,}\s*', string=s)
        faces = []
        for p in pairs:
            faces.extend(p.strip().replace('\r\n', '\n').split('\n\n', 1))
        notes.append(Note(name=faces[0], faces=faces))

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
                notes = extract_notes(fullp)
                current_group.children[name] = Group(name=name, children={n.name: n for n in notes})
    return current_group


if __name__ == '__main__':
    notes = read_notes('./notes')
    for n in notes:
        print(n)
    logging.info('Done')
