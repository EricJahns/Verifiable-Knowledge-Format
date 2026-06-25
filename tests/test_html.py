from pathlib import Path

from vkf.html import render_html, write_html

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def test_render_html_is_self_contained():
    html = render_html(EXAMPLES)
    assert html.startswith("<!DOCTYPE html>")
    # No external resources — the whole point is a single offline file.
    assert "http://" not in html.split("<script>")[0].replace("http://www.w3.org/2000/svg", "")
    assert "src=" not in html
    # Data is embedded, not fetched.
    assert "__DATA__" not in html
    assert "metric:activation_rate" in html


def test_write_html(tmp_path):
    out = write_html(EXAMPLES, tmp_path / "graph.html")
    assert out.exists()
    assert out.read_text().count("<script>") == 1
