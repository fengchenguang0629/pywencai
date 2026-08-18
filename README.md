[![PyPI version](https://badge.fury.io/py/pywencai.svg)](https://badge.fury.io/py/pywencai)
[![Downloads](https://static.pepy.tech/badge/pywencai/month)](https://pepy.tech/project/pywencai)

# pywencai

获取同花顺问财数据

⚠️**注意**：由于问财登录策略调整，目前**必填cookie参数**才能使用，可以参看下面关于如何获取cookie参数的介绍

## 声明

1. pywencai为开源社区开发，并非同花顺官方提供的工具。
2. 该工具只是效率工具，为了便于通过python获取问财数据，用于量化研究和学习，其原理，与登录网页获取数据方式一致。
3. 建议低频使用，反对高频调用，高频调用会被问财屏蔽，请自行评估技术和法律风险。
4. 项目代码遵循MIT开源协议，但不赞成商用，商用请自行评估法律风险。
5. 感谢问财提供免费接口和数据分享。

## 环境依赖

由于程序中执行了js代码，请先保证已安装了[Node.js](https://nodejs.org/en/)，需要版本**v16+**

未安装请自行安装

## 安装

```
pip install pywencai
```
> 由于问财接口策略经常发生变化，请安装最新版本使用，遇到问题时，优先尝试升级解决

## 视频教程

[如何使用Python获取同花顺问财数据？全网最简单方法！](https://www.bilibili.com/video/BV1NP411C7UU/)

# Demo

```python
import pywencai

res = pywencai.get(query='退市股票', sort_key='退市@退市日期', sort_order='asc', cookie='xxx')
print(res)
```

# API

pywencai目前支持4种方法，分别对应问财不同的功能入口：

| 方法 | 对应问财功能 | 底层接口 | 返回值 |
|-|-|-|-|
| `get` | 条件选股 / 个股问答（旧版） | `customized/chart/get-robot-data` + `gateway/urp/v7/landing/getDataList` | `DataFrame` 或 `dict` |
| `screener` | AI选股（新版，即问财官网的"选股"入口） | `gateway/aime/stream-query`（选股agent） | `DataFrame` |
| `chat` | AI对话（问财官网的"对话"入口，问知识、规则等） | `gateway/aime/stream-query`（对话agent） | 字符串（完整回答文本） |
| `search` | 综合搜索（新闻/网页/公告/研报/互动易） | `gateway/mobilesearch/comprehensive/search` | `DataFrame` |

> `get`和`screener`都能做条件选股，是问财新旧两套并行的技术实现，功能上大体等价，`screener`是新接口，覆盖的指标和数据可能更新更及时，但返回条数上限固定（见下文`perpage`说明），`get`支持`loop`翻页拿到全部结果。日常选股优先用`get`（更稳定、支持分页），`screener`可用于验证或获取新接口独有的字段。

## get(**kwargs)

根据问财语句查询结果

### 参数

#### query

必填，查询问句

> 老版本的question参数1.0版本以后会弃用，请以后统一使用query参数

#### sort_key

非必填，指定用于排序的字段，值为返回结果的列名

#### sort_order

非必填，排序规则，至为`asc`（升序）或`desc`（降序）

#### page

非必填，查询的页号，默认为1

#### perpage

非必填，每页数据条数，默认值100，由于问财做了数据限制，最大值为100，指定大于100的数值无效。

#### loop

非必填，是否循环分页，返回多页合并数据。默认值为`False`，可以设置为`True`或具体数值。

当设置为`True`时，程序会一直循环到最后一页，返回全部数据。

当设置具体数值`n`时，循环请求n页，返回n页合并数据。

#### query_type

非必填，默认为`stock`，当查询的类型不是股票的时候需要传，取值如下：

| 取值 | 含义 |
|-|-|
| stock | A股 |
| zhishu | A股指数 |
| fund | 基金产品（含场内ETF） |
| fundmanager | 基金经理 |
| fundcompany | 基金公司 |
| hkstock | 港股 |
| hkzhishu | 港股指数 |
| usstock | 美股 |
| uszhishu | 美股指数 |
| threeboard | 新三板 |
| conbond | 可转债 |
| insurance | 保险 |
| futures | 期货 |
| lccp | 理财 |
| foreign_exchange | 外汇 |
| macro | 宏观 |

#### retry

非必填，默认为10，表示请求失败后的重试次数。

#### sleep

非必填，默认为0，表示循环请求时，每次请求间隔多少秒。

#### log

非必填，默认为`False`，是否在控制台打印日志。

#### pro

非必填，默认为False，付费版传True，

> 必须传入cookie参数才能使用付费版


#### cookie

**必填**，默认为None

```python
pywencai.get(question='近3个月每日市盈率', pro=True, cookie='xxxx')
```
cookie获取方法，复制请求头中的Cookie字段值

![cookie](./cookie.png)
 

#### request_params

非必填，默认为`{}`，可以设置额外的request参数

```python
pywencai.get(query='昨日涨幅', sort_order='asc', loop=True, log=True, request_params={ 'proxies': proxies })
```
> 具体参数参看：[https://requests.readthedocs.io/en/latest/api/#requests.request](https://requests.readthedocs.io/en/latest/api/#requests.request)

#### no_detail

非必填，默认为`False`，当为`True`时，查询一些**详情类问题**不再会返回字典，而返回`None`，可以保证查询结果类型一直为`pd.DataFrame`或`None`。

#### find

非必填，默认为`None`，可以传一个数组，例如`['600519', '000010']`，数组内的对应标的会排列在DataFrame的最前面。

**【注意】** 1、该参数只有结果范围DataFrame时有效。2、配置该参数后，loop参数会失效，结果只会返回前100条。

#### user_agent

非必填，默认为`None`，可以自己传`user_agent`，不使用随机的生成的`user_agent`

### 返回值

当查询的是列表时，该方法返回一个`pandas`的`Dataframe`

当查询的是详情时，该方法返回一个字典，字典中可能包含若干个文本和`Dataframe`

## screener(question, **kwargs)

AI选股（问财官网"选股"入口对应的新接口），根据自然语言条件返回选股结果

```python
import pywencai

res = pywencai.screener('macd金叉，换手率大于5%', cookie='xxx')
print(res)
```

### 参数

#### question

必填，选股问句

#### query_type

非必填，默认为`stock`，取值同`get`方法的`query_type`

#### perpage

非必填，默认为50，单次返回的最大条数（该接口不支持分页，若结果条数超过`perpage`只会返回其中一部分）

#### retry / sleep / log / cookie / user_agent / request_params

含义同`get`方法对应参数

### 返回值

返回一个`pandas`的`Dataframe`

## chat(question, **kwargs)

AI对话（问财官网"对话"入口），用于问知识、规则等不需要返回股票列表的问题，返回完整的回答文本

```python
import pywencai

answer = pywencai.chat('股性评分的计算规则是什么', cookie='xxx', user_id='你的userid')
print(answer)
```

### 参数

#### question

必填，对话问句

#### user_id

非必填，默认为空字符串，建议传入cookie中的`userid`字段值

#### deep_research

非必填，默认为`False`，是否开启深度研究模式

#### retry / sleep / log / cookie / user_agent / request_params

含义同`get`方法对应参数

### 返回值

返回一个字符串，为AI对话的完整回答文本（内容为Markdown格式）

## search(query, **kwargs)

综合搜索（问财官网"搜索"入口），聚合新闻、网页、公告、研报、互动易等多渠道结果

```python
import pywencai

res = pywencai.search('工商银行', cookie='xxx')
print(res)
```

### 参数

#### query

必填，搜索关键词

#### channels

非必填，默认为`['news_filter', 'web', 'announcement', 'report', 'interact']`，指定搜索渠道

#### offset / size

非必填，分页参数，默认`offset=0`，`size=20`

#### retry / sleep / log / cookie / user_agent / request_params

含义同`get`方法对应参数

### 返回值

返回一个`pandas`的`Dataframe`，包含`channel`（结果所属渠道）、`title`、`summary`、`url`等字段
