# coding: utf-8

"""
    api~tips.py
    ```````````

    : 首页tips api

    : GET /api/v1.0/tips/ 获取首页每日tip
    : GET /api/v1.0/tips/id/ 获取特定id的tip
    : POST(admin) /api/v1.0/tips/ 发布一条新贴士
    : PUT(admin) /api/v1.0/tips/id/ 更新一条新贴士
    : DElETE(admin) /api/v1.0/tip/id/ 删除一条特定的贴士

"""
from flask import jsonify, url_for, request, current_app
from ..models import Tips
from . import api
from xueer import db
import json
from xueer.decorators import admin_required,moderator_required


@api.route('/tips/', methods=["GET"])
def get_tips():
    """
    获取首页的每日tip, 每次5条
    按时间倒序排列
    """
    page = request.args.get('page', 1, type=int)
    pagination = Tips.query.order_by(Tips.timestamp.desc()).paginate(
        page, per_page=current_app.config['XUEER_TIPS_PER_PAGE'],
        error_out=False
    )
    tips = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_tips', page=page - 1, _external=True)
    next = None
    if pagination.has_next:
        next = url_for('api.get_tips', page=page + 1, _external=True)
    tips_count = len(Tips.query.all())
    if tips_count % current_app.config['XUEER_TIPS_PER_PAGE'] == 0:
        page_count = tips_count//current_app.config['XUEER_TIPS_PER_PAGE']
    else:
        page_count = tips_count//current_app.config['XUEER_TIPS_PER_PAGE']+1
    last = url_for('api.get_tips', page=page_count, _external=True)
    return json.dumps(
        [tip.to_json() for tip in tips],
        ensure_ascii=False,
        indent=1
    ), 200, {'link': '<%s>; rel="next", <%s>; rel="last"' % (next, last)}


@api.route('/tips/<int:id>/', methods=['GET'])
def get_tip_id(id):
    """
    获取已知id对应的tip
    这里涉及一个路由计数
    """
    tip = Tips.query.get_or_404(id)
    if request.method == 'GET':
        tip.views += 1
        db.session.add(tip)
        db.session.commit()
    return jsonify(
        tip.to_json2()
    )


@api.route('/tips/', methods=['POST', 'GET'])
@moderator_required
def new_tip():
    """
    发布一条新贴士
    :param id: 贴士id
    """
    if request.method == "POST":
        tip = Tips.from_json(request.get_json())
        db.session.add(tip)
        db.session.commit()
        return jsonify({'id': tip.id}), 201


@api.route('/tips/<int:id>/', methods=['PUT', 'GET'])
@moderator_required
def update_tip(id):
    """
    更新一条tips
    """
    tip = Tips.query.get_or_404(id)
    if request.method == "PUT":
        tip.title = request.get_json().get('title') or tip.title
        tip.img_url = request.get_json().get('img_url') or tip.img_url
        tip.banner_url = request.get_json().get('banner_url') or tip.banner_url
        tip.body = request.get_json().get('body') or tip.body
        tip.author = request.get_json().get('author') or tip.author
        db.session.add(tip)
        db.session.commit()
        return jsonify({
           'update': tip.id
        })



@api.route('/tip/<int:id>/', methods=['GET', 'DELETE'])
@admin_required
def delete_tip(id):
    """
    删除一个贴士
    :param id: 贴士id
    """
    tip = Tips.query.get_or_404(id)
    if request.method == "DELETE":
        db.session.delete(tip)
        db.session.commit()
        return jsonify({
            'delete': tip.id
        })
