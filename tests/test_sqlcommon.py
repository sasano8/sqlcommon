import pytest
from lark.exceptions import UnexpectedCharacters

from sqlcommon import get_parser, new_parse, parse


def test_bug():

    try:
        result = parse("select 'a'")  # no from
        result = parse("select myfunc(1)")  # func
        result = parse("select myschema.myfunc(1)")  # schema + func
        result = parse("select 1 from users")  # number
        result = parse("select 'a' from users")  # string
    except:
        ...


def test_parse():
    result = parse("select name from users, users2")
    result = parse("select schema.name col1 from app.users t1, app.users2 t2")
    result = parse("select * from app.users")
    result = parse("select t1.name c1, t1.name c2 from app.users t1")
    result = parse('select * from "mytable"')  # 関数呼び出しに対応していない


# http://teiid.github.io/teiid-documents/9.0.x/content/reference/BNF_for_SQL_Grammar.html


def test_new_parser_bug():
    with pytest.raises(Exception):
        assert new_parse("''-- comment\n''").data == "str"  # コメントをはさめること
        assert new_parse("''/*\n comment\n*/''").data == "str"  # コメントをはさめること


def test_new_parser():
    new_parse = get_parser(start="value", cls_transformer=None)

    assert new_parse("1").data == "int"
    assert new_parse("1.0").data == "float"
    assert new_parse("null").data == "null"
    assert new_parse("NULL").data == "null"
    assert new_parse("true").data == "true"
    assert new_parse("True").data == "true"
    assert new_parse("false").data == "false"
    assert new_parse("FALSE").data == "false"
    assert new_parse("'a'").data == "str"
    assert new_parse("''").data == "str"
    assert new_parse("''''").data == "str"
    assert new_parse("''  ''").data == "str"
    assert new_parse("'' -- comment\n ''").data == "str"
    assert new_parse("'' /* comment */ ''").data == "str"

    with pytest.raises(UnexpectedCharacters):
        assert new_parse("'")

    with pytest.raises(UnexpectedCharacters):
        assert new_parse("'''")


def test_expr():
    new_parse = get_parser(start="expr", cls_transformer=None)

    assert new_parse('"a"').data == "identifier"
    assert new_parse("a").data == "identifier"
    assert new_parse('"a"."b"').data == "identifier"
    assert new_parse("a.b").data == "identifier"
    assert new_parse('"a"()').data == "func"
    assert new_parse("a()").data == "func"
    assert new_parse('"a"."b"()').data == "func"
    assert new_parse("a.b()").data == "func"
    assert new_parse('"a"(1)').data == "func"
    assert new_parse("a(1)").data == "func"
    assert new_parse('"a"."b"(1)').data == "func"
    assert new_parse("a.b(1)").data == "func"
    assert new_parse("a(\n1)").data == "func"
    assert new_parse("a(1\n)").data == "func"
    assert new_parse("a(\n1\n)").data == "func"


def test_stmt():
    new_parse = get_parser(start="stmt", cls_transformer=None)

    assert new_parse("select 1")
    assert new_parse("select *")
    assert new_parse("select * from users")
    assert new_parse("select * from users where 1")


def test_keywords():
    new_parse = get_parser(start="stmt")

    with pytest.raises(Exception, match="Invalid syntax"):
        result = new_parse("select limit")


def test_transform():
    new_parse = get_parser(start="stmt")
    # result = new_parse("select 'a''b', sum(1) order by name asc")
    # result = new_parse("select name + 1 from users")
    result = new_parse("select name from users")

    assert result["type"] == "SELECT"
    assert [(x["type"], x["name"]) for x in result["RETURNING"]] == [
        ("identifier", "name")
    ]
    assert [(x["type"], x["name"]) for x in result["FROM"]] == [("identifier", "users")]
    import json

    result = new_parse("select sum(name), 1 + 1 from users")
    print(json.dumps(result, indent=2))

    result = new_parse("select 1 from users")
    assert result


def test_join():
    new_parse = get_parser(start="stmt")
    result = new_parse("select * from users1 join users2 on users1.id = users2.id")
    result = new_parse("select * from users1 join users2 using(id)")
