import os
from typing import Literal

from lark import Lark, Transformer, v_args

path = os.path.dirname(__file__)


def Node(name, arr):
    return (name, arr)


def Term(val):
    return ("TERM", val)


class CommonTransformer(Transformer):
    true = lambda self, _: True
    false = lambda self, _: False
    int = v_args(inline=True)(int)
    float = v_args(inline=True)(float)
    null = lambda self, _: None
    STAR = str
    BOPS = v_args(inline=True)(str)
    SIGN = v_args(inline=True)(str)

    def RESERVED_WORDS(self, tree):
        raise NotImplementedError(f"Invalid syntax: {str(tree)}")

    def STRING_LITERAL(self, s):
        return s[1:-1]

    def str(self, strings):
        return "".join(strings)

    @v_args(inline=True)
    def NAME(self, s):
        if s[0] == '"' and s[len(s) - 1] == '"':
            s = s[1 : len(s) - 2]
            return s
        else:
            return str(s)

    @v_args(inline=True)
    def alias_string(self, s):
        return self.NAME(s)

    def identifier(self, tree):
        schema_or_table, name = tree
        return {"type": "identifier", "parent": schema_or_table, "name": name}

    def func(self, tree):
        schema_or_table, name, expr = tree
        return {"type": "func", "parent": schema_or_table, "name": name, "args": [expr]}

    def item(self, tree):
        obj, alias = tree
        if isinstance(obj, dict):
            obj["is_item"] = True
            obj["alias"] = alias
        else:
            obj = {"type": "value", "value": obj, "alias": alias, "is_item": True}

        return obj

    def ASC_OR_DESC(self, tree):
        return str(tree).upper()

    def sign_expr(self, tree):
        return {"type": "bo", "op": tree[0], "expr": [tree[1]]}

    def bo_expr(self, tree):
        return {"type": "bo", "op": tree[1], "expr": [tree[0], tree[2]]}

    def expr(self, tree):
        return tree

    items = lambda self, tree: list(tree)
    order_items = lambda self, tree: list(tree)


class SelectTransformer(CommonTransformer):
    returning_stmt = lambda self, tree: Node("RETURNING", tree[0])
    from_stmt = lambda self, tree: Node("FROM", tree[0])
    orderby_stmt = lambda self, tree: Node("ORDERBY", tree[0])
    groupby_stmt = lambda self, tree: Node("GROUPBY", tree[0])
    where_stmt = lambda self, tree: Node("WHERE", tree[0])
    having_stmt = lambda self, tree: Node("HAVING", tree[0])
    window_stmt = lambda self, tree: Node("WINDOW", tree[0])
    limit_stmt = lambda self, tree: Node("LIMIT", tree[0])
    offset_stmt = lambda self, tree: Node("OFFSET", tree[0])

    query_stmt = lambda self, tree: Node("QUERY", list(tree))

    union_all_stmt = lambda self, tree: self._union_stmt("UNION", tree)
    intersect_stmt = lambda self, tree: self._union_stmt("INTERSECT", tree)
    except_stmt = lambda self, tree: self._union_stmt("EXCEPT", tree)

    def order_item(self, tree):
        obj, asc_or_desc = tree
        if asc_or_desc == "ASC":
            is_asc = True
        elif asc_or_desc == "DESC":
            is_asc = False
        elif asc_or_desc is None:
            is_asc = None
        else:
            raise RuntimeError()

        obj["is_asc"] = is_asc
        return obj

    def join_stmt(self, tree):
        items, expression = tree
        return Node("JOIN", [Node("FROM", items), expression])

    def join_on_items(self, tree):
        (expressions,) = tree
        return expressions

    def join_using_items(self, tree):
        (names,) = tree
        return names

    def join_on_stmt(self, tree):
        (expressions,) = tree
        return Node("ON", expressions)

    def join_using_stmt(self, tree):
        (names,) = tree
        return Node("USING", names)

    def _union_stmt(self, union_name, tree):
        return Node(union_name, list(tree))

    def select(self, tree):
        returning_stmt, query_stmt, orderby_stmt, union_stmt = tree
        # evalute order
        dic = {
            "FROM": [],
            "JOIN": [],
            "WHERE": [],
            "GROUPBY": [],
            "HAVING": [],
            "RETURNING": [returning_stmt[1]],
            "ORDERBY": [],
            "WINDOW": [],
            "LIMIT": [],
            "OFFSET": [],
            "UNION": [],
            "INTERSECT": [],
            "EXCEPT": [],
        }

        if query_stmt is None:
            query_stmt = []
        else:
            query_stmt = query_stmt[1]

        for stmt in query_stmt:
            if stmt is not None:
                dic[stmt[0]].append(stmt[1])

        for stmt in orderby_stmt or []:
            dic[stmt[0]].append(stmt[1])

        for stmt in union_stmt or []:
            dic[stmt[0]].append(stmt[1])

        u1 = dic.pop("UNION", None)
        u2 = dic.pop("INTERSECT", None)
        u3 = dic.pop("EXCEPT", None)

        if u1:
            dic.setdefault("UNION", []).append({"UNION": u1})

        if u2:
            dic.setdefault("UNION", []).append({"INTERSECT": u2})

        if u3:
            dic.setdefault("UNION", []).append({"EXCEPT": u3})

        for values in dic.values():
            if len(values) > 1:
                raise RuntimeError()

        return {"type": "SELECT", **{k: v[0] for k, v in dic.items() if len(v) == 1}}


class SqlTransformer(SelectTransformer):
    ...


def parse(text: str):
    with open(path + "/grammer.lark") as grammer:
        parser = Lark(grammer.read(), start="start")
        tree = parser.parse(text)
        result = SqlTransformer().transform(tree)
        return result


def new_parse(text: str):
    with open(path + "/grammer2.lark") as grammer:
        parser = Lark(grammer.read(), start="start")
        tree = parser.parse(text)
        result = SqlTransformer().transform(tree)
        return result


def get_parser(
    start: Literal["start", "value", "stmt"] = "start", cls_transformer=SqlTransformer
):
    with open(path + "/grammer2.lark") as grammer:
        parser = Lark(grammer.read(), start=start)

        if cls_transformer is None:

            def parse(text: str):
                tree = parser.parse(text)
                return tree

        else:
            transformer = cls_transformer()

            def parse(text: str):
                tree = parser.parse(text)
                result = transformer.transform(tree)
                return result

        return parse
