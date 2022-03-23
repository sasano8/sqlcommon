from typing import Any, List, NamedTuple


def tokenize(it):
    for x in it:
        yield to_sql(x)


def to_sql(obj):
    if isinstance(obj, (AstBase, Expressions)):
        return obj.to_sql()
    elif isinstance(obj, (int, str, float, bool)):
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
        return " ".join(x for x in self.tokens())

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


class Identifier(AstBase):
    def __init__(self, name: str, parent: str = None, alias: str = None):
        self["type"] = "identifier"
        self["name"] = name
        self["parent"] = parent
        self["alias"] = alias

    def tokens(self):
        if self["parent"] is not None:
            yield to_sql(self["parent"]) + "." + self["name"]
        else:
            yield self["name"]


class Table(Identifier):
    ...


class Column(Identifier):
    ...


# class Func(Identifier):
#     ...


class Func(AstBase):
    def __init__(
        self, name: str, parent: str = None, args: Expressions = None, alias: str = None
    ):
        self["type"] = "func"
        self["name"] = name
        self["parent"] = parent
        self["args"] = args or []
        self["alias"] = alias

    def tokens(self):
        args = ", ".join(tokenize(self["args"]))

        if self["parent"] is not None:
            yield to_sql(self["parent"]) + "." + self["name"] + "(" + args + ")"
        else:
            yield self["name"] + "(" + args + ")"

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
            joins = self["joins"]
            yield "JOIN<NOT IMPLEMENT>"
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
            unions = self["unions"]
            yield "UNION<NOT IMPLEMENT>"
            yield to_sql(self["joins"])


class JoinStatement(AstBase):
    def __init__(self, join_type: str, from_, on=None, using=None):
        self["type"] = "join"
        self["join_type"] = join_type
        self["from_"] = from_
        self["on"] = on
        self["using"] = using


class UnionStatement(AstBase):
    def __init__(self, union_type: str, select, alias: str = None):
        self["type"] = "union"
        self["union_type"] = union_type  # UNION, INTERSECT, EXCEPT
        self["select"] = select  # UNION, INTERSECT, EXCEPT
