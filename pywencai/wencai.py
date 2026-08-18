import json
from typing import List
import math
import uuid
from urllib.parse import quote

import requests as rq
import pandas as pd
import time
import logging
import pydash as _
from .convert import convert
from .headers import headers

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[pywencai] %(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def while_do(do, retry=10, sleep=0, log=False):
    count = 0
    while count < retry:
        time.sleep(sleep)
        try:
            return do()
        except:
            log and logger.warning(f'{count+1}次尝试失败')
            count += 1
    return None


def get_robot_data(**kwargs):
    '''获取condition'''
    retry = kwargs.get('retry', 10)
    sleep = kwargs.get('sleep', 0)
    question = kwargs.get('query')
    log = kwargs.get('log', False)
    query_type = kwargs.get('query_type', 'stock')
    cookie = kwargs.get('cookie', None)
    user_agent = kwargs.get('user_agent', None)
    request_params = kwargs.get('request_params', {})
    data = {
        'add_info': "{\"urp\":{\"scene\":1,\"company\":1,\"business\":1},\"contentType\":\"json\",\"searchInfo\":true}",
        'perpage': '10',
        'page': 1,
        'source': 'Ths_iwencai_Xuangu',
        'log_info': "{\"input_type\":\"click\"}",
        'version': '2.0',
        'secondary_intent': query_type,
        'question': question
    }

    pro = kwargs.get('pro', False)

    if pro:
        data['iwcpro'] = 1

    log and logger.info(f'获取condition开始')

    def do():
        res = rq.request(
            method='POST',
            url='https://www.iwencai.com/customized/chart/get-robot-data',
            json=data,
            headers=headers(cookie, user_agent),
            **request_params
        )
        params = convert(res)
        log and logger.info(f'获取get_robot_data成功')
        return params

    result = while_do(do, retry, sleep, log)

    if result is None:
        log and logger.info(f'获取get_robot_data失败')

    return result


def replace_key(key):
    '''替换key'''
    key_map = {
        'question': 'query',
        'sort_key': 'urp_sort_index',
        'sort_order': 'urp_sort_way'
    }
    return key_map.get(key, key)


def get_page(url_params, **kwargs):
    '''获取每页数据'''
    retry = kwargs.pop('retry', 10)
    sleep = kwargs.pop('sleep', 0)
    log = kwargs.pop('log', False)
    cookie = kwargs.pop('cookie', None)
    user_agent = kwargs.get('user_agent', None)
    find = kwargs.pop('find', None)
    query_type = kwargs.get('query_type', 'stock')
    request_params = kwargs.get('request_params', {})
    pro = kwargs.get('pro', False)
    if find is None:
        data = {
            **url_params,
            'perpage': 100,
            'page': 1,
            **kwargs
        }
        target_url = 'https://www.iwencai.com/gateway/urp/v7/landing/getDataList'
        if pro:
            target_url = f'{target_url}?iwcpro=1'
        path = 'answer.components.0.data.datas'
    else:
        if isinstance(find, List):
            # 传入股票代码列表时，拼接
            find = ','.join(find)
        data = {
             **url_params,
            'perpage': 100,
            'page': 1,
            'query_type': query_type,
            'question': find,
            **kwargs
        }
        target_url = 'https://www.iwencai.com/unifiedwap/unified-wap/v2/stock-pick/find'
        path = 'data.data.datas'
    
    log and logger.info(f'第{data.get("page")}页开始')

    def do():
        res = rq.request(
            method='POST',
            url=target_url,
            data=data,
            headers=headers(cookie, user_agent),
            timeout=(5, 10),
            **request_params
        )
        result_do = json.loads(res.text)
        data_list = _.get(result_do, path)

        if len(data_list) == 0:
            log and logger.error(f'第{data.get("page")}页返回空！')
            raise Exception("data_list is empty!")
        log and logger.info(f'第{data.get("page")}页成功')
        return pd.DataFrame.from_dict(data_list)
    
    result = while_do(do, retry, sleep, log)

    if result is None:
        log and logger.error(f'第{data.get("page")}页失败')

    return result


def can_loop(loop, count):
    return count < loop


def loop_page(loop, row_count, url_params, **kwargs):
    '''循环分页'''
    count = 0
    perpage = kwargs.pop('perpage', 100)
    max_page = math.ceil(row_count / perpage)
    result = None
    if 'page' not in kwargs:
        kwargs['page'] = 1
    initPage = kwargs['page']
    loop_count = max_page if loop is True else loop
    while can_loop(loop_count, count):
        kwargs['page'] = initPage + count
        resultPage = get_page(url_params, **kwargs)
        count = count + 1
        if result is None:
            result = resultPage
        else:
            result = pd.concat([result, resultPage], ignore_index=True)

    return result


def get(loop=False, **kwargs):
    '''获取结果'''
    kwargs = {replace_key(key): value for key, value in kwargs.items()}
    params = get_robot_data(**kwargs)
    data = params.get('data')
    url_params = params.get('url_params')
    condition = _.get(data, 'condition')

    if condition is not None:
        kwargs = {**kwargs, **data}
        find = kwargs.get('find', None)
        if loop and find is None:
            row_count = params.get('row_count')
            return loop_page(loop, row_count, url_params, **kwargs)
        else:
            return get_page(url_params, **kwargs)
    else:
        no_detail = kwargs.get('no_detail')
        if no_detail != True:
            return data
        else:
            return None


def parse_stream_line(line):
    '''解析一行SSE数据'''
    if not line or not line.startswith('data:'):
        return None
    try:
        return json.loads(line[len('data:'):])
    except json.JSONDecodeError:
        return None


def chat(question, **kwargs):
    '''AI对话，返回完整回答文本'''
    retry = kwargs.get('retry', 10)
    sleep = kwargs.get('sleep', 0)
    log = kwargs.get('log', False)
    cookie = kwargs.get('cookie', None)
    user_agent = kwargs.get('user_agent', None)
    user_id = kwargs.get('user_id', '')
    deep_research = kwargs.get('deep_research', False)
    request_params = kwargs.get('request_params', {})

    data = {
        'version': '3.4.1',
        'session_id': uuid.uuid4().hex,
        'user_id': user_id,
        'source': 'Ths_iwencai_Xuangu',
        'input_type': 'click',
        'question': question,
        'deviceType': 'browser',
        'add_info': {
            'merge_repeat': True,
            'async_generate_data': True,
            'show_searching': True,
            'urp': {'is_lowcode': 1, 'component_version': '1.1.4'}
        },
        'entity_info': {},
        'events': [
            {'event_name': 'auto_agent', 'event_type': 'user_input'},
            {'event_name': 'ab_test', 'event_type': 'front_trigger', 'content': {'deep_research': 1 if deep_research else 0}}
        ]
    }

    log and logger.info(f'AI对话开始')

    def do():
        res = rq.request(
            method='POST',
            url='https://www.iwencai.com/gateway/aime/stream-query',
            json=data,
            headers={
                **headers(cookie, user_agent, referer='https://www.iwencai.com/chat'),
                'Content-Type': 'application/json',
                'accept': 'text/event-stream',
                'X-Source': 'Ths_iwencai_Xuangu'
            },
            stream=True,
            **request_params
        )
        answer_parts = []
        for line in res.iter_lines(decode_unicode=True):
            event = parse_stream_line(line)
            if event is None:
                continue
            if event.get('answer_path') == 'other/openAnswer':
                answer_parts.append(_.get(event, 'section.text_answer', ''))
        answer = ''.join(answer_parts)
        if answer == '':
            raise Exception('answer is empty!')
        log and logger.info(f'AI对话成功')
        return answer

    result = while_do(do, retry, sleep, log)

    if result is None:
        log and logger.info(f'AI对话失败')

    return result


def search(query, **kwargs):
    '''综合搜索，返回新闻/网页/公告/研报/互动易等多渠道结果列表'''
    retry = kwargs.get('retry', 10)
    sleep = kwargs.get('sleep', 0)
    log = kwargs.get('log', False)
    cookie = kwargs.get('cookie', None)
    user_agent = kwargs.get('user_agent', None)
    offset = kwargs.get('offset', 0)
    size = kwargs.get('size', 20)
    channels = kwargs.get('channels', ['news_filter', 'web', 'announcement', 'report', 'interact'])
    request_params = kwargs.get('request_params', {})

    data = {
        'offset': offset,
        'size': size,
        'app_id': 'wencai_pc',
        'query': query,
        'channels': channels,
        'qid': uuid.uuid4().hex,
        'scroll_mode': 'web',
        'platform': 'pc',
        'slots': []
    }

    log and logger.info(f'综合搜索开始')

    def do():
        res = rq.request(
            method='POST',
            url='https://www.iwencai.com/gateway/mobilesearch/comprehensive/search',
            json=data,
            headers={
                **headers(cookie, user_agent, referer=f'https://www.iwencai.com/search/result?w={quote(query)}'),
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*'
            },
            **request_params
        )
        result_do = json.loads(res.text)
        data_list = _.get(result_do, 'data')
        if not data_list:
            raise Exception('data is empty!')
        log and logger.info(f'综合搜索成功')
        return pd.DataFrame.from_dict(data_list)

    result = while_do(do, retry, sleep, log)

    if result is None:
        log and logger.info(f'综合搜索失败')

    return result


def screener(question, **kwargs):
    '''AI选股（新版条件选股agent），返回选股结果DataFrame'''
    retry = kwargs.get('retry', 10)
    sleep = kwargs.get('sleep', 0)
    log = kwargs.get('log', False)
    cookie = kwargs.get('cookie', None)
    user_agent = kwargs.get('user_agent', None)
    query_type = kwargs.get('query_type', 'stock')
    perpage = kwargs.get('perpage', 50)
    request_params = kwargs.get('request_params', {})

    data = {
        'question': question,
        'default_fallback': False,
        'input_type': 'click',
        'entity_info': {'device_type': 'pc', 'comefrom': None},
        'source': 'ths_iwencai_pc_xuangu',
        'dialog_model': 'CUSTOMER_AGENT',
        'version': '3.4.1',
        'agent_tools': [{'tool_id': 'FinQuery', 'tool_param': {'domain': query_type, 'perpage': perpage}}],
        'events': [{'event_type': 'user_input', 'event_name': 'normal_agent', 'content': {}}],
        'add_info': {},
        'agent_id': 'MaSzyUwyyl',
        'agent_name': ''
    }

    log and logger.info(f'AI选股开始')

    def do():
        res = rq.request(
            method='POST',
            url='https://www.iwencai.com/gateway/aime/stream-query',
            json=data,
            headers={
                **headers(cookie, user_agent, referer=f'https://www.iwencai.com/screener/result?w={quote(question)}&querytype={query_type}'),
                'Content-Type': 'application/json',
                'accept': 'text/event-stream',
                'X-Source': 'ths_iwencai_pc_xuangu'
            },
            stream=True,
            **request_params
        )
        datas = None
        for line in res.iter_lines(decode_unicode=True):
            event = parse_stream_line(line)
            if event is None:
                continue
            if event.get('answer_path') != 'other/openAnswer':
                continue
            components = _.get(event, 'section.result_page.components', [])
            comp = _.find(components, lambda c: _.get(c, 'data.datas') is not None)
            if comp is not None:
                datas = _.get(comp, 'data.datas')
        if not datas:
            raise Exception('datas is empty!')
        log and logger.info(f'AI选股成功')
        return pd.DataFrame.from_dict(datas)

    result = while_do(do, retry, sleep, log)

    if result is None:
        log and logger.info(f'AI选股失败')

    return result