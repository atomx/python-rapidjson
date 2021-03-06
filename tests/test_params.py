from datetime import date, datetime, time
import math
import pytest
import rapidjson


@pytest.mark.unit
def test_skipkeys():
    o = {True: False, 1: 1, 1.1: 1.1, (1,2): "foo", b"asdf": 1, None: None}

    with pytest.raises(TypeError):
        rapidjson.dumps(o)

    with pytest.raises(TypeError):
        rapidjson.dumps(o, skipkeys=False)

    assert rapidjson.dumps(o, skipkeys=True) == '{}'


@pytest.mark.unit
def test_ensure_ascii():
    s = '\N{GREEK SMALL LETTER ALPHA}\N{GREEK CAPITAL LETTER OMEGA}'
    assert rapidjson.dumps(s) == '"\\u03b1\\u03a9"'
    assert rapidjson.dumps(s, ensure_ascii=True) == '"\\u03b1\\u03a9"'
    assert rapidjson.dumps(s, ensure_ascii=False) == '"%s"' % s


@pytest.mark.unit
def test_allow_nan():
    f = [1.1, float("inf"), 2.2, float("nan"), 3.3, float("-inf"), 4.4]
    expected = '[1.1,Infinity,2.2,NaN,3.3,-Infinity,4.4]'
    assert rapidjson.dumps(f) == expected
    assert rapidjson.dumps(f, allow_nan=True) == expected

    with pytest.raises(ValueError):
        rapidjson.dumps(f, allow_nan=False)

    s = "NaN"
    assert math.isnan(rapidjson.loads(s))
    assert math.isnan(rapidjson.loads(s, allow_nan=True))

    with pytest.raises(ValueError):
        rapidjson.loads(s, allow_nan=False)

    s = "Infinity"
    assert rapidjson.loads(s) == float("inf")
    assert rapidjson.loads(s, allow_nan=True) == float("inf")

    with pytest.raises(ValueError):
        rapidjson.loads(s, allow_nan=False)

    s = "-Infinity"
    assert rapidjson.loads(s) == float("-inf")
    assert rapidjson.loads(s, allow_nan=True) == float("-inf")

    with pytest.raises(ValueError):
        rapidjson.loads(s, allow_nan=False)


@pytest.mark.unit
def test_indent():
    o = {"a": 1, "z": 2, "b": 3}
    expected1 = '{\n    "a": 1,\n    "z": 2,\n    "b": 3\n}'
    expected2 = '{\n    "a": 1,\n    "b": 3,\n    "z": 2\n}'
    expected3 = '{\n    "b": 3,\n    "a": 1,\n    "z": 2\n}'
    expected4 = '{\n    "b": 3,\n    "z": 2,\n    "a": 1\n}'
    expected5 = '{\n    "z": 2,\n    "a": 1,\n    "b": 3\n}'
    expected6 = '{\n    "z": 2,\n    "b": 3,\n    "a": 1\n}'
    expected = (
        expected1,
        expected2,
        expected3,
        expected4,
        expected5,
        expected6)

    assert rapidjson.dumps(o, indent=4) in expected

    with pytest.raises(TypeError):
        rapidjson.dumps(o, indent="\t")


@pytest.mark.unit
def test_sort_keys():
    o = {"a": 1, "z": 2, "b": 3}
    expected1 = '{"a":1,"b":3,"z":2}'
    expected2 = '{\n    "a": 1,\n    "b": 3,\n    "z": 2\n}'

    assert rapidjson.dumps(o, sort_keys=True) == expected1
    assert rapidjson.dumps(o, sort_keys=True, indent=4) == expected2


@pytest.mark.unit
def test_default():
    class Bar:
        pass

    class Foo:
        def __init__(self):
            self.foo = "bar"

    def default(obj):
        if isinstance(obj, Foo):
            return {"foo": obj.foo}

        raise TypeError("default error")

    o = {"asdf": Foo()}
    assert rapidjson.dumps(o, default=default) == '{"asdf":{"foo":"bar"}}'

    o = {"asdf": Foo(), "qwer": Bar()}
    with pytest.raises(TypeError):
        rapidjson.dumps(o, default=default)

    with pytest.raises(TypeError):
        rapidjson.dumps(o)


@pytest.mark.unit
def test_use_decimal():
    import math
    from decimal import Decimal

    dstr = "2.7182818284590452353602874713527"
    d = Decimal(dstr)

    with pytest.raises(TypeError):
        rapidjson.dumps(d)

    assert rapidjson.dumps(float(dstr)) == str(math.e)
    assert rapidjson.dumps(d, use_decimal=True) == dstr
    assert rapidjson.dumps({"foo": d}, use_decimal=True) == '{"foo":%s}' % dstr

    assert rapidjson.loads(
        rapidjson.dumps(d, use_decimal=True),
        use_decimal=True) == d

    assert rapidjson.loads(rapidjson.dumps(d, use_decimal=True)) == float(dstr)


@pytest.mark.unit
def test_max_recursion_depth():
    a = {'a': {'b': {'c': 1}}}

    assert rapidjson.dumps(a) == '{"a":{"b":{"c":1}}}'

    with pytest.raises(OverflowError):
        rapidjson.dumps(a, max_recursion_depth=2)


