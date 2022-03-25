import pytest
from lark.exceptions import UnexpectedCharacters as _UnexpectedCharacters

from sqlcommon import get_parser

# http://teiid.github.io/teiid-documents/9.0.x/content/reference/BNF_for_SQL_Grammar.html


def UnexpectedCharacters():
    return _UnexpectedCharacters(" ", 0, 0, 0)


@pytest.fixture(scope="session")
def value_parser():
    return get_parser(start="value", cls_transformer=None)


@pytest.fixture(scope="session")
def expr_parser():
    return get_parser(start="expr", cls_transformer=None)


@pytest.fixture(scope="session")
def stmt_parser():
    return get_parser(start="stmt", cls_transformer=None)


@pytest.fixture(scope="session")
def parser():
    return get_parser(start="stmt")


# TODO: 既知のバグを直す
def test_new_parser_bug():
    new_parse = get_parser(start="value", cls_transformer=None)

    with pytest.raises(Exception):
        assert new_parse("''-- comment\n''").data == "str"  # コメントをはさめること
        assert new_parse("''/*\n comment\n*/''").data == "str"  # コメントをはさめること
        assert (
            new_parse('select "users1".* from users1')
            == "SELECT 'users'.* FROM users1"  # ダブルクォートでない＆1が消えている
        )
        assert new_parse("select 'a''b'") == "SELECT 'ab'"  # シングルクォートが消えている


_args = (0,)


@pytest.mark.parametrize(
    "sql, type, size",
    [
        ("1", "int", 1),
        ("1.0", "float", 1),
        ("1.1", "float", 1),
        ("null", "null", *_args),
        ("NULL", "null", *_args),
        ("true", "true", *_args),
        ("True", "true", *_args),
        ("false", "false", *_args),
        ("FALSE", "false", *_args),
        ("'a'", "str", 1),
        ("''", "str", 1),
        ("''''", "str", 2),
        ("''  ''", "str", 2),
        ("'' -- comment ''", "str", 1),
        ("'' \n -- comment ''", "str", 1),
        ("'' -- comment\n ''", "str", 2),
        ("'' /* comment */ ''", "str", 2),
        ("'' \n /* comment */ ''", "str", 2),
        # ("'' /* comment \n */ ''", "str", 2),  # TODO: 解析エラー
        ("'' /* comment */ \n ''", "str", 2),
        ("'", UnexpectedCharacters(), *_args),
        ("'''", UnexpectedCharacters(), *_args),
    ],
)
def test_value_parser(value_parser, sql, type, size):
    if isinstance(type, Exception):
        with pytest.raises(type.__class__):
            value_parser(sql)
    else:
        result = value_parser(sql)
        assert result.data == type
        assert len(result.children) == size


@pytest.mark.parametrize(
    "sql, type",
    [
        ('"a"', "identifier"),
        ("a", "identifier"),
        ('"a"."b"', "identifier"),
        ("a.b", "identifier"),
        ('"a"()', "func"),
        ("a()", "func"),
        ('"a"."b"()', "func"),
        ("a.b()", "func"),
        ('"a"(1)', "func"),
        ("a(1)", "func"),
        ('"a"."b"(1)', "func"),
        ("a.b(1)", "func"),
        ('"a"(1,2)', "func"),
        ("a(1,2)", "func"),
        ('"a"."b"(1,2)', "func"),
        ("a.b(1,2)", "func"),
        ("a(\n1)", "func"),
        ("a(1\n)", "func"),
        ("a(\n1\n)", "func"),
    ],
)
def test_expr(expr_parser, sql, type):
    assert expr_parser(sql).data == type


@pytest.mark.parametrize(
    "keyword",
    ["select", "limit"],
)
def test_keywords(parser, keyword):
    with pytest.raises(Exception, match="Invalid syntax"):
        result = parser(f"select {keyword}")


@pytest.mark.parametrize(
    "sql, expect",
    [
        ("select 1", "SELECT 1"),
        ("select *", "SELECT *"),
        ("select * from users", "SELECT * FROM users"),
        ("select * from users where 1", "SELECT * FROM users WHERE 1"),
        ("select name from users", "SELECT name FROM users"),
        ("select sum() from users", "SELECT sum() FROM users"),
        ("select sum(1) from users", "SELECT sum(1) FROM users"),
        ("select sum(1, 2) from users", "SELECT sum(1, 2) FROM users"),
        ("select sum(name), 1+1 from users", "SELECT sum(name), 1 + 1 FROM users"),
        ("select id, name from users1", "SELECT id, name FROM users1"),
    ],
)
def test_transform(parser, sql, expect):
    if isinstance(type, Exception):
        with pytest.raises(type.__class__):
            parser(sql)
    else:
        result = parser(sql)
        result.to_sql() == expect


@pytest.mark.parametrize(
    "sql, expect",
    [
        (
            "select * from users1 join users2 on users1.id = users2.id, users1.name = users2.name",
            "SELECT * FROM users1 JOIN users2 ON users1.id = users2.id, users1.name = users2.name",
        ),
        (
            "select * from users1 join users2 using(id)",
            "SELECT * FROM users1 JOIN users2 USING(id)",
        ),
        (
            "select * from users1 inner join users2 using(id)",
            "SELECT * FROM users1 INNER JOIN users2 USING(id)",
        ),
        (
            "select * from users1 inner outer join users2 using(id)",
            UnexpectedCharacters(),
        ),
        (
            "select * from users1 cross join users2 using(id)",
            "SELECT * FROM users1 CROSS JOIN users2 USING(id)",
        ),
        (
            "select * from users1 cross outer join users2 using(id)",
            UnexpectedCharacters(),
        ),
        (
            "select * from users1 left join users2 using(id)",
            "SELECT * FROM users1 LEFT JOIN users2 USING(id)",
        ),
        (
            "select * from users1 left outer join users2 using(id)",
            "SELECT * FROM users1 LEFT OUTER JOIN users2 USING(id)",
        ),
        (
            "select * from users1 right join users2 using(id)",
            "SELECT * FROM users1 RIGHT JOIN users2 USING(id)",
        ),
        (
            "select * from users1 right outer join users2 using(id)",
            "SELECT * FROM users1 RIGHT OUTER JOIN users2 USING(id)",
        ),
        (
            "select * from users1 full join users2 using(id)",
            "SELECT * FROM users1 FULL JOIN users2 USING(id)",
        ),
        (
            "select * from users1 full outer join users2 using(id,name)",
            "SELECT * FROM users1 FULL outer JOIN users2 USING(id,name)",
        ),
    ],
)
def test_join(parser, sql, expect):
    if isinstance(expect, Exception):
        with pytest.raises(expect.__class__):
            parser(sql)
    else:
        result = parser(sql)
        result.to_sql() == expect
