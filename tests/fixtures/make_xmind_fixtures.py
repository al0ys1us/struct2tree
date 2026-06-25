"""Generate binary .xmind fixtures (ZIP archives) for tests.

Run once: ``python tests/fixtures/make_xmind_fixtures.py``
Creates basic.xmind (content.json + relationships), multi.xmind (two sheets),
and legacy.xmind (old content.xml format).
"""

import json
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))


def write_xmind(path, members):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in members.items():
            zf.writestr(name, data)


def basic():
    sheet = {
        "title": "博客系统架构",
        "rootTopic": {
            "id": "root",
            "title": "博客系统",
            "children": {
                "attached": [
                    {
                        "id": "a",
                        "title": "用户模块",
                        "notes": {"plain": {"content": "核心模块"}},
                        "children": {
                            "attached": [
                                {"id": "a1", "title": "注册登录",
                                 "labels": ["OAuth2"]},
                                {"id": "a2", "title": "权限管理"},
                            ]
                        },
                    },
                    {"id": "b", "title": "文章模块"},
                ]
            },
        },
        "relationships": [
            {"end1Id": "b", "end2Id": "a2", "title": "depends-on"},
        ],
    }
    write_xmind(
        os.path.join(HERE, "basic.xmind"),
        {"content.json": json.dumps([sheet], ensure_ascii=False)},
    )


def multi():
    sheets = [
        {"title": "Sheet1", "rootTopic": {"id": "r1", "title": "First"}},
        {
            "title": "Sheet2",
            "rootTopic": {
                "id": "r2",
                "title": "Second",
                "children": {"attached": [{"id": "c", "title": "Child"}]},
            },
        },
    ]
    write_xmind(
        os.path.join(HERE, "multi.xmind"),
        {"content.json": json.dumps(sheets, ensure_ascii=False)},
    )


def legacy():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" version="2.0">
  <sheet id="s1">
    <topic id="root">
      <title>Old Root</title>
      <children>
        <topics type="attached">
          <topic id="x1"><title>Alpha</title></topic>
          <topic id="x2">
            <title>Beta</title>
            <children>
              <topics type="attached">
                <topic id="x3"><title>Gamma</title></topic>
              </topics>
            </children>
          </topic>
        </topics>
      </children>
    </topic>
    <title>Legacy Sheet</title>
  </sheet>
</xmap-content>"""
    write_xmind(os.path.join(HERE, "legacy.xmind"), {"content.xml": xml})


def summary():
    # Parent P with subtopics a/b/c; a summary topic covering the first two.
    sheet = {
        "title": "概要测试",
        "rootTopic": {
            "id": "P",
            "title": "父主题",
            "children": {
                "attached": [
                    {"id": "a", "title": "子主题A"},
                    {"id": "b", "title": "子主题B"},
                    {"id": "c", "title": "子主题C"},
                ],
                "summary": [{"id": "sumNode", "title": "前两项=核心能力"}],
            },
            "summaries": [{"id": "s1", "range": "(0,1)", "topicId": "sumNode"}],
        },
    }
    write_xmind(
        os.path.join(HERE, "summary.xmind"),
        {"content.json": json.dumps([sheet], ensure_ascii=False)},
    )


if __name__ == "__main__":
    basic()
    multi()
    legacy()
    summary()
    print("fixtures written")
