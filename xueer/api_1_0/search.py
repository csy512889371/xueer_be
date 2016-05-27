# coding: utf-8
"""
    search.py
    `````````

    xueer search api
"""

from . import api
from flask import request, url_for
from xueer import rds, lru
import json


def pagination(lit, page, perpage):
    """
    返回当前分页的列表对象,
    next、last链接
    {current: next_lit}
    """
    _yu = len(lit) % perpage
    _chu = len(lit) // perpage
    if _yu == 0:
        last = _chu
    else:
        last = _chu + 1
    current = lit[perpage*(page-1): perpage*page]
    next_page = ""
    if page < last:
        next_page = url_for('api.search', page=page+1)
    elif page == last:
        next_page = ""
    last_page = url_for('api.search', page=last)
    return [current, (next_page, last_page)]


def category_catch(keywords, main_cat_id=0, ts_cat_id=0):
    """
    类别筛选
    """
    category = {
        1: '公共课', 2:'通识课',
        3: '专业课', 4:'素质课'
    }.get(main_cat_id)
    subcategory = {
        1: '通识核心课',
        2: '通识选修课'
    }.get(ts_cat_id)
    if category and not subcategory:
        gen = (course_json for course_json in lru.keys() \
                if eval(course_json).get('main_category') == category)
    elif subcategory:
        gen = (course_json for course_json in lru.keys() \
                if eval(course_json).get('sub_category') == subcategory)
    else:
        gen = lru.keys()
    results = []
    for course_json in gen:
        searchs = lru.get(course_json)
        for search in eval(searchs):
            if keywords in search:
                results.append(eval(course_json))
    return results


@api.route('/search/', methods=['GET'])
def search():
    """
    搜索API
    """
    keywords = request.args.get('keywords')
    page = int(request.args.get('page')) or 1
    per_page = int(request.args.get('per_page'))
    sort = request.args.get('sort')
    main_cat = request.args.get('main_cat') or '0'
    ts_cat = request.args.get('ts_cat') or '0'
    # 搜索条件匹配
    results = category_catch(keywords, int(main_cat), int(ts_cat))
    # 热搜词存储
    rds.set(keywords, 1) \
        if rds.get(keywords) is None \
        else rds.incr(keywords)
    # 对结果集分页返回返回
    pagination_lit = pagination(results, page, per_page)
    current = pagination_lit[0]
    next_page = pagination_lit[1][0]
    last_page = pagination_lit[1][1]
    return json.dumps(
        current,
        ensure_ascii=False,
        indent=1
    ), 200, {
        'link': '<%s>; rel="next", <%s>; rel="last"' % (next_page, last_page)}


@api.route('/search/hot/', methods=['GET'])
def hot():
    """
    返回最热的10个搜索词
    """
    words = rds.keys()
    hot_words = sorted(words, key=lambda w: int(rds.get(w)), reverse=True)[:10]
    return json.dumps(hot_words), 200