@pytest.mark.unit
def test_datetime_mode_dumps():
    import pytz

    assert rapidjson.DATETIME_MODE_NONE == 0
    assert rapidjson.DATETIME_MODE_ISO8601 == 1
    assert rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ == 2
    assert rapidjson.DATETIME_MODE_ISO8601_UTC == 3

    d = datetime.utcnow()
    dstr = d.isoformat()

    with pytest.raises(TypeError):
        rapidjson.dumps(d)

    with pytest.raises(ValueError):
        rapidjson.dumps(d, datetime_mode=42)

    with pytest.raises(ValueError):
        rapidjson.loads('""', datetime_mode=42)

    with pytest.raises(TypeError):
        rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_NONE)

    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == '"%s"' % dstr
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ) == '"%s"' % dstr

    d = d.replace(tzinfo=pytz.utc)
    dstr = utcstr = d.isoformat()

    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == '"%s"' % dstr
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ) == '"%s"' % dstr[:-6]

    d = d.astimezone(pytz.timezone('Pacific/Chatham'))
    dstr = d.isoformat()

    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == '"%s"' % dstr
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ) == '"%s"' % dstr[:-6]

    d = d.astimezone(pytz.timezone('Asia/Kathmandu'))
    dstr = d.isoformat()

    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == '"%s"' % dstr
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ) == '"%s"' % dstr[:-6]

    d = d.astimezone(pytz.timezone('America/New_York'))
    dstr = d.isoformat()

    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == '"%s"' % dstr
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ) == '"%s"' % dstr[:-6]
    assert rapidjson.dumps(d, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_UTC) == '"%s"' % utcstr


@pytest.mark.unit
def test_datetime_mode_loads():
    import pytz

    utc = datetime.now(pytz.utc)
    utcstr = utc.isoformat()

    jsond = rapidjson.dumps(utc, datetime_mode=rapidjson.DATETIME_MODE_ISO8601)

    assert jsond == '"%s"' % utcstr
    assert rapidjson.loads(jsond, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == utc

    local = utc.astimezone(pytz.timezone('Europe/Rome'))
    locstr = local.isoformat()

    jsond = rapidjson.dumps(local, datetime_mode=rapidjson.DATETIME_MODE_ISO8601)

    assert jsond == '"%s"' % locstr
    assert rapidjson.loads(jsond) == locstr
    assert rapidjson.loads(jsond, datetime_mode=rapidjson.DATETIME_MODE_ISO8601) == local

    load_as_utc = rapidjson.loads(jsond, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_UTC)

    assert load_as_utc == utc
    assert not load_as_utc.utcoffset()

    load_as_naive = rapidjson.loads(jsond, datetime_mode=rapidjson.DATETIME_MODE_ISO8601_IGNORE_TZ)

    assert load_as_naive == local.replace(tzinfo=None)


@pytest.mark.unit
@pytest.mark.parametrize(
    'value', [date.today(), datetime.now(), time(10,20,30)])
def test_datetime_values(value):
    with pytest.raises(TypeError):
        rapidjson.dumps(value)

    dumped = rapidjson.dumps(value, datetime_mode=rapidjson.DATETIME_MODE_ISO8601)
    loaded = rapidjson.loads(dumped, datetime_mode=rapidjson.DATETIME_MODE_ISO8601)
    assert loaded == value


@pytest.mark.unit
@pytest.mark.parametrize(
    'value,cls', [
        ('x999-02-03', str),
        ('1999 02 03', str),
        ('x0:02:20', str),
        ('20.02:20', str),
        ('x999-02-03T10:20:30', str),
        ('1999-02-03t10:20:30', str),

        ('0000-01-01', str),
        ('0001-99-99', str),
        ('0001-01-32', str),
        ('0001-02-29', str),

        ('24:02:20', str),
        ('23:62:20', str),
        ('23:02:62', str),
        ('20:02:20.123-25:00', str),
        ('20:02:20.123-05:61', str),

        ('1968-02-29', date),
        ('1999-02-03', date),

        ('20:02:20', time),
        ('20:02:20Z', time),
        ('20:02:20.123', time),
        ('20:02:20.123Z', time),
        ('20:02:20-05:00', time),
        ('20:02:20.123456', time),
        ('20:02:20.123456Z', time),
        ('20:02:20.123-05:00', time),
        ('20:02:20.123456-05:00', time),

        ('1999-02-03T10:20:30', datetime),
        ('1999-02-03T10:20:30Z', datetime),
        ('1999-02-03T10:20:30.123', datetime),
        ('1999-02-03T10:20:30.123Z', datetime),
        ('1999-02-03T10:20:30-05:00', datetime),
        ('1999-02-03T10:20:30.123456', datetime),
        ('1999-02-03T10:20:30.123456Z', datetime),
        ('1999-02-03T10:20:30.123-05:00', datetime),
        ('1999-02-03T10:20:30.123456-05:00', datetime),
    ])
def test_datetime_iso8601(value, cls):
    result = rapidjson.loads('"%s"' % value, datetime_mode=rapidjson.DATETIME_MODE_ISO8601)
    assert isinstance(result, cls)


@pytest.mark.unit
def test_precise_float():
    f = "1.234567890E+34"
    f1 = "1.2345678900000002e+34"

    assert rapidjson.loads(f) == float(f)
    assert rapidjson.loads(f, precise_float=True) == float(f)
    assert rapidjson.loads(f, precise_float=False) == float(f1)


@pytest.mark.unit
def test_object_hook():
    class Foo:
        def __init__(self, foo):
            self.foo = foo

    def hook(d):
        if 'foo' in d:
            return Foo(d['foo'])

        return d

    def default(obj):
        return {'foo': obj.foo}

    res = rapidjson.loads('{"foo": 1}', object_hook=hook)
    assert isinstance(res, Foo)
    assert res.foo == 1

    assert rapidjson.dumps(rapidjson.loads('{"foo": 1}', object_hook=hook),
            default=default) == '{"foo":1}'
    res = rapidjson.loads(rapidjson.dumps(Foo(foo="bar"), default=default),
            object_hook=hook)
    assert isinstance(res, Foo)
    assert res.foo == "bar"
