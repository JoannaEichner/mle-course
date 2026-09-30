from shelfwise import cleaning


def test_keep_products_drops_postage(lines):
    kept = cleaning.keep_products(lines)
    assert "POST" not in set(kept["stock_code"])
    assert len(kept) == 5


def test_split_returns_marks_cancellations(lines):
    out = cleaning.split_returns(cleaning.keep_products(lines))
    assert out["qty_returned"].tolist() == [0, 4, 0, 0, 0]
    assert out["qty_sold"].tolist() == [10, 0, 6, 5, 0]
