# coding: utf-8

import json
from flask import Flask, g, session, redirect, url_for, current_app
from flask import render_template,request
from jinja2 import Environment
from . import hello
from xueer import db
from xueer.models import Courses, Tips, Tags, CourseCategories, CourseTag, User, Comments
from flask_login import login_user, current_user
import requests
import base64



def is_mobie():
    platform = request.user_agent.platform
    if platform in ["android", "iphone", "ipad"]:
        return True
    else:
        return False


def add_tags(course):
    """
    判断
        向数据库中添加tag实例
        向数据库中添加tag和course关系
    """
    tags = request.form.get("tags").split()
    # add tag
    for tag in tags:
        tag_in_db = Tags.query.filter_by(name=tag).first()
        if tag_in_db:
            tag_in_db.count += 1
        else:
            add_tag = Tags(name=tag, count=1)
        db.session.add(add_tag)
        db.session.commit()
    # add course & tag
    for tag in tags:
        get_tag = Tags.query.filter_by(name=tag).first()
        course_tags = [tag.tags for tag in course.tags.all()]
        if get_tag in course_tags:
            course_tag = CourseTag.query.filter_by(
                tag_id=get_tag.id, course_id=id,
            ).first()
            course_tag.count += 1
        else:
            course_tag = CourseTag(
                tag_id=get_tag.id, course_id=id, count=1
            )
        db.session.add(course_tag)
        db.session.commit()


def login_xueer_user(user):
    """
    登入学而用户, 请求token, 存入session
    """
    token = user.generate_auth_token()
    login_user(user)
    session[user.username] = token


@hello.route('/')
def index():
    flag = is_mobie()
    if flag:
        return render_template("hello/mobile/index.html")
    else:
        tips = sorted(Tips.query.all(), key=lambda x: x.id, reverse=True)[:3]
        gong_list = Courses.query.filter_by(category_id=1).all()
        gong_top_list = sorted(gong_list, key=lambda x: x.count, reverse=True)[:3]
        zhuan_top_list = sorted(Courses.query.filter_by(category_id=3).all(), key=lambda x: x.count, reverse=True)[:3]
        tong_top_list = sorted(Courses.query.filter_by(category_id=2).all(), key=lambda x:x.count, reverse=True)[:3]
        su_top_list = sorted(Courses.query.filter_by(category_id=4).all(), key=lambda x:x.count, reverse=True)[:3]
        # hot_five = sorted(Courses.query.all)
        return render_template(
            "hello/desktop/pages/index.html", tips=tips,
            gong_top_list=gong_top_list, su_top_list=su_top_list,
            zhuan_top_list=zhuan_top_list, tong_top_list=tong_top_list
        )

# placehold 路由
@hello.route('/search-result/', methods=['GET'])
def get_search_result():
    """get search result"""
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return render_template("hello/desktop/pages/search-result.html")


@hello.route('/course/<int:id>/', methods=['GET', 'POST'])
def course(id):
    """ course index  """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        course_id = id
        page = int(request.args.get('page') or 1)
        former_page = page-2
        next_page = page+2

        info = Courses.query.get_or_404(id)
        info_tags = []
        for course_tag in info.tags.all():
            info_tags.append(Tags.query.get_or_404(course_tag.tag_id))
        category = {
            1: "公", 2: "通", 3: "专", 4: "素"
        }.get(info.category_id)

        get_comment_list = []
        hot_comments = []
        all_comments = Courses.query.get_or_404(id).comment.all()
        all_comments = sorted(all_comments, reverse=True)
        for each_comment in all_comments:
            each_comment.c_time = each_comment.timestamp.strftime("%Y-%m-%d")
            each_comment.user_name = User.query.get_or_404(each_comment.user_id).username
            if each_comment.likes > 3:
                hot_comments.append(each_comment)
        sort_hot_comments = sorted(hot_comments, key=lambda x: x.likes, reverse=True)

        last_page = ((len(all_comments)-1)/5) + 1
        if former_page < 1: former_page = 1
        if next_page > last_page: next_page = last_page
        for each_comment in all_comments[((page-1)*5):(page*5)]:
            get_comment_list.append(each_comment)

        return render_template(
            "hello/desktop/pages/courses.html",
            info = info,
            category = category,
            info_tags = info_tags,
            hot_comments = sort_hot_comments[:3],
            comments = get_comment_list,
            page = page,
            former_page = former_page,
            next_page = next_page,
            course_id = course_id,
            last_page = last_page,
            hot_comments_len = len(sort_hot_comments),
            comments_len = len(all_comments)
        )


@hello.route('/add_comments/', methods=['POST'])
def add_comment():
    cid = int(request.form.get('cid'))
    comment = Comments(
        body = request.form.get('body'),
        user_id = current_user.id,
        course_id = cid
    )
    db.session.add(comment)
    db.session.commit()
    course = Courses.query.get_or_404(cid)
    course.count = len(course.comment.all())
    db.session.add(course)
    db.session.commit()
    add_tags(course)
    return redirect(url_for('hello.course', id=course.id))

@hello.route('/tip/<int:id>/', methods=['GET'])
def tip(id):
    """ tip index """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return render_template("hello/desktop/index.html")


@hello.route('/courses/', methods=['GET'])
def courses():
    """ get courses """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return render_template("hello/desktop/pages/courses.html")


@hello.route('/user/<string:username>/', methods=['GET'])
def user(username):
    """ user index """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return render_template("hello/desktop/index.html")


@hello.route('/login/', methods=['GET', 'POST'])
def login():
    """ login """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return redirect("/auth/login/")


@hello.route('/privateship/', methods=['GET', 'POST'])
def privateship():
    """同步登录, token存入session"""
    email = request.args.get('email')
    user = User.query.filter_by(email=email).first()
    info = requests.get(current_app.config['MUXIAUTH'] + '/api/user/?email=%s' % email).json()
    username = info.get('username')
    password = 'muxi304'  # password placehold
    if user is None:
        u = User(
            username=username, email=email,
            password=base64.b64encode(password))
        db.session.add(u)
        db.session.commit()
    login_xueer_user(user)
    return redirect(url_for('hello.index'))


@hello.route('/register/', methods=['GET', 'POST'])
def register():
    """ register """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        return redirect(current_app.config["MUXIAUTH"] + "/auth/register/")


@hello.route('/category/')
def category():
    """ category """
    if is_mobie():
        return render_template("hello/mobile/index.html")
    else:
        hot_tags = sorted(Tags.query.all(), key=lambda tag: tag.count, reverse=True)[:12]
        return render_template(
            "hello/desktop/pages/category.html",
            hot_tags = hot_tags
        )
