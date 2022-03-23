class Alias:
    def __init__(self, obj):
        self.obj = obj


def merge_items(args: tuple, kwargs: dict):
    yield from args
    for k, v in kwargs:
        if isinstance(v, Alias):
            yield v
        else:
            yield Alias(v)


class Returning:
    def __init__(self, *args, **kwargs):
        self.obj = [x for x in merge_items(args, kwargs)]


class From:
    def __init__(self, *args, **kwargs):
        self.obj = [x for x in merge_items(args, kwargs)]


class Join:
    def __init__(self, *args, **kwargs):
        self.obj = [x for x in merge_items(args, kwargs)]

    def On(self):
        ...

    def Using(self):
        ...


class InnerJoin(Join):
    ...


class RightJoin(Join):
    ...


class LeftJoin(Join):
    ...


class Where:
    def __init__(self, *args):
        ...
