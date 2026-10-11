import json
import os
import shutil
import yaml
import jsonschema
from pathlib import Path

def write_case(case_dir, recipe, params, body, meta, now, expected):
    case_dir.mkdir(parents=True, exist_ok=True)
    # Write recipe.yaml
    with open(case_dir / "recipe.yaml", "w", encoding="utf-8") as f:
        yaml.dump(recipe, f, sort_keys=False)
    # Write params.json
    with open(case_dir / "params.json", "w", encoding="utf-8") as f:
        json.dump(params, f, indent=2)
    # Write response.body (bytes)
    with open(case_dir / "response.body", "wb") as f:
        if isinstance(body, str):
            f.write(body.encode("utf-8"))
        else:
            f.write(body)
    # Write response.meta.json
    with open(case_dir / "response.meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    # Write now.txt
    with open(case_dir / "now.txt", "w", encoding="utf-8") as f:
        f.write(now.strip() + "\n")
    # Write expected.json
    with open(case_dir / "expected.json", "w", encoding="utf-8") as f:
        json.dump(expected, f, indent=2)

def base_recipe(id_slug, **kwargs):
    clean_slug = id_slug.replace("_", "-")
    kwargs.pop("features", None)
    kwargs.pop("timezone", None)
    r = {
        "spec": 1,
        "id": f"dev.peek.test.{clean_slug}",
        "version": 1,
        "name": f"Test {clean_slug}",
        "description": "Conformance test recipe",
        "fetch": {
            "url": "https://example.com/test",
            "format": kwargs.pop("format", "html"),
            "allowed_domains": ["example.com"],
            "min_interval_s": 300
        },
        "extract": kwargs.pop("extract", {"fields": {}}),
        "display": kwargs.pop("display", {"layout": "list", "row": {"primary": "val"}})
    }
    r.update(kwargs)
    return r

def base_meta(status=200, final_url="https://example.com/test", headers=None):
    return {
        "status": status,
        "final_url": final_url,
        "headers": headers or {"content-type": "text/html; charset=utf-8"}
    }

def base_expected(id_slug, status="ok", data=None, view=None, diag=None, error=None):
    clean_slug = id_slug.replace("_", "-")
    d = diag or {"fallbacks_used": [], "skipped_items": [], "warnings": []}
    return {
        "spec": 1,
        "recipe": {"id": f"dev.peek.test.{clean_slug}", "version": 1},
        "status": status,
        "data": data,
        "view": view,
        "diagnostics": d,
        "error": error
    }

def build_all(root_dir):
    cases_dir = root_dir / "conformance" / "cases"
    opt_dir = root_dir / "conformance" / "cases-optional"
    NOW = "2026-10-02T12:00:00+01:00"

    # --- CATEGORY 1: CSS Selectors (001 - 008) ---
    # 001-css-basic
    html_001 = "<html><body><h1 id='title'>Header</h1><p class='content'>Body Text</p></body></html>"
    rec_001 = base_recipe("css_basic", extract={
        "fields": {
            "title": {"from": [{"css": "h1#title"}]},
            "text": {"from": [{"css": "p.content"}]}
        }
    }, display={
        "layout": "kv",
        "items": [
            {"label": "Title", "value": "{title}"},
            {"label": "Text", "value": "{text}"}
        ]
    })
    write_case(cases_dir / "001-css-basic", rec_001, {}, html_001, base_meta(), NOW,
        base_expected("css_basic", data={"fields": {"title": "Header", "text": "Body Text"}, "lists": {}},
                      view={"title": None, "layout": "kv", "rows": None, "items": [{"label": "Title", "value": "Header"}, {"label": "Text", "value": "Body Text"}], "empty_text": None, "footer": None, "link": None}))

    # 002-css-attr-exact-and-prefix
    html_002 = "<html><body><a href='https://example.com/start' data-kind='primary'>Link 1</a><a href='https://other.com/abc' data-kind='secondary'>Link 2</a></body></html>"
    rec_002 = base_recipe("css_attr_prefix", extract={
        "fields": {
            "first": {"from": [{"css": "a[data-kind='primary']"}]},
            "by_href": {"from": [{"css": "a[href^='https://other.com']"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{first}"}})
    write_case(cases_dir / "002-css-attr-exact-and-prefix", rec_002, {}, html_002, base_meta(), NOW,
        base_expected("css_attr_prefix", data={"fields": {"first": "Link 1", "by_href": "Link 2"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Link 1", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 003-css-attr-contains-and-hyphen
    html_003 = "<html><body><span data-tags='apple banana orange'>Fruit</span><span lang='en-GB'>British</span></body></html>"
    rec_003 = base_recipe("css_attr_contains", extract={
        "fields": {
            "fruit": {"from": [{"css": "span[data-tags*='banana']"}]},
            "lang": {"from": [{"css": "span[lang|='en']"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{fruit}"}})
    write_case(cases_dir / "003-css-attr-contains-and-hyphen", rec_003, {}, html_003, base_meta(), NOW,
        base_expected("css_attr_contains", data={"fields": {"fruit": "Fruit", "lang": "British"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Fruit", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 004-css-attr-case-insensitive
    html_004 = "<html><body><div data-status='ACTIVE'>Target</div></body></html>"
    rec_004 = base_recipe("css_attr_case_insensitive", extract={
        "fields": {
            "val": {"from": [{"css": "div[data-status='active' i]"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{val}"}})
    write_case(cases_dir / "004-css-attr-case-insensitive", rec_004, {}, html_004, base_meta(), NOW,
        base_expected("css_attr_case_insensitive", data={"fields": {"val": "Target"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Target", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 005-css-pseudo-is
    html_005 = "<html><body><main><article><h2>Selected Headline</h2></article></main></body></html>"
    rec_005 = base_recipe("css_pseudo_is", extract={
        "fields": {
            "headline": {"from": [{"css": ":is(h1, h2, h3)"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{headline}"}})
    write_case(cases_dir / "005-css-pseudo-is", rec_005, {}, html_005, base_meta(), NOW,
        base_expected("css_pseudo_is", data={"fields": {"headline": "Selected Headline"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Selected Headline", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 006-css-pseudo-not
    html_006 = "<html><body><ul id='items'><li class='hidden'>Skip</li><li>Keep Me</li></ul></body></html>"
    rec_006 = base_recipe("css_pseudo_not", extract={
        "fields": {
            "item": {"from": [{"css": "#items li:not(.hidden)"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{item}"}})
    write_case(cases_dir / "006-css-pseudo-not", rec_006, {}, html_006, base_meta(), NOW,
        base_expected("css_pseudo_not", data={"fields": {"item": "Keep Me"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Keep Me", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 007-css-scope-in-list
    html_007 = "<html><body><table><tbody><tr><td>Row 1</td><td>Meta 1</td></tr><tr><td>Row 2</td><td>Meta 2</td></tr></tbody></table></body></html>"
    rec_007 = base_recipe("css_scope_list", extract={
        "lists": {
            "rows": {
                "items": [{"css": "table tbody tr"}],
                "fields": {
                    "c1": {"from": [{"css": ":scope > td:first-child"}]},
                    "c2": {"from": [{"css": ":scope > td:nth-child(2)"}]}
                }
            }
        }
    }, display={
        "layout": "list",
        "source": "rows",
        "row": {"primary": "{c1}", "secondary": "{c2}"}
    })
    write_case(cases_dir / "007-css-scope-in-list", rec_007, {}, html_007, base_meta(), NOW,
        base_expected("css_scope_list", data={"fields": {}, "lists": {"rows": [{"c1": "Row 1", "c2": "Meta 1"}, {"c1": "Row 2", "c2": "Meta 2"}]}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Row 1", "secondary": "Meta 1", "trailing": None, "badge": None}, {"primary": "Row 2", "secondary": "Meta 2", "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 008-css-nested-combinators
    html_008 = "<html><body><div class='container'><p class='lead'>Intro</p><p class='body'>Detail</p></div></body></html>"
    rec_008 = base_recipe("css_combinators", extract={
        "fields": {
            "detail": {"from": [{"css": ".container > p.lead + p"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{detail}"}})
    write_case(cases_dir / "008-css-nested-combinators", rec_008, {}, html_008, base_meta(), NOW,
        base_expected("css_combinators", data={"fields": {"detail": "Detail"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Detail", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # --- CATEGORY 2: Locators (009 - 016) ---
    # 009-loc-attr
    html_009 = "<html><body><a id='main-link' href='/details/123'>Go</a></body></html>"
    rec_009 = base_recipe("loc_attr", extract={
        "fields": {
            "href": {"from": [{"css": "a#main-link", "attr": "href"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{href}"}})
    write_case(cases_dir / "009-loc-attr", rec_009, {}, html_009, base_meta(), NOW,
        base_expected("loc_attr", data={"fields": {"href": "/details/123"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "/details/123", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 010-loc-text-own
    html_010 = "<html><body><div id='box'>Direct Text<span>Child Text</span></div></body></html>"
    rec_010 = base_recipe("loc_text_own", extract={
        "fields": {
            "own": {"from": [{"css": "#box", "text": "own"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{own}"}})
    write_case(cases_dir / "010-loc-text-own", rec_010, {}, html_010, base_meta(), NOW,
        base_expected("loc_text_own", data={"fields": {"own": "Direct Text"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Direct Text", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 011-loc-text-all
    html_011 = "<html><body><div id='box'>Direct Text <span>Child Text</span></div></body></html>"
    rec_011 = base_recipe("loc_text_all", extract={
        "fields": {
            "all": {"from": [{"css": "#box", "text": "all"}], "transforms": [{"op": "collapse_ws"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{all}"}})
    write_case(cases_dir / "011-loc-text-all", rec_011, {}, html_011, base_meta(), NOW,
        base_expected("loc_text_all", data={"fields": {"all": "Direct Text Child Text"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Direct Text Child Text", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 012-loc-nth
    html_012 = "<html><body><ul><li>First</li><li>Second</li><li>Third</li></ul></body></html>"
    rec_012 = base_recipe("loc_nth", extract={
        "fields": {
            "second": {"from": [{"css": "ul li", "nth": 1}]}
        }
    }, display={"layout": "list", "row": {"primary": "{second}"}})
    write_case(cases_dir / "012-loc-nth", rec_012, {}, html_012, base_meta(), NOW,
        base_expected("loc_nth", data={"fields": {"second": "Second"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Second", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 013-loc-join
    html_013 = "<html><body><div class='tags'><span>Tech</span><span>News</span><span>AI</span></div></body></html>"
    rec_013 = base_recipe("loc_join", extract={
        "fields": {
            "tags": {"from": [{"css": ".tags span", "join": ", "}]}
        }
    }, display={"layout": "list", "row": {"primary": "{tags}"}})
    write_case(cases_dir / "013-loc-join", rec_013, {}, html_013, base_meta(), NOW,
        base_expected("loc_join", data={"fields": {"tags": "Tech, News, AI"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Tech, News, AI", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 014-loc-const
    html_014 = "<html><body><p>Unused Body</p></body></html>"
    rec_014 = base_recipe("loc_const", extract={
        "fields": {
            "status": {"from": [{"const": "Fixed Value"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{status}"}})
    write_case(cases_dir / "014-loc-const", rec_014, {}, html_014, base_meta(), NOW,
        base_expected("loc_const", data={"fields": {"status": "Fixed Value"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Fixed Value", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 015-loc-jsonpath-response
    json_015 = json.dumps({"data": {"user": {"name": "Alice", "role": "admin"}}})
    rec_015 = base_recipe("loc_jsonpath", format="json", extract={
        "fields": {
            "username": {"from": [{"json_path": "$.data.user.name"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{username}"}})
    write_case(cases_dir / "015-loc-jsonpath-response", rec_015, {}, json_015,
        base_meta(headers={"content-type": "application/json"}), NOW,
        base_expected("loc_jsonpath", data={"fields": {"username": "Alice"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Alice", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 016-loc-embedded-json
    html_016 = '<html><head><script id="__DATA__" type="application/json">{"items":[{"id":1,"val":"Apple"},{"id":2,"val":"Banana"}]}</script></head><body></body></html>'
    rec_016 = base_recipe("loc_embedded_json", extract={
        "lists": {
            "fruits": {
                "items": [{"css": "script#__DATA__", "json_path": "$.items[*]"}],
                "fields": {
                    "val": {"from": [{"json_path": "$.val"}]}
                }
            }
        }
    }, display={
        "layout": "list",
        "source": "fruits",
        "row": {"primary": "{val}"}
    })
    write_case(cases_dir / "016-loc-embedded-json", rec_016, {}, html_016, base_meta(), NOW,
        base_expected("loc_embedded_json", data={"fields": {}, "lists": {"fruits": [{"val": "Apple"}, {"val": "Banana"}]}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Apple", "secondary": None, "trailing": None, "badge": None}, {"primary": "Banana", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # --- CATEGORY 3: Fallbacks, Options, Defaults, and Skipping (017 - 024) ---
    # 017-fallback-first-succeeds
    html_017 = "<html><body><span class='primary'>Primary Value</span></body></html>"
    rec_017 = base_recipe("fb_first_ok", extract={
        "fields": {
            "v": {"from": [{"css": ".primary"}, {"css": ".secondary"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "017-fallback-first-succeeds", rec_017, {}, html_017, base_meta(), NOW,
        base_expected("fb_first_ok", data={"fields": {"v": "Primary Value"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Primary Value", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 018-fallback-second-succeeds
    html_018 = "<html><body><span class='secondary'>Secondary Fallback</span></body></html>"
    rec_018 = base_recipe("fb_second_ok", extract={
        "fields": {
            "v": {"from": [{"css": ".missing"}, {"css": ".secondary"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "018-fallback-second-succeeds", rec_018, {}, html_018, base_meta(), NOW,
        base_expected("fb_second_ok", status="degraded",
                      data={"fields": {"v": "Secondary Fallback"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Secondary Fallback", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None},
                      diag={"fallbacks_used": [{"path": "fields.v", "locator_index": 1}], "skipped_items": [], "warnings": []}))

    # 019-field-optional-null
    html_019 = "<html><body><h1>Title</h1></body></html>"
    rec_019 = base_recipe("field_optional", extract={
        "fields": {
            "title": {"from": [{"css": "h1"}]},
            "subtitle": {"from": [{"css": "h2"}], "optional": True}
        }
    }, display={"layout": "list", "row": {"primary": "{title}", "secondary": "{subtitle}"}})
    write_case(cases_dir / "019-field-optional-null", rec_019, {}, html_019, base_meta(), NOW,
        base_expected("field_optional", data={"fields": {"title": "Title", "subtitle": None}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Title", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 020-field-default-used
    html_020 = "<html><body><h1>Title</h1></body></html>"
    rec_020 = base_recipe("field_default", extract={
        "fields": {
            "badge": {"from": [{"css": "span.badge"}], "default": "N/A"}
        }
    }, display={"layout": "list", "row": {"primary": "{badge}"}})
    write_case(cases_dir / "020-field-default-used", rec_020, {}, html_020, base_meta(), NOW,
        base_expected("field_default", data={"fields": {"badge": "N/A"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "N/A", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 021-list-skipped-item
    html_021 = "<html><body><ul><li><h3>Item 1</h3></li><li><p>No heading</p></li><li><h3>Item 3</h3></li></ul></body></html>"
    rec_021 = base_recipe("list_skipped", extract={
        "lists": {
            "items": {
                "items": [{"css": "ul li"}],
                "min_items": 1,
                "fields": {
                    "heading": {"from": [{"css": "h3"}]}
                }
            }
        }
    }, display={"layout": "list", "source": "items", "row": {"primary": "{heading}"}})
    write_case(cases_dir / "021-list-skipped-item", rec_021, {}, html_021, base_meta(), NOW,
        base_expected("list_skipped", status="degraded",
                      data={"fields": {}, "lists": {"items": [{"heading": "Item 1"}, {"heading": "Item 3"}]}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Item 1", "secondary": None, "trailing": None, "badge": None}, {"primary": "Item 3", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None},
                      diag={"fallbacks_used": [], "skipped_items": [{"list": "items", "index": 1, "reason": "FIELD_MISSING:heading"}], "warnings": []}))

    # 022-list-min-items-pass
    html_022 = "<html><body><ul><li>One</li><li>Two</li></ul></body></html>"
    rec_022 = base_recipe("min_items_pass", extract={
        "lists": {
            "l": {
                "items": [{"css": "ul li"}],
                "min_items": 2,
                "fields": {"v": {"from": [{"css": ":scope"}]}}
            }
        }
    }, display={"layout": "list", "source": "l", "row": {"primary": "{v}"}})
    write_case(cases_dir / "022-list-min-items-pass", rec_022, {}, html_022, base_meta(), NOW,
        base_expected("min_items_pass", data={"fields": {}, "lists": {"l": [{"v": "One"}, {"v": "Two"}]}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "One", "secondary": None, "trailing": None, "badge": None}, {"primary": "Two", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 023-list-min-items-zero
    html_023 = "<html><body><ul></ul></body></html>"
    rec_023 = base_recipe("min_items_zero", extract={
        "lists": {
            "l": {
                "items": [{"css": "ul li"}],
                "min_items": 0,
                "fields": {"v": {"from": [{"css": ":scope"}]}}
            }
        }
    }, display={"layout": "list", "source": "l", "empty_text": "No items found", "row": {"primary": "{v}"}})
    write_case(cases_dir / "023-list-min-items-zero", rec_023, {}, html_023, base_meta(), NOW,
        base_expected("min_items_zero", data={"fields": {}, "lists": {"l": []}},
                      view={"title": None, "layout": "list", "rows": [], "items": None, "empty_text": "No items found", "footer": None, "link": None}))

    # 024-list-limit-applied
    html_024 = "<html><body><ul><li>1</li><li>2</li><li>3</li><li>4</li><li>5</li></ul></body></html>"
    rec_024 = base_recipe("list_limit", extract={
        "lists": {
            "l": {
                "items": [{"css": "ul li"}],
                "limit": 3,
                "fields": {"n": {"from": [{"css": ":scope"}]}}
            }
        }
    }, display={"layout": "list", "source": "l", "row": {"primary": "{n}"}})
    write_case(cases_dir / "024-list-limit-applied", rec_024, {}, html_024, base_meta(), NOW,
        base_expected("list_limit", data={"fields": {}, "lists": {"l": [{"n": "1"}, {"n": "2"}, {"n": "3"}]}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "1", "secondary": None, "trailing": None, "badge": None}, {"primary": "2", "secondary": None, "trailing": None, "badge": None}, {"primary": "3", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # --- CATEGORY 4: Transforms (025 - 040) ---
    # 025-tx-trim-and-collapse-ws
    html_025 = "<html><body><p>   Hello \n\t   World!   </p></body></html>"
    rec_025 = base_recipe("tx_ws", extract={
        "fields": {
            "trimmed": {"from": [{"css": "p"}], "transforms": [{"op": "trim"}]},
            "collapsed": {"from": [{"css": "p"}], "transforms": [{"op": "collapse_ws"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{collapsed}"}})
    write_case(cases_dir / "025-tx-trim-and-collapse-ws", rec_025, {}, html_025, base_meta(), NOW,
        base_expected("tx_ws", data={"fields": {"trimmed": "Hello \n\t   World!", "collapsed": "Hello World!"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Hello World!", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 026-tx-case-upper-lower
    html_026 = "<html><body><span id='txt'>Mixed Case TÜRK</span></body></html>"
    rec_026 = base_recipe("tx_case", extract={
        "fields": {
            "u": {"from": [{"css": "#txt"}], "transforms": [{"op": "upper"}]},
            "l": {"from": [{"css": "#txt"}], "transforms": [{"op": "lower"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{u}"}})
    write_case(cases_dir / "026-tx-case-upper-lower", rec_026, {}, html_026, base_meta(), NOW,
        base_expected("tx_case", data={"fields": {"u": "MIXED CASE TÜRK", "l": "mixed case türk"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "MIXED CASE TÜRK", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 027-tx-replace
    html_027 = "<html><body><p>foo bar foo baz</p></body></html>"
    rec_027 = base_recipe("tx_replace", extract={
        "fields": {
            "res": {"from": [{"css": "p"}], "transforms": [{"op": "replace", "find": "foo", "with": "qux"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{res}"}})
    write_case(cases_dir / "027-tx-replace", rec_027, {}, html_027, base_meta(), NOW,
        base_expected("tx_replace", data={"fields": {"res": "qux bar qux baz"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "qux bar qux baz", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 028-tx-regex-replace
    html_028 = "<html><body><p>Order #12345</p></body></html>"
    rec_028 = base_recipe("tx_regex_replace", extract={
        "fields": {
            "masked": {"from": [{"css": "p"}], "transforms": [{"op": "regex_replace", "pattern": "#(\\d+)", "with": "#[REDACTED $1]"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{masked}"}})
    write_case(cases_dir / "028-tx-regex-replace", rec_028, {}, html_028, base_meta(), NOW,
        base_expected("tx_regex_replace", data={"fields": {"masked": "Order #[REDACTED 12345]"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Order #[REDACTED 12345]", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 029-tx-regex-extract
    html_029 = "<html><body><p>Version: v2.4.1 (build 98)</p></body></html>"
    rec_029 = base_recipe("tx_regex_extract", extract={
        "fields": {
            "version": {"from": [{"css": "p"}], "transforms": [{"op": "regex_extract", "pattern": "v(\\d+\\.\\d+\\.\\d+)", "group": 1}]}
        }
    }, display={"layout": "list", "row": {"primary": "{version}"}})
    write_case(cases_dir / "029-tx-regex-extract", rec_029, {}, html_029, base_meta(), NOW,
        base_expected("tx_regex_extract", data={"fields": {"version": "2.4.1"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "2.4.1", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 030-tx-split-positive-index
    html_030 = "<html><body><p>alpha/beta/gamma</p></body></html>"
    rec_030 = base_recipe("tx_split_pos", extract={
        "fields": {
            "part": {"from": [{"css": "p"}], "transforms": [{"op": "split", "sep": "/", "index": 1}]}
        }
    }, display={"layout": "list", "row": {"primary": "{part}"}})
    write_case(cases_dir / "030-tx-split-positive-index", rec_030, {}, html_030, base_meta(), NOW,
        base_expected("tx_split_pos", data={"fields": {"part": "beta"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "beta", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 031-tx-split-negative-index
    html_031 = "<html><body><p>alpha/beta/gamma</p></body></html>"
    rec_031 = base_recipe("tx_split_neg", extract={
        "fields": {
            "last": {"from": [{"css": "p"}], "transforms": [{"op": "split", "sep": "/", "index": -1}]}
        }
    }, display={"layout": "list", "row": {"primary": "{last}"}})
    write_case(cases_dir / "031-tx-split-negative-index", rec_031, {}, html_031, base_meta(), NOW,
        base_expected("tx_split_neg", data={"fields": {"last": "gamma"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "gamma", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 032-tx-strip-prefix-suffix
    html_032 = "<html><body><p>--Header Value--</p></body></html>"
    rec_032 = base_recipe("tx_strip", extract={
        "fields": {
            "val": {"from": [{"css": "p"}], "transforms": [
                {"op": "strip_prefix", "value": "--"},
                {"op": "strip_suffix", "value": "--"}
            ]}
        }
    }, display={"layout": "list", "row": {"primary": "{val}"}})
    write_case(cases_dir / "032-tx-strip-prefix-suffix", rec_032, {}, html_032, base_meta(), NOW,
        base_expected("tx_strip", data={"fields": {"val": "Header Value"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Header Value", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 033-tx-prepend-append
    html_033 = "<html><body><p>100</p></body></html>"
    rec_033 = base_recipe("tx_prepend_append", extract={
        "fields": {
            "val": {"from": [{"css": "p"}], "transforms": [
                {"op": "prepend", "value": "£"},
                {"op": "append", "value": " GBP"}
            ]}
        }
    }, display={"layout": "list", "row": {"primary": "{val}"}})
    write_case(cases_dir / "033-tx-prepend-append", rec_033, {}, html_033, base_meta(), NOW,
        base_expected("tx_prepend_append", data={"fields": {"val": "£100 GBP"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "£100 GBP", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 034-tx-truncate
    html_034 = "<html><body><p>Hello Unicode 🚀 World</p></body></html>"
    rec_034 = base_recipe("tx_truncate", extract={
        "fields": {
            "val": {"from": [{"css": "p"}], "transforms": [{"op": "truncate", "max": 16}]}
        }
    }, display={"layout": "list", "row": {"primary": "{val}"}})
    write_case(cases_dir / "034-tx-truncate", rec_034, {}, html_034, base_meta(), NOW,
        base_expected("tx_truncate", data={"fields": {"val": "Hello Unicode 🚀 "}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Hello Unicode 🚀 ", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 035-tx-parse-number-standard
    html_035 = "<html><body><p>Price: $1,234.50</p></body></html>"
    rec_035 = base_recipe("tx_parse_num_std", extract={
        "fields": {
            "price": {"from": [{"css": "p"}], "transforms": [{"op": "parse_number"}], "type": "number"}
        }
    }, display={"layout": "list", "row": {"primary": "{price}"}})
    write_case(cases_dir / "035-tx-parse-number-standard", rec_035, {}, html_035, base_meta(), NOW,
        base_expected("tx_parse_num_std", data={"fields": {"price": 1234.5}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "1234.5", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 036-tx-parse-number-european
    html_036 = "<html><body><p>1.234,50 €</p></body></html>"
    rec_036 = base_recipe("tx_parse_num_eu", extract={
        "fields": {
            "price": {"from": [{"css": "p"}], "transforms": [{"op": "parse_number", "decimal": ",", "thousands": "."}], "type": "number"}
        }
    }, display={"layout": "list", "row": {"primary": "{price}"}})
    write_case(cases_dir / "036-tx-parse-number-european", rec_036, {}, html_036, base_meta(), NOW,
        base_expected("tx_parse_num_eu", data={"fields": {"price": 1234.5}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "1234.5", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 037-tx-parse-time
    html_037 = "<html><body><p>Departing: 01:45 PM</p></body></html>"
    rec_037 = base_recipe("tx_parse_time", extract={
        "fields": {
            "time": {"from": [{"css": "p"}], "transforms": [
                {"op": "regex_extract", "pattern": "(\\d{2}:\\d{2}\\s+[AP]M)"},
                {"op": "parse_time", "format": "%I:%M %p"}
            ], "type": "time"}
        }
    }, display={"layout": "list", "row": {"primary": "{time}"}})
    write_case(cases_dir / "037-tx-parse-time", rec_037, {}, html_037, base_meta(), NOW,
        base_expected("tx_parse_time", data={"fields": {"time": "13:45"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "13:45", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 038-tx-parse-datetime
    html_038 = "<html><body><p>02 Oct 2026 09:30:00</p></body></html>"
    rec_038 = base_recipe("tx_parse_dt", timezone="Europe/London", extract={
        "fields": {
            "dt": {"from": [{"css": "p"}], "transforms": [
                {"op": "parse_datetime", "format": "%d %b %Y %H:%M:%S", "tz": "Europe/London"}
            ], "type": "datetime"}
        }
    }, display={"layout": "list", "row": {"primary": "{dt}"}})
    write_case(cases_dir / "038-tx-parse-datetime", rec_038, {}, html_038, base_meta(), NOW,
        base_expected("tx_parse_dt", data={"fields": {"dt": "2026-10-02T09:30:00+01:00"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "2026-10-02 09:30", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 039-tx-map-table
    html_039 = "<html><body><span class='status'>running</span></body></html>"
    rec_039 = base_recipe("tx_map_table", extract={
        "fields": {
            "sev": {"from": [{"css": "span.status"}], "transforms": [
                {"op": "map", "table": {"running": "ok", "stopped": "bad"}}
            ], "type": "severity"}
        }
    }, display={"layout": "list", "row": {"primary": "Status", "badge": {"text": "State", "severity": "{sev}"}}})
    write_case(cases_dir / "039-tx-map-table", rec_039, {}, html_039, base_meta(), NOW,
        base_expected("tx_map_table", data={"fields": {"sev": "ok"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Status", "secondary": None, "trailing": None, "badge": {"text": "State", "severity": "ok"}}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 040-tx-map-else
    html_040 = "<html><body><span class='status'>unknown_code</span></body></html>"
    rec_040 = base_recipe("tx_map_else", extract={
        "fields": {
            "sev": {"from": [{"css": "span.status"}], "transforms": [
                {"op": "map", "table": {"running": "ok"}, "else": "neutral"}
            ], "type": "severity"}
        }
    }, display={"layout": "list", "row": {"primary": "Status", "badge": {"text": "State", "severity": "{sev}"}}})
    write_case(cases_dir / "040-tx-map-else", rec_040, {}, html_040, base_meta(), NOW,
        base_expected("tx_map_else", data={"fields": {"sev": "neutral"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Status", "secondary": None, "trailing": None, "badge": {"text": "State", "severity": "neutral"}}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # --- CATEGORY 5: Types (041 - 048) ---
    # 041-type-string
    html_041 = "<html><body><p>Pure String</p></body></html>"
    rec_041 = base_recipe("type_str", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "string"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "041-type-string", rec_041, {}, html_041, base_meta(), NOW,
        base_expected("type_str", data={"fields": {"v": "Pure String"}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "Pure String", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 042-type-number
    html_042 = "<html><body><p>42.75</p></body></html>"
    rec_042 = base_recipe("type_num", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "number"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "042-type-number", rec_042, {}, html_042, base_meta(), NOW,
        base_expected("type_num", data={"fields": {"v": 42.75}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "42.75", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 043-type-integer
    html_043 = "<html><body><p>-15</p></body></html>"
    rec_043 = base_recipe("type_int", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "integer"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "043-type-integer", rec_043, {}, html_043, base_meta(), NOW,
        base_expected("type_int", data={"fields": {"v": -15}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "-15", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 044-type-boolean
    html_044 = "<html><body><p>true</p></body></html>"
    rec_044 = base_recipe("type_bool", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "boolean"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "044-type-boolean", rec_044, {}, html_044, base_meta(), NOW,
        base_expected("type_bool", data={"fields": {"v": True}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "true", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 045-type-time
    html_045 = "<html><body><p>8:05</p></body></html>"
    rec_045 = base_recipe("type_time", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "time"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "045-type-time", rec_045, {}, html_045, base_meta(), NOW,
        base_expected("type_time", data={"fields": {"v": "08:05"}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "08:05", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 046-type-datetime
    html_046 = "<html><body><p>2026-10-02T11:00:00Z</p></body></html>"
    rec_046 = base_recipe("type_dt", timezone="UTC", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "datetime"}}}, display={"layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "046-type-datetime", rec_046, {}, html_046, base_meta(), NOW,
        base_expected("type_dt", data={"fields": {"v": "2026-10-02T11:00:00Z"}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "2026-10-02 11:00", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 047-type-severity
    html_047 = "<html><body><p>warn</p></body></html>"
    rec_047 = base_recipe("type_sev", extract={"fields": {"v": {"from": [{"css": "p"}], "type": "severity"}}}, display={"layout": "list", "row": {"primary": "Msg", "badge": {"text": "Alert", "severity": "{v}"}}})
    write_case(cases_dir / "047-type-severity", rec_047, {}, html_047, base_meta(), NOW,
        base_expected("type_sev", data={"fields": {"v": "warn"}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "Msg", "secondary": None, "trailing": None, "badge": {"text": "Alert", "severity": "warn"}}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 048-type-url
    html_048 = "<html><body><a href='/sub/path'>Link</a></body></html>"
    rec_048 = base_recipe("type_url", extract={"fields": {"v": {"from": [{"css": "a", "attr": "href"}], "type": "url"}}}, display={"layout": "list", "row": {"primary": "{v}"}, "link": "{v}"})
    write_case(cases_dir / "048-type-url", rec_048, {}, html_048, base_meta(final_url="https://example.com/main/"), NOW,
        base_expected("type_url", data={"fields": {"v": "https://example.com/sub/path"}, "lists": {}}, view={"title": None, "layout": "list", "rows": [{"primary": "https://example.com/sub/path", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": "https://example.com/sub/path"}))

    # --- CATEGORY 6: Templates & Display (049 - 054) ---
    # 049-template-params-and-fields
    html_049 = "<html><body><p id='city'>London</p></body></html>"
    rec_049 = base_recipe("tpl_sub", params=[{"key": "code", "label": "Code", "type": "string"}], extract={"fields": {"city": {"from": [{"css": "#city"}]}}}, display={"title": "{params.code}: {city}", "layout": "list", "row": {"primary": "{city}"}})
    write_case(cases_dir / "049-template-params-and-fields", rec_049, {"code": "LON"}, html_049, base_meta(), NOW,
        base_expected("tpl_sub", data={"fields": {"city": "London"}, "lists": {}}, view={"title": "LON: London", "layout": "list", "rows": [{"primary": "London", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 050-template-escaping
    html_050 = "<html><body><p id='v'>val</p></body></html>"
    rec_050 = base_recipe("tpl_esc", extract={"fields": {"v": {"from": [{"css": "#v"}]}}}, display={"title": "Use {{brackets}} for {v}", "layout": "list", "row": {"primary": "{v}"}})
    write_case(cases_dir / "050-template-escaping", rec_050, {}, html_050, base_meta(), NOW,
        base_expected("tpl_esc", data={"fields": {"v": "val"}, "lists": {}}, view={"title": "Use {brackets} for val", "layout": "list", "rows": [{"primary": "val", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 051-template-null-rule
    html_051 = "<html><body><p id='name'>Widget</p></body></html>"
    rec_051 = base_recipe("tpl_null_rule", extract={
        "fields": {
            "name": {"from": [{"css": "#name"}]},
            "desc": {"from": [{"css": "#missing"}], "optional": True}
        }
    }, display={
        "layout": "list",
        "row": {
            "primary": "{name}",
            "secondary": "Details: {desc}"
        }
    })
    write_case(cases_dir / "051-template-null-rule", rec_051, {}, html_051, base_meta(), NOW,
        base_expected("tpl_null_rule", data={"fields": {"name": "Widget", "desc": None}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Widget", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # 052-display-layout-list
    html_052 = "<html><body><ul><li><span class='t'>Train 1</span><span class='p'>Plat 1</span><span class='s'>ok</span></li></ul></body></html>"
    rec_052 = base_recipe("disp_list", extract={
        "lists": {
            "trains": {
                "items": [{"css": "ul li"}],
                "fields": {
                    "train": {"from": [{"css": ".t"}]},
                    "plat": {"from": [{"css": ".p"}]},
                    "stat": {"from": [{"css": ".s"}], "type": "severity"}
                }
            }
        }
    }, display={
        "title": "Departures",
        "layout": "list",
        "source": "trains",
        "row": {
            "primary": "{train}",
            "secondary": "{plat}",
            "trailing": "Dep",
            "badge": {"text": "Normal", "severity": "{stat}"}
        },
        "footer": "Last check"
    })
    write_case(cases_dir / "052-display-layout-list", rec_052, {}, html_052, base_meta(), NOW,
        base_expected("disp_list", data={"fields": {}, "lists": {"trains": [{"train": "Train 1", "plat": "Plat 1", "stat": "ok"}]}},
                      view={"title": "Departures", "layout": "list", "rows": [{"primary": "Train 1", "secondary": "Plat 1", "trailing": "Dep", "badge": {"text": "Normal", "severity": "ok"}}], "items": None, "empty_text": None, "footer": "Last check", "link": None}))

    # 053-display-layout-kv
    html_053 = "<html><body><div id='cpu'>45%</div><div id='mem'>12GB</div></body></html>"
    rec_053 = base_recipe("disp_kv", extract={
        "fields": {
            "cpu": {"from": [{"css": "#cpu"}]},
            "mem": {"from": [{"css": "#mem"}]}
        }
    }, display={
        "title": "System Status",
        "layout": "kv",
        "items": [
            {"label": "CPU Usage", "value": "{cpu}"},
            {"label": "Memory", "value": "{mem}"}
        ],
        "footer": "Host: srv1"
    })
    write_case(cases_dir / "053-display-layout-kv", rec_053, {}, html_053, base_meta(), NOW,
        base_expected("disp_kv", data={"fields": {"cpu": "45%", "mem": "12GB"}, "lists": {}},
                      view={"title": "System Status", "layout": "kv", "rows": None, "items": [{"label": "CPU Usage", "value": "45%"}, {"label": "Memory", "value": "12GB"}], "empty_text": None, "footer": "Host: srv1", "link": None}))

    # 054-display-badge-severity
    html_054 = "<html><body><span id='s'>bad</span></body></html>"
    rec_054 = base_recipe("disp_badge", extract={
        "fields": {"s": {"from": [{"css": "#s"}], "type": "severity"}}
    }, display={"layout": "list", "row": {"primary": "Alarm", "badge": {"text": "Critical", "severity": "{s}"}}})
    write_case(cases_dir / "054-display-badge-severity", rec_054, {}, html_054, base_meta(), NOW,
        base_expected("disp_badge", data={"fields": {"s": "bad"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Alarm", "secondary": None, "trailing": None, "badge": {"text": "Critical", "severity": "bad"}}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # --- CATEGORY 7: Errors & Security Validation (055 - 062) ---
    # 055-err-field-missing
    html_055 = "<html><body><p>Other</p></body></html>"
    rec_055 = base_recipe("err_missing", extract={"fields": {"required_key": {"from": [{"css": "#absent"}]}}})
    write_case(cases_dir / "055-err-field-missing", rec_055, {}, html_055, base_meta(), NOW,
        base_expected("err_missing", status="error", data=None, view=None,
                      error={"code": "FIELD_MISSING", "message": "Required field absent", "path": "fields.required_key", "http_status": None}))

    # 056-err-too-few-items
    html_056 = "<html><body><ul><li>Item 1</li></ul></body></html>"
    rec_056 = base_recipe("err_few_items", extract={
        "lists": {
            "l": {
                "items": [{"css": "ul li"}],
                "min_items": 3,
                "fields": {"v": {"from": [{"css": ":scope"}]}}
            }
        }
    })
    write_case(cases_dir / "056-err-too-few-items", rec_056, {}, html_056, base_meta(), NOW,
        base_expected("err_few_items", status="error", data=None, view=None,
                      error={"code": "TOO_FEW_ITEMS", "message": "Fewer than min_items valid items", "path": "lists.l", "http_status": None}))

    # 057-err-param-invalid
    html_057 = "<html><body></body></html>"
    rec_057 = base_recipe("err_param", params=[{"key": "code", "label": "Code", "type": "string", "pattern": "^[A-Z]{3}$"}], extract={"fields": {"k": {"from": [{"const": "ok"}]}}})
    write_case(cases_dir / "057-err-param-invalid", rec_057, {"code": "toolong"}, html_057, base_meta(), NOW,
        base_expected("err_param", status="error", data=None, view=None,
                      error={"code": "PARAM_INVALID", "message": "Parameter code does not match pattern", "path": "params.code", "http_status": None}))

    # 058-err-domain-not-allowed
    html_058 = "<html><body></body></html>"
    rec_058 = base_recipe("err_domain", extract={"fields": {"k": {"from": [{"const": "ok"}]}}})
    rec_058["fetch"]["url"] = "https://unauthorized.org/page"
    write_case(cases_dir / "058-err-domain-not-allowed", rec_058, {}, html_058, base_meta(), NOW,
        base_expected("err_domain", status="error", data=None, view=None,
                      error={"code": "DOMAIN_NOT_ALLOWED", "message": "Host unauthorized.org is not in allowed_domains", "path": "fetch.url", "http_status": None}))

    # 059-err-redirect-not-allowed
    html_059 = "<html><body></body></html>"
    rec_059 = base_recipe("err_redirect", extract={"fields": {"k": {"from": [{"const": "ok"}]}}})
    write_case(cases_dir / "059-err-redirect-not-allowed", rec_059, {}, html_059, base_meta(final_url="https://malicious.com/landing"), NOW,
        base_expected("err_redirect", status="error", data=None, view=None,
                      error={"code": "REDIRECT_NOT_ALLOWED", "message": "Redirect destination not allowed", "path": "response.final_url", "http_status": None}))

    # 060-err-http-status
    html_060 = "<html><body><h1>503 Service Unavailable</h1></body></html>"
    rec_060 = base_recipe("err_http", extract={"fields": {"k": {"from": [{"const": "ok"}]}}})
    write_case(cases_dir / "060-err-http-status", rec_060, {}, html_060, base_meta(status=503), NOW,
        base_expected("err_http", status="error", data=None, view=None,
                      error={"code": "HTTP_STATUS", "message": "HTTP request failed with status 503", "path": None, "http_status": 503}))

    # 061-err-response-too-large
    # Spec cap default max_response_bytes is 524288, test setting max_response_bytes: 1024 and delivering 2048 bytes
    body_061 = "A" * 2048
    rec_061 = base_recipe("err_too_large", extract={"fields": {"k": {"from": [{"const": "ok"}]}}})
    rec_061["fetch"]["max_response_bytes"] = 1024
    write_case(cases_dir / "061-err-response-too-large", rec_061, {}, body_061, base_meta(), NOW,
        base_expected("err_too_large", status="error", data=None, view=None,
                      error={"code": "RESPONSE_TOO_LARGE", "message": "Response body exceeded cap of 1024 bytes", "path": "response.body", "http_status": None}))

    # 062-err-parse-error
    malformed_json = "{\"broken\": json"
    rec_062 = base_recipe("err_parse", format="json", extract={"fields": {"k": {"from": [{"json_path": "$.broken"}]}}})
    write_case(cases_dir / "062-err-parse-error", rec_062, {}, malformed_json, base_meta(headers={"content-type": "application/json"}), NOW,
        base_expected("err_parse", status="error", data=None, view=None,
                      error={"code": "PARSE_ERROR", "message": "Failed to parse body as json", "path": "response.body", "http_status": None}))

    # --- CATEGORY 8: Optional Features (cases-optional) ---
    # render.js/001-rendered-dom-snapshot
    # Modeled after Risk of Ruin probe result!
    html_opt_render = """<!DOCTYPE html><html><body>
    <div class="metric-row">
      <div class="metric"><div id="m-ror" class="value danger">41.0%</div></div>
      <div class="metric"><div id="m-median" class="value">£26,250</div></div>
      <div class="metric"><div id="m-yr" class="value">62 mo (5.2 yr)</div></div>
    </div></body></html>"""
    rec_opt_render = base_recipe("opt_render_sim", features=["render.js"], extract={
        "fields": {
            "ruin_prob": {"from": [{"css": "#m-ror"}]},
            "median_port": {"from": [{"css": "#m-median"}]},
            "time_to_ruin": {"from": [{"css": "#m-yr"}]}
        }
    }, display={
        "layout": "list",
        "row": {
            "primary": "Ruin: {ruin_prob}",
            "secondary": "Median: {median_port} ({time_to_ruin})"
        }
    })
    rec_opt_render["fetch"]["render"] = "js"
    rec_opt_render["fetch"]["min_interval_s"] = 900
    rec_opt_render["fetch"]["wait_for"] = "#m-yr.value"
    write_case(opt_dir / "render.js" / "001-rendered-dom-snapshot", rec_opt_render, {}, html_opt_render, base_meta(), NOW,
        base_expected("opt_render_sim", data={"fields": {"ruin_prob": "41.0%", "median_port": "£26,250", "time_to_ruin": "62 mo (5.2 yr)"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Ruin: 41.0%", "secondary": "Median: £26,250 (62 mo (5.2 yr))", "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # render.js/002-captured-document
    html_page = "<html><body><h1>Rendered Main Page</h1></body></html>"
    rec_opt_cap = base_recipe("opt_render_cap", features=["render.js"], extract={
        "fields": {
            "station": {"from": [{"css": "h1"}]},
            "live_alert": {"from": [{"source": "alerts", "json_path": "$.alerts[0].title"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{station}: {live_alert}"}})
    rec_opt_cap["fetch"]["render"] = "js"
    rec_opt_cap["fetch"]["min_interval_s"] = 900
    rec_opt_cap["fetch"]["capture"] = [{"name": "alerts", "url_pattern": "*/api/alerts*", "format": "json"}]
    cap_dir = opt_dir / "render.js" / "002-captured-document"
    write_case(cap_dir, rec_opt_cap, {}, html_page, base_meta(), NOW,
        base_expected("opt_render_cap", data={"fields": {"station": "Rendered Main Page", "live_alert": "Signal Failure"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Rendered Main Page: Signal Failure", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))
    # Write captured document
    captured_dir = cap_dir / "response.captured"
    captured_dir.mkdir(parents=True, exist_ok=True)
    with open(captured_dir / "alerts.json", "w", encoding="utf-8") as f:
        json.dump({"alerts": [{"id": 101, "title": "Signal Failure"}]}, f, indent=2)

    # render.js/003-captured-fallback
    rec_opt_cap_fb = base_recipe("opt_render_cap_fb", features=["render.js"], extract={
        "fields": {
            "status": {
                "from": [
                    {"source": "missing_feed", "json_path": "$.status"},
                    {"css": "span#status-fallback"}
                ]
            }
        }
    }, display={"layout": "list", "row": {"primary": "{status}"}})
    rec_opt_cap_fb["fetch"]["render"] = "js"
    rec_opt_cap_fb["fetch"]["min_interval_s"] = 900
    html_page_fb = "<html><body><span id='status-fallback'>Fallback Active</span></body></html>"
    write_case(opt_dir / "render.js" / "003-captured-fallback", rec_opt_cap_fb, {}, html_page_fb, base_meta(), NOW,
        base_expected("opt_render_cap_fb", status="degraded",
                      data={"fields": {"status": "Fallback Active"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Fallback Active", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None},
                      diag={"fallbacks_used": [{"path": "fields.status", "locator_index": 1}], "skipped_items": [], "warnings": []}))

    # xpath/001-xpath-basic
    html_opt_xpath = "<html><body><div id='wrapper'><section><p class='msg'>Found via XPath</p></section></div></body></html>"
    rec_opt_xpath = base_recipe("opt_xpath_basic", features=["xpath"], extract={
        "fields": {
            "msg": {"from": [{"xpath": "//div[@id='wrapper']//p[@class='msg']"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{msg}"}})
    write_case(opt_dir / "xpath" / "001-xpath-basic", rec_opt_xpath, {}, html_opt_xpath, base_meta(), NOW,
        base_expected("opt_xpath_basic", data={"fields": {"msg": "Found via XPath"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Found via XPath", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    # css.has/001-css-has
    html_opt_has = "<html><body><div class='card'><span class='badge'>Hot</span><h2>Title 1</h2></div><div class='card'><h2>Title 2</h2></div></body></html>"
    rec_opt_has = base_recipe("opt_css_has", features=["css.has"], extract={
        "fields": {
            "hot_card": {"from": [{"css": ".card:has(.badge) h2"}]}
        }
    }, display={"layout": "list", "row": {"primary": "{hot_card}"}})
    write_case(opt_dir / "css.has" / "001-css-has", rec_opt_has, {}, html_opt_has, base_meta(), NOW,
        base_expected("opt_css_has", data={"fields": {"hot_card": "Title 1"}, "lists": {}},
                      view={"title": None, "layout": "list", "rows": [{"primary": "Title 1", "secondary": None, "trailing": None, "badge": None}], "items": None, "empty_text": None, "footer": None, "link": None}))

    print(f"Generated cases in {cases_dir} and {opt_dir}")

if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    build_all(root)
