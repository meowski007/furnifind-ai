from app.services.search.query_parser import QueryParser


def test_query_parser_price_and_category():
    query = "Scandinavian light oak study desk under ₹15000"
    filters, residual = QueryParser.parse_query(query)

    assert filters.category == "desks"
    assert filters.max_price == 15000.0
    assert filters.style == "scandinavian"
    assert filters.material == "oak"


def test_query_parser_width_and_budget():
    query = "Find a modern desk width below 120 cm and budget 20000"
    filters, residual = QueryParser.parse_query(query)

    assert filters.category == "desks"
    assert filters.max_width_cm == 120.0
    assert filters.max_price == 20000.0
    assert filters.style == "modern"


def test_query_parser_synonym_resolution():
    synonym_tests = [
        ("luxurious couch for living room", "sofas"),
        ("wooden workstation with drawers", "desks"),
        ("ergonomic task chair for office", "chairs"),
        ("marble dining table for 4", "tables"),
        ("ladder bookshelf for study", "bookcases"),
        ("contemporary bedside lamp", "lighting"),
    ]
    for q, expected_cat in synonym_tests:
        filters, _ = QueryParser.parse_query(q)
        assert filters.category == expected_cat, (
            f"Failed resolving {q} to {expected_cat}, got {filters.category}"
        )


def test_query_parser_colour_and_material():
    query = "emerald green velvet accent armchair"
    filters, residual = QueryParser.parse_query(query)

    assert filters.category == "chairs"
    assert filters.material == "velvet"
    assert filters.colour == "emerald green"


def test_query_parser_empty_or_generic():
    query = "something nice for the apartment"
    filters, residual = QueryParser.parse_query(query)

    assert filters.category is None
    assert filters.max_price is None
    assert filters.max_width_cm is None
