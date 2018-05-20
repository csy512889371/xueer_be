# coding:utf-8
"""
    tags.py
    ```````

    : 标签API

    : GET /api/v1.0/tags/: 获取所有标签信息
    : GET /api/v1.0/tags/id/: 获取特定id标签信息
    : DELETE(admin) /api/v1.0/tags/id/: 删除特定id标签
    : GET /api/v1.0/courses/id/tags/: 获取特定id课程的所有标签
    ..........................................................

"""
from flask import jsonify, url_for, request, current_app
from xueer.decorators import admin_required
from ..models import Tags, Courses
from . import api
from xueer import db
import json


@api.route('/tags/', methods=["GET"])
def get_tags():
    page = request.args.get('page', 1, type=int)
    pagination = Tags.query.order_by(-(Tags.count)).paginate(
        page, error_out=False,
        per_page=current_app.config['XUEER_TAGS_PER_PAGE']
    )
    tags = pagination.items
    prev = ""
    next = ""
    if pagination.has_prev:
        prev = url_for('api.get_tags', page=page-1, _external=True)
    if pagination.has_next:
        next = url_for('api.get_tags', page=page+1, _external=True)
    tags_count = len(Tags.query.all())
    if tags_count % current_app.config['XUEER_TAGS_PER_PAGE'] == 0:
        page_count = tags_count//current_app.config['XUEER_TAGS_PER_PAGE']
    else:
        page_count = tags_count//current_app.config['XUEER_TAGS_PER_PAGE']+1
    last = url_for('api.get_tags', page=page_count, _external=True)
    return json.dumps(
        [tag.to_json() for tag in tags],
        ensure_ascii=False,
        indent=1
    ), 200, {'link': '<%s>; rel="next", <%s>; rel="last"' % (next, last)}


@api.route('/tags/<int:id>/', methods=["GET"])
def get_tags_id(id):
    """
    获取特定id的标签
    """
    tags = Tags.query.get_or_404(id)
    return jsonify(tags.to_json())


@api.route('/tags/<int:id>', methods=["GET", "DELETE"])
@admin_required
def delete_tags(id):
    tag = Tags.query.get_or_404(id)
    if request.method == "DELETE":
        db.session.delete(tag)
        db.session.commit()
        return jsonify({
            'message': '该标签已移除'
        })


@api.route('/courses/<int:id>/tags/',methods=["GET"])
def get_courses_id_tags(id):
    """
    获取特定id课程的所有标签
    """
    courses = Courses.query.get_or_404(id)
    return jsonify({
        'tags': [tag.to_json() for tag in courses.tags.all()]
    })
