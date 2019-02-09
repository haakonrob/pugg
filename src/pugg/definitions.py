import logging


class Store:
    def __init__(self, *args, **kwargs):
        self.args = args
        for k, v in kwargs.items():
            self.__dict__[k] = v

    def __repr__(self):
        return self.__class__.__name__+"({})".format(
            ", ".join(str(k)+'='+
                      (repr(v) if type(v) is not dict else str(tuple(k for k in v.keys())))
                      for k, v in self.__dict__.items() if v != ())
        )


class Note(Store):
    def __init__(self, *args, **kwargs):
        self.name = None
        self.faces = None
        self.metadata = Store(half_life=None, last_reviewed=None)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return "( note :: {} )".format(
            ' ::\n\t'.join(self.faces) if len(self.faces) > 0 else 'EMPTY')

    def __getitem__(self, path):
        if path == ():
            return self

    def __iter__(self):
        for f in self.faces:
            yield f


class Group(Store):
    def dfs(self, path=()):
        it = iter(sorted(self.children.keys()))
        for n in it:
            c = self.children[n]
            if isinstance(c, Group):
                for p, cc in c.dfs(path + (c.name,)):
                    yield p, cc
            else:
                yield path + (c.name,), c

    def __str__(self):
        return "( group :: {} :: {} )".format(
            self.name,
            ('\n'+'\n'.join(repr(c) for c in self.children)) if len(self.children) > 0 else 'EMPTY')

    def __getitem__(self, path):
        if path == ():
            return self

        if type(path) is not tuple:
            path = (path,)

        head, tail = path[0], (path[1:] if len(path)>1 else ())
        if head in self.children.keys():
            return self.children[head][tail]
        else:
            return None

    def __setitem__(self, path, value):
        if type(path) is not tuple:
            path = (path,)

        head, tail = path[0], (path[1:] if len(path)>1 else ())

        if tail == ():
            if isinstance(value, Note) or isinstance(value, Group):
                if value.name is not None and value.name != head:
                    logging.warning(("An attempt was made to assign a {} with name '{}' under the key '{}'. "
                                     "The key has been changed to '{}'")
                                    .format(type(value), repr(value.name(), repr(head), repr(value.name))))
                    head = value.name

                elif value.name is None:
                    logging.warning(("An attempt was made to assign a {} with no name under the key '{}'. "
                                     "The objects name has been changed to '{}'")
                                    .format(type(value), head, head))
                    value.name = head

                self.children[head] = value
            else:
                raise ValueError('Cannot assisn value of type {} to group'.format(type(value)))
        elif head in self.children.keys():
            self.children[head][tail] = value
        else:
            raise IndexError('Child {} not in group {}'.format(head, self.name))

    def __contains__(self, item):
        return item in self.children.keys()

    def __iter__(self):
        for name in sorted(self.children.keys()):
            yield self.children[name]

    def __eq__(self, other):
        if not isinstance(other, Group):
            return False

        if self.children.keys() != other.children.keys():
            return False

        for k, c in self.children.items():
            if c != other.children[k]:
                return False

        return True







