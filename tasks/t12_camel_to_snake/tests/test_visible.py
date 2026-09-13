from solution import camel_to_snake


def test_example_1():
    assert camel_to_snake("camelCase") == "camel_case"


def test_example_2():
    assert camel_to_snake("PascalCase") == "pascal_case"


def test_example_3():
    assert camel_to_snake("parseXMLFile") == "parse_x_m_l_file"
