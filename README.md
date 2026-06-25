# struct2tree

[![tests](https://github.com/al0ys1us/struct2tree/actions/workflows/tests.yml/badge.svg)](https://github.com/al0ys1us/struct2tree/actions/workflows/tests.yml)

[English](README.en.md) | [中文](README.md)

将多种来源的层级结构数据（思维导图、文件树、Markdown 大纲、JSON、YAML 等）统一转换为一种对 LLM 可读性最优的 XML 格式的 Python CLI 工具。

核心价值：**去噪、补全、统一**。

- **去噪**：剥离样式、布局、随机 ID 等非语义信息，只保留结构骨架
- **补全**：显式化原始格式难以表达的跨节点引用和边语义（`<ref>`）
- **统一**：无论输入来源是什么，AI 看到的永远是同一个 schema

零外部依赖，仅使用 Python 标准库（要求 Python 3.10+）。

## 安装

```bash
pip install -e .
```

安装后 `struct2tree` 命令全局可用。

## 输出格式

```xml
<tree name="博客系统架构">
  <n id="1" label="博客系统">
    <n id="1.1" label="用户模块">
      <n id="1.1.1" label="注册登录" meta="auth:OAuth2" />
      <n id="1.1.2" label="权限管理">
        <n id="1.1.2.1" label="管理员" />
        <n id="1.1.2.2" label="普通用户" />
      </n>
    </n>
    <n id="1.2" label="文章模块">
      <n id="1.2.1" label="编辑器" meta="format:markdown" />
      <n id="1.2.2" label="评论系统" meta="storage:append-only" />
    </n>
  </n>

  <ref from="1.2" to="1.1.2" rel="depends-on" note="文章模块依赖权限校验" />
  <ref from="1.2.2" to="1.1" rel="depends-on" />
</tree>
```

- `<tree name="...">`：根元素，`name` 为标题
- `<n id label meta?>`：节点，`id` 为层级编号路径（`1.2.3`），叶子节点自闭合
- `<ref from to rel note?>`：跨节点引用（图的边），集中写在引用区

## 支持的输入格式

| 格式 | 扩展名 / 触发 | 说明 |
|------|--------------|------|
| Xmind | `.xmind` | 新版 `content.json` 与旧版 `content.xml`，含 relationships |
| Markdown | `.md`, `.markdown` | 嵌套列表，可选 `{meta}` 与 `[ref]` 扩展语法 |
| JSON | `.json` | 对象嵌套型（结构 A）与路径映射型（结构 B）自动识别 |
| YAML | `.yaml`, `.yml` | 自实现简易 parser，支持 mapping / scalar / sequence |
| 缩进纯文本 | `.txt` | 2 空格或 1 tab 为一层 |
| 目录树文本 | `--format tree-text` / stdin | `tree` 命令的 ASCII box-art 输出，或缩进文本 |
| 文件系统目录 | `--dir <path>` | 递归扫描目录 |

## 用法

```bash
# 自动检测输入格式
struct2tree input.xmind
struct2tree outline.md
struct2tree tree.json
struct2tree structure.yaml

# 目录模式
struct2tree --dir ./my-project

# stdin 管道
tree ./src | struct2tree --format tree-text
cat outline.md | struct2tree --format markdown

# 输出到文件 / 剪贴板
struct2tree input.xmind -o output.xml
struct2tree --dir ./src --clipboard

# 指定 tree name
struct2tree input.xmind --name "博客系统架构"

# Markdown 扩展语法
struct2tree outline.md --parse-meta --parse-ref

# 批量转换
for f in *.xmind; do struct2tree "$f" -o "${f%.xmind}.xml"; done
```

### 全部参数

```
位置参数：
  input                    输入文件路径（自动检测格式）。省略时从 stdin 读取

选项：
  -o, --output <file>      输出文件路径。省略则输出到 stdout
  --name <string>          指定 tree name，覆盖自动推断
  --dir <path>             目录模式：将文件系统目录转为树
  --format <fmt>           强制指定输入格式：xmind, markdown, json, yaml, text, dir, tree-text
  --sheet <n>              Xmind 专用：指定处理第几个 sheet（从 0 开始，默认 0）
  --parse-meta             Markdown 专用：启用 {key:value} meta 语法解析
  --parse-ref              Markdown 专用：启用 [ref] 引用区语法解析
  --include-hidden         目录模式：包含隐藏文件和目录
  --ignore <pattern>       目录模式：额外忽略的 glob 模式（可多次使用）
  --file-meta              目录模式：为文件节点添加 size/ext meta
  --max-depth <n>          限制最大递归深度（默认不限制）
  --wrap-code-block        将输出包裹在 ```xml ... ``` 代码块中
  --clipboard              输出到系统剪贴板（替代 stdout）
  -v, --version            显示版本号
  -h, --help               显示帮助信息
```

### Markdown 扩展语法

`--parse-meta` 开启后，列表项尾部花括号被提取为 meta：

```markdown
- 匹配策略 {type:greedy, mode:fallback}
```

`--parse-ref` 开启后，文件末尾 `[ref]` 区域被解析为引用：

```
[ref]: 1.2 -> 1.1.2 | depends-on | 文章模块依赖权限校验
```

## 作为 Python 库调用

```python
from struct2tree import convert_source, convert

xml = convert_source("outline.md", parse_meta=True)   # 文件路径 -> XML
xml = convert_source("x", fmt="markdown", content="- a\n- b\n")  # 文本 -> XML

# 或直接操作内部模型
from struct2tree import Tree, TreeNode
xml = convert(Tree(name="t", roots=[TreeNode(label="root")]))
```

## 在 Agent 中使用

struct2tree 的核心定位是作为 Agent（如 Claude Code、Cursor、自建 Agent）的预处理工具：把结构化数据标准化成统一 XML 后再注入上下文，比直接把 `.xmind`、目录树、杂乱大纲喂给模型更省 token、可读性也更好。stdout 只输出纯 XML，警告和错误走 stderr，因此管道安全。

### Claude Code

最直接的用法是让 Claude Code 在终端里调用，把结果接进对话或剪贴板：

```bash
# 把项目结构序列化后复制，粘进对话让 AI 做代码分析
struct2tree --dir ./src --clipboard

# 把思维导图转成 XML 直接看
struct2tree design.xmind

# 管道串联：tree 命令的输出转成统一格式
tree ./src | struct2tree --format tree-text
```

也可以封装成一个 slash command。在项目里建 `.claude/commands/struct2tree.md`：

```markdown
---
description: 把指定文件或目录转成 struct2tree XML 并展示
---

运行 `struct2tree $ARGUMENTS` 并把输出的 XML 作为后续分析的上下文。
```

之后在 Claude Code 里输入 `/struct2tree ./src` 或 `/struct2tree design.xmind` 即可。

### 嵌入 prompt / SKILL.md

把转换结果作为知识骨架写进 system prompt 或 skill 文档：

```bash
# 生成 XML 片段，手动粘进 SKILL.md 的某一节
struct2tree knowledge.xmind -o skill-tree.xml

# 或包成代码块直接复制到剪贴板
struct2tree knowledge.xmind --wrap-code-block --clipboard
```

XML 里的 `id`（如 `1.2.3`）编码了顺序、层级、深度，`<ref>` 显式表达了跨节点依赖，模型可以直接引用 `1.2.3` 这样的路径来讨论结构中的某个节点。

### 自建 Agent / 自动化流程

作为库调用，省去 subprocess 开销，适合嵌进流水线：

```python
from struct2tree import convert_source

# 把用户上传的 xmind 转成 XML，拼进 prompt
tree_xml = convert_source("uploaded.xmind")
prompt = f"以下是产品结构，请基于它生成 PRD：\n{tree_xml}"
```

批量构建知识库：

```bash
for f in docs/*.xmind; do
  struct2tree "$f" -o "build/$(basename "${f%.xmind}").xml"
done
```

## 开发与测试

```bash
python3 tests/fixtures/make_xmind_fixtures.py   # 生成二进制 xmind 测试夹具
python3 -m unittest discover -s tests -v
```

测试仅使用标准库 `unittest`，无需安装 pytest。

## 架构

```
struct2tree/
  cli.py            argparse 入口
  converter.py      内部树 -> XML（id 分配、ref 路径映射、转义、缩进）
  models.py         TreeNode / TreeRef / Tree 数据模型
  detect.py         格式自动检测（扩展名 + stdin 内容启发式）
  utils.py          XML 转义、剪贴板、stdin / 文件读取
  parsers/          各输入格式 parser，统一 parse(source, options) -> Tree
```

新增输入格式只需新建一个 parser 模块（实现 `parse(source, options) -> Tree`），
并注册到 `parsers/__init__.py` 的 `REGISTRY` 与 `detect.py` 中。
