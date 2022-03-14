from dataclasses import dataclass, field
from functools import lru_cache
from typing import TYPE_CHECKING, Any, List, Optional, TypedDict, Union, no_type_check


class Node:
    tag: str

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, tag=self._tag())

    @classmethod
    @lru_cache(maxsize=20)
    def _tag(cls):
        return cls.__name__.upper()


class Terminal(Node):
    ...


@dataclass
class Table(Terminal):
    name: str
    schema: Optional[str]
    alias: Optional[str]


@dataclass
class Column(Terminal):
    name: str
    table: Optional[str]
    table_alias: Optional[str]
    alias: Optional[str]


@dataclass
class Star(Column):
    name: str = field(default="*", init=False)
    table: Optional[str]
    table_alias: None
    alias: None


@dataclass
class Func(Terminal):
    name: str
    schema: Optional[str]
    alias: Optional[str]
    nodes: List[Node]
    anonymous: bool


@dataclass
class Value(Terminal):
    value: Any


@dataclass
class Param(Terminal):
    name: str


class Expr(Node):
    name: str
    nodes: List[Node]


@dataclass
class Select(Expr):
    expr: str = field(default="SELECT", init=False)
    nodes: List[Union["Returning", "Query", "Union_", "UnionAll", "Except"]]

    def get_tables(self):
        return []

    def get_columns(self):
        return []


@dataclass
class Returning(Expr):
    expr: str = field(default="RETURNING", init=False)
    nodes: List[Union["Expr", Terminal]]

    def to_select(self):
        return Select(nodes=[self])

    def get_columns(self):
        return []


@dataclass
class Query(Expr):
    expr: str = field(default="QUERY", init=False)
    nodes: List[Union["From", "Where", "Join", "OrderBy", "Limit", "Offset"]]

    def get_tables(self):
        return []

    def to_select(self):
        star = Star()
        return Select(nodes=[self, Returning(nodes=[star])])


@dataclass
class From(Expr):
    expr: str = field(default="FROM", init=False)
    nodes: List[Union["Expr", Terminal]]

    def to_select(self):
        query = Query(nodes=[self])
        return query.to_select()

    def get_tables(self):
        return []


@dataclass
class Join(Expr):
    expr: str = field(default="JOIN", init=False)
    nodes: List[Union["Expr", Terminal]]

    def get_tables(self):
        return []


@dataclass
class Where(Expr):
    expr: str = field(default="WHERE", init=False)
    nodes: List[Union["Expr", Terminal]]


@dataclass
class OrderBy(Expr):
    expr: str = field(default="ORDERBY", init=False)
    nodes: List[Union["Expr", Terminal]]


@dataclass
class Limit(Expr):
    expr: str = field(default="LIMIT", init=False)
    nodes: List[Union["Expr", Terminal]]


@dataclass
class Offset(Expr):
    expr: str = field(default="OFFSET", init=False)
    nodes: List[Union["Expr", Terminal]]


@dataclass
class Union_(Expr):
    expr: str = field(default="UNION", init=False)
    nodes: List["Select"]


@dataclass
class UnionAll(Expr):
    expr: str = field(default="UNIONALL", init=False)
    nodes: List["Select"]


@dataclass
class Except(Expr):
    expr: str = field(default="EXCEPT", init=False)
    nodes: List["Select"]


@dataclass
class Uo(Node):
    name: str
    op: str
    nodes: List[Node]

    def __str__(self):
        if not len(self.nodes) == 1:
            raise ValueError()

        return f"{self.op} {str(self.nodes[0])}"


@dataclass
class Op(Node):
    name: str
    op: str
    nodes: List[Node]

    def __str__(self):
        if len(self.nodes) > 1:
            raise ValueError()

        if len(self.nodes) > 2:
            return "(" + f" {self.op} ".join((str(x) for x in self.nodes)) + ")"
        else:
            return f"{self.op} ".join((str(x) for x in self.nodes))
