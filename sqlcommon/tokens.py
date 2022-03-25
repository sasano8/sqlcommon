from typing import Any, List, NamedTuple


def tokenize(it):
    for x in it:
        yield to_sql(x)


def to_sql(obj):
    if isinstance(obj, (AstBase, Expressions)):
        return obj.to_sql()
    elif isinstance(obj, (int, str, float, bool)):
        return Value(obj).to_sql()
    elif obj is None:
        return Value(obj).to_sql()
    elif isinstance(obj, list):
        return Expressions(*obj).to_sql()
    else:
        raise TypeError()


class AstBase(dict):
    def tokens(self):
        yield ""

    def to_sql(self):
        return " ".join(self.tokens())


class Expressions(list):
    def __init__(self, *args):
        for x in args:
            self.append(x)

    def to_sql(self):
        return ", ".join(x for x in self.tokens())

    def tokens(self):
        yield from tokenize(self)


class Bracket(AstBase):
    def __init__(self, expr: Expressions = None, alias: str = None):
        self["type"] = "bracket"
        self["expr"] = expr
        self["alias"] = alias

    def tokens(self):
        yield "(" + to_sql(self["expr"]) + ")"


class Prefix(AstBase):
    def __init__(self, op: str, expr: Expressions, alias: str = None):
        self["type"] = "prefix"
        self["op"] = op
        self["expr"] = expr

    def tokens(self):
        yield self["op"] + to_sql(self["expr"][0])


class Postfix(AstBase):
    def __init__(self, op: str, expr: Expressions, alias: str = None):
        self["type"] = "postfix"
        self["op"] = op
        self["expr"] = expr

    def tokens(self):
        yield to_sql(self["expr"][0]) + self["op"]


class BinaryOperator(AstBase):
    def __init__(self, op: str, expr: Expressions, alias: str = None):
        self["type"] = "bo"
        self["op"] = op
        self["expr"] = expr
        self["alias"] = alias

    def tokens(self):
        yield to_sql(self["expr"][0])
        yield self["op"]
        yield to_sql(self["expr"][1])


# def get_name(self: dict):
#     name = Name.get_name(self["name"])

#     if self["parent"] is not None:
#         return Name.get_name(self["parent"]) + "." + name
#     else:
#         return name


class Name(AstBase):
    def __init__(self, value: str, quote=True):
        self["type"] = "name"
        self["value"] = value
        self["quote"] = quote

    def tokens(self):
        if self["quote"]:
            yield '"' + self["value"] + '"'
        else:
            yield self["value"]

    def to_str(self):
        return "".join(self.tokens())

    @classmethod
    def get_name(cls, name):
        if isinstance(name, str):
            return Name(name, quote=False).to_str()
        elif isinstance(name, Name):
            return name.to_str()
        else:
            raise TypeError()

    @classmethod
    def from_obj(cls, name):
        if isinstance(name, str):
            return Name(name, quote=False)
        elif isinstance(name, Name):
            return Name(name["value"], name["quote"])
        else:
            raise TypeError()


class Identifier(AstBase):
    def __init__(self, name: str, parent: str = None, alias: str = None):
        self["type"] = "identifier"
        self["name"] = name
        self["parent"] = parent
        self["alias"] = alias

    def get_name(self: dict):
        name = Name.get_name(self["name"])

        if self["parent"] is not None:
            return Name.get_name(self["parent"]) + "." + name
        else:
            return name

    def tokens(self):
        yield self.get_name()


class Table(Identifier):
    ...


class Column(Identifier):
    ...


# class Func(Identifier):
#     ...


class Func(Identifier):
    def __init__(
        self, name: str, parent: str = None, args: Expressions = None, alias: str = None
    ):
        self["type"] = "func"
        self["name"] = name
        self["parent"] = parent
        self["expr"] = args or []
        self["alias"] = alias

    def tokens(self):
        name = self.get_name()
        args = ", ".join(tokenize(self["expr"]))
        yield name + "(" + args + ")"

        # if self["alias"] is not None:
        #     yield str(self["alias"])


class Value(AstBase):
    def __init__(self, value, alias: str = None):
        self["type"] = "value"
        self["value"] = value
        self["alias"] = alias

    def tokens(self):
        val = self["value"]
        if isinstance(val, str):
            yield "'" + val + "'"
        elif val is None:
            yield "NULL"
        else:
            yield str(val)


class SelectStatement(AstBase):
    def __init__(
        self,
        returning: Expressions,
        from_: Expressions = None,
        joins: "Expressions[JoinStatement]" = None,
        groupby: Expressions = None,
        having: Expressions = None,
        where: Expressions = None,
        orderby: Expressions = None,
        window: Expressions = None,
        limit: Expressions = None,
        offset: Expressions = None,
        unions: "Expressions[UnionStatement]" = None,
    ):
        dic = locals()
        self["type"] = "SELECT"

        for key in {
            "returning",
            "from_",
            "joins",
            "groupby",
            "having",
            "where",
            "orderby",
            "window",
            "limit",
            "offset",
            "unions",
        }:
            val = dic[key]
            if val is not None:
                self[key] = val

    def tokens(self):
        yield "SELECT"
        yield to_sql(self["returning"])

        if self.get("from_", None):
            yield "FROM"
            yield to_sql(self["from_"])

        if self.get("joins", None):
            yield to_sql(self["joins"])

        if self.get("groupby", None):
            yield "GROUP BY"
            yield to_sql(self["groupby"])

        if self.get("having", None):
            yield "HAVING"
            yield to_sql(self["having"])

        if self.get("where", None):
            yield "WHERE"
            yield to_sql(self["where"])

        if self.get("orderby", None):
            yield "ORDER BY"
            yield to_sql(self["orderby"])

        if self.get("window", None):
            yield "WINDOW"
            yield to_sql(self["window"])

        if self.get("limit", None):
            yield "LIMIT"
            yield to_sql(self["limit"])

        if self.get("offset", None):
            yield "OFFSET"
            yield to_sql(self["offset"])

        if self.get("unions", None):
            yield to_sql(self["unions"])


class JoinStatement(AstBase):
    def __init__(self, join_type: str, from_, on=None, using=None):
        self["type"] = "join"

        if join_type is None:
            join_type = "INNER"

        self["join_type"] = join_type
        self["from_"] = from_

        if on is not None:
            self["on"] = on

        if using is not None:
            self["using"] = using

    def tokens(self):
        yield self["join_type"]
        yield "JOIN"
        yield to_sql(self["from_"])

        if "on" in self:
            yield "ON"
            yield to_sql(self["on"])

        if "using" in self:
            yield "USING(" + to_sql(self["using"]) + ")"


class UnionStatement(AstBase):
    def __init__(self, union_type: str, select, alias: str = None):
        self["type"] = "union"
        self["union_type"] = union_type  # UNION, INTERSECT, EXCEPT
        self["select"] = select  # UNION, INTERSECT, EXCEPT

    def tokens(self):
        yield self["union_type"]
        yield to_sql(self["select"])
