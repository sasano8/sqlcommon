import pytest
from lark.exceptions import UnexpectedCharacters

from sqlcommon import get_parser

# http://teiid.github.io/teiid-documents/9.0.x/content/reference/BNF_for_SQL_Grammar.html


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


def test_new_parser():
    new_parse = get_parser(start="value", cls_transformer=None)

    assert new_parse("1").data == "int"
    assert new_parse("1.0").data == "float"
    assert new_parse("1.1").data == "float"
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
    assert len(new_parse("'' -- comment ''").children) == 1
    assert len(new_parse("'' \n -- comment ''").children) == 1
    assert len(new_parse("'' -- comment\n ''").children) == 2
    assert new_parse("'' /* comment */ ''").data == "str"
    assert len(new_parse("'' /* comment */ ''").children) == 2
    assert len(new_parse("'' \n /* comment */ ''").children) == 2
    # assert len(new_parse("'' /* comment \n */ ''").children) == 2  # TODO: 解析エラー
    assert len(new_parse("'' /* comment */ \n ''").children) == 2

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
    assert [(x["type"], x["name"]) for x in result["returning"]] == [
        ("identifier", "name")
    ]
    assert [(x["type"], x["name"]) for x in result["from_"]] == [
        ("identifier", "users")
    ]
    import json

    result = new_parse("select sum(name), 1 + 1 from users")
    print(json.dumps(result, indent=2))

    result = new_parse("select 1 from users")
    assert result


def test_join():
    new_parse = get_parser(start="stmt")
    result = new_parse(
        "select * from users1 join users2 on users1.id = users2.id, users1.name = users2.name"
    )
    assert result
    result = new_parse("select * from users1 join users2 using(id)")
    assert result
    result = new_parse("select * from users1 inner join users2 using(id)")
    assert result

    with pytest.raises(UnexpectedCharacters):
        result = new_parse("select * from users1 inner outer join users2 using(id)")

    result = new_parse("select * from users1 cross join users2 using(id)")
    assert result

    with pytest.raises(UnexpectedCharacters):
        result = new_parse("select * from users1 cross outer join users2 using(id)")

    result = new_parse("select * from users1 left join users2 using(id)")
    assert result
    result = new_parse("select * from users1 left outer join users2 using(id)")
    assert result
    result = new_parse("select * from users1 right join users2 using(id)")
    assert result
    result = new_parse("select * from users1 right outer join users2 using(id)")
    assert result
    result = new_parse("select * from users1 full join users2 using(id)")
    assert result
    result = new_parse("select * from users1 full outer join users2 using(id,name)")
    assert result
    result = new_parse("select id, name from users1")
    assert result
    assert result.to_sql()
