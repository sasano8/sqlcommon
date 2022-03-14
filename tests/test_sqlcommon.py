import pytest
from lark.exceptions import UnexpectedCharacters

from sqlcommon import new_parse, parse


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
    assert new_parse("1").data == "int"
    assert new_parse("1.0").data == "float"
    assert new_parse('"a"').data == "identifier"
    assert new_parse("a").data == "identifier"
    assert new_parse("null").data == "null"
    assert new_parse("NULL").data == "null"
    assert new_parse("true") == True
    assert new_parse("True") == True
    assert new_parse("false") == False
    assert new_parse("FALSE") == False
    assert new_parse("'a'").data == "str"
    assert new_parse("''").data == "str"
    assert new_parse("''''").data == "str"

    with pytest.raises(UnexpectedCharacters):
        assert new_parse("'")

    with pytest.raises(UnexpectedCharacters):
        assert new_parse("'''")
