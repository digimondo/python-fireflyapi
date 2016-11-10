from abc import ABCMeta
from .json_dump import JSONDump


class ListObserver(list):
    """
        Send all changes to an observer.
    """
    def __init__(self, value, observer):
        list.__init__(self, value)
        self.set_observer(observer)

    def set_observer(self, observer):
        """
        All changes to this list will trigger calls to observer methods.
        """
        self.observer = observer

    def __setitem__(self, key, value):
        """
        Intercept the l[key]=value operations.
        Also covers slice assignment.
        """
        try:
            oldvalue = self.__getitem__(key)
        except KeyError:
            list.__setitem__(self, key, value)
            self.observer.list_create(self, key)
        else:
            list.__setitem__(self, key, value)
            self.observer.list_set(self, key, oldvalue)

    def __delitem__(self, key):
        oldvalue = list.__getitem__(self, key)
        list.__delitem__(self, key)
        self.observer.list_del(self, key, oldvalue)

    def __setslice__(self, i, j, sequence):
        oldvalue = list.__getslice__(self, i, j)
        self.observer.list_setslice(self, i, j, sequence, oldvalue)
        list.__setslice__(self, i, j, sequence)

    def __delslice__(self, i, j):
        oldvalue = list.__getitem__(self, slice(i, j))
        list.__delslice__(self, i, j)
        self.observer.list_delslice(self, i, oldvalue)

    def append(self, value):
        list.append(self, value)
        self.observer.list_append(self)

    def pop(self):
        oldvalue = list.pop(self)
        self.observer.list_pop(self, oldvalue)

    def extend(self, newvalue):
        list.extend(self, newvalue)
        self.observer.list_extend(self, newvalue)

    def insert(self, i, element):
        list.insert(self, i, element)
        self.observer.list_insert(self, i, element)

    def remove(self, element):
        index = list.index(self, element)
        list.remove(self, element)
        self.observer.list_remove(self, index, element)

    def reverse(self):
        list.reverse(self)
        self.observer.list_reverse(self)

    def sort(self, cmpfunc=None):
        oldlist = self[:]
        list.sort(self, cmpfunc)
        self.observer.list_sort(self, oldlist)


class DictObserver(dict):
    """
        Send all changes to an observer.
    """
    def __init__(self, value, observer):
        dict.__init__(self, value)
        self.set_observer(observer)

    def set_observer(self, observer):
        """
        All changes to this dictionary will trigger calls to observer methods
        """
        self.observer = observer

    def __setitem__(self, key, value):
        """
        Intercept the l[key]=value operations.
        Also covers slice assignment.
        """
        try:
            oldvalue = self.__getitem__(key)
        except KeyError:
            dict.__setitem__(self, key, value)
            self.observer.dict_create(self, key)
        else:
            dict.__setitem__(self, key, value)
            self.observer.dict_set(self, key, oldvalue)

    def __delitem__(self, key):
        oldvalue = dict.__getitem__(self, key)
        dict.__delitem__(self, key)
        self.observer.dict_del(self, key, oldvalue)

    def clear(self):
        oldvalue = self.copy()
        dict.clear(self)
        self.observer.dict_clear(self, oldvalue)

    def update(self, update_dict):
        replaced_key_values = []
        new_keys = []
        for key, item in update_dict.items():
            if key in self:
                replaced_key_values.append((key, item))
            else:
                new_keys.append(key)
        dict.update(self, update_dict)
        self.observer.dict_update(self, new_keys, replaced_key_values)

    def setdefault(self, key, value=None):
        if key not in self:
            dict.setdefault(self, key, value)
            self.observer.dict_setdefault(self, key, value)
            return value
        else:
            return self[key]

    def pop(self, k, x=None):
        if k in self:
            value = self[k]
            dict.pop(self, k, x)
            self.observer.dict_pop(self, k, value)
            return value
        else:
            return x

    def popitem(self):
        key, value = dict.popitem(self)
        self.observer.dict_popitem(self, key, value)
        return key, value


class Observable(JSONDump):
    """
    Observable type adapted from http://code.activestate.com/recipes/306864-list-and-dictionary-observer/
    """
    __metaclass__ = ABCMeta

    _original_state = {}
    _changed = []
    _export = []

    def __init__(self):
        self._dirty = False

    def __setattr__(self, key, value):
        if key != '_dirty':
            self._original_state[key] = getattr(self, key)
            self._changed.append(key)
            if(isinstance(value, list)):
                self.__dict__[key] = ListObserver(value, self._Observer(self))
            elif(isinstance(value, dict)):
                self.__dict__[key] = DictObserver(value, self._Observer(self))
            else:
                self.__dict__[key] = value
            self._make_dirty()

    def _make_dirty(self):
        self._dirty = True

    def _not_dirty(self):
        self._dirty = False
        self._changed = []

    def get_changes(self):
        return self._changed

    def export(self, changes_only=False):
        if(changes_only):
            return self._changed.intersection(self.export(False))

        return self._export

    class _Observer(object):
        def __init__(self, instance):
            self.instance = instance

        def p(self, *args):
            # print self.attr, args
            self.instance._make_dirty()

        def __getattr__(self, attr):
            self.attr = attr
            return self.p
