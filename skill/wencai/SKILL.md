---
name: wencai
description: 使用pywencai查询同花顺问财数据，包括个股/基金/指数等查询、条件选股、AI对话（概念规则问答）、综合搜索（新闻公告研报）。当用户需要查股票行情、财务数据、选股、问财相关指标含义、或搜索个股新闻公告时使用。
---

# 使用pywencai查询问财数据

本技能所在目录通常是通过软链接被引用的（例如软链到agent的skills目录下），实际的`pywencai`源码不一定和本文件在同一路径。执行任何命令前，先用`readlink -f`穿透软链，解析出`pywencai`项目的真实路径（将下面的`<本文件路径>`替换为实际加载到的`SKILL.md`路径）：

```bash
SKILL_MD_REAL_PATH="$(readlink -f "<本文件路径>")"
PYWENCAI_ROOT="$(dirname "$(dirname "$(dirname "$SKILL_MD_REAL_PATH")")")"
echo "pywencai项目路径: $PYWENCAI_ROOT"
```

`<root>/skill/wencai/SKILL.md`向上三级目录即为`pywencai`项目根目录。后续所有`pip install -e`、`uv run`等命令都基于这个解析出来的`$PYWENCAI_ROOT`执行，不要假设固定的绝对路径。

## 环境准备

首次使用需确认`pywencai`可以被import：

```bash
cd "$PYWENCAI_ROOT" && uv run python3 -c "import pywencai; print(pywencai.__file__)"
```

如果在其他项目里使用，需要先安装（可编辑模式，改动本地源码立即生效）：

```bash
uv add --editable "$PYWENCAI_ROOT"
# 或
pip install -e "$PYWENCAI_ROOT"
```

`pywencai`依赖Node.js（v16+）生成反爬token，请确认已安装：`node --version`

## cookie 获取

所有方法均**必填** `cookie` 参数（同花顺问财登录态）。cookie从浏览器登录 `https://www.iwencai.com/` 后，复制请求头中的Cookie字段值。若当前环境已配置cookie自动同步服务（如综合搜索技能），优先通过该服务获取最新cookie，避免手动过期。

## 方法选型决策树

根据用户问题的意图，按以下顺序判断使用哪个方法：

```
用户问题
│
├─ 是否在问"某个指标/名词/规则是什么、怎么计算的"？
│   （例如："股性评分怎么算的"、"什么是市净率"、"MACD金叉是什么意思"）
│   └─ 是 → 使用 chat()，返回一段完整的解释性文本
│
├─ 是否要"筛选/找出符合条件的一批股票"？
│   （例如："换手率大于5%的股票"、"macd金叉且市盈率小于20的股票"）
│   └─ 是 → 优先使用 get()（支持loop翻页拿到全部结果，更稳定）
│            若get()对某些新指标识别不佳，或需要交叉验证，再尝试 screener()
│            （screener是问财新版选股agent，指标可能更新更快，但不支持分页，受perpage限制）
│
├─ 是否在查"某一个具体标的（股票/基金/指数）的行情、财务、简介等数据"？
│   （例如："贵州茅台"、"最近一年收益率最高的基金经理"）
│   └─ 是 → 使用 get()，不带选股条件时会返回该标的的问答类数据（字典）
│
└─ 是否要查"某公司/事件相关的新闻、公告、研报、互动易问答"？
    （例如："工商银行最新新闻"、"贵州茅台公告"）
    └─ 是 → 使用 search()，聚合多渠道资讯结果
```

## 四个方法速查

| 方法 | 用途 | 底层接口 | 返回值 |
|-|-|-|-|
| `get(query, cookie=..., **kwargs)` | 条件选股 / 个股查询 | `customized/chart/get-robot-data` + 分页接口 | 选股条件→`DataFrame`；个股问答→`dict` |
| `screener(question, cookie=..., **kwargs)` | AI选股（新接口，选股备选） | `gateway/aime/stream-query`（选股agent） | `DataFrame` |
| `chat(question, cookie=..., user_id=..., **kwargs)` | AI对话，问知识/规则/概念 | `gateway/aime/stream-query`（对话agent） | 字符串（完整回答文本，Markdown格式） |
| `search(query, cookie=..., **kwargs)` | 综合搜索：新闻/公告/研报/互动易 | `gateway/mobilesearch/comprehensive/search` | `DataFrame`（含`channel`字段区分渠道） |

## 用法示例

```python
import pywencai

# 选股（优先方式，支持翻页）
res = pywencai.get(query='市盈率小于20的沪深300成分股', cookie=cookie, loop=True)

# 选股备选（新接口）
res = pywencai.screener('macd金叉，换手率大于5%', cookie=cookie)

# 个股查询
res = pywencai.get(query='贵州茅台', cookie=cookie)

# 概念/规则问答
answer = pywencai.chat('股性评分的计算规则是什么', cookie=cookie, user_id=user_id)

# 综合搜索
res = pywencai.search('工商银行', cookie=cookie)
```

## 关键约束

1. **必须传cookie**，问财登录策略调整后不传cookie无法使用。
2. **低频调用**：短时间高频请求会触发风控返回`403 Access Denied`，同一账号/cookie也会被限制，请求间隔建议2秒以上。
3. `query_type`参数（`get`/`screener`通用）用于指定非A股品类，取值见项目`README.md`（stock/zhishu/fund/fundmanager/fundcompany/hkstock/hkzhishu/usstock/uszhishu/threeboard/conbond/insurance/futures/lccp/foreign_exchange/macro）。
4. `get()`返回类型不固定（可能是`DataFrame`或`dict`），调用后需要判断类型再处理；如需固定返回`DataFrame`或`None`，可传`no_detail=True`。
5. 条件选股中支持的具体指标分类（技术面/行情面/基本面/财务面/阶段表现/特色数据）见`pywencai/xuangu_conditions.json`。
