from sqlcommon import parse


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
