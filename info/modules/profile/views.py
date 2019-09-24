from flask import render_template, g, redirect, request, jsonify, current_app, abort

from info import db, constants
from info.constants import HOME_PAGE_MAX_NEWS
from info.models import Category, News, User
from info.modules.profile import profile_blu
from info.response_code import RET
from info.utils.common import user_login_data


@profile_blu.route('/info')
@user_login_data
def user_info():

    user = g.user

    # 如果用户登陆则进入个人中心
    if not user:

        return redirect("/")

    data = {"user": user.to_dict() if user else None}
    return render_template("news/user.html", data=data)


@profile_blu.route('/base_info', methods=["GET", "POST"])
@user_login_data
def base_info():
    """
    用户基本信息
    :return:
    """
    user = g.user
    # 不同的请求方式，做不同的事情
    # 如果是GET请求,返回用户数据
    if request.method == "GET":
        return render_template('news/user_base_info.html', data={"user": g.user.to_dict()})
    if request.method == "POST":
        # 修改用户数据
        # 获取传入参数
        signature = request.json.get("signature")
        nick_name = request.json.get("nick_name")
        gender = request.json.get("gender")

        # 校验参数
        # 修改用户数据
        if signature != "":
            user.signature = signature

        if nick_name != "":
            user.nick_name = nick_name

        if gender == "":
            user.gender = gender

        db.session.commit()

        # 返回
        return jsonify(errno=RET.OK, errmsg='信息修改成功')


@profile_blu.route('/pic_info', methods=["GET", "POST"])
@user_login_data
def pic_info():
    user = g.user
    # 如果是GET请求,返回用户数据
    user = g.user
    if request.method == "GET":
        return render_template('news/user_pic_info.html', data={"user_info": user.to_dict()})

    # 如果是POST请求表示修改头像
    # 1. 获取到上传的图片

    # 2. 上传头像

        # 使用自已封装的storage方法去进行图片上传

    # 3. 保存头像地址
    # 拼接url并返回数据


@profile_blu.route('/pass_info', methods=["GET", "POST"])
@user_login_data
def pass_info():
    user = g.user

    if request.method == "GET":
        return render_template('news/user_pass_info.html')

    # 1. 获取参数
    new_password = request.json.get("new_password")
    old_password = request.json.get("old_password")

    # 2. 校验参数
    if not all([new_password, old_password]):
        return jsonify(errno=RET.DATAERR, errmsg='参数缺失')

    print(user.check_password(old_password))

    # 3. 判断旧密码是否正确
    if user.check_password(old_password):

        # 4. 设置新密码
        user.password = new_password
        db.session.commit()

        # 返回
        return jsonify(errno=RET.OK, errmsg='密码修改成功')
    else:
        return jsonify(errno=RET.DATAERR, errmsg='旧密码不正确')


@profile_blu.route('/collection')
@user_login_data
def user_collection():
    user = g.user

    # 1. 获取参数
    page_num = int(request.args.get("p", 1))
    # 2. 判断参数
    if not page_num:
        return jsonify(errno=RET.DATAERR, errmsg='参数获取失败')

    # 3. 查询用户指定页数的收藏的新闻
    # 进行分页数据查询
    page_num_news = user.collection_news.paginate(page_num, HOME_PAGE_MAX_NEWS, False)

    # 当前页数
    current_page = page_num_news.page

    # 总页数
    total_page = page_num_news.pages

    # 总数据
    count_news = page_num_news.total

    # 收藏列表
    collection_list = page_num_news.items

    # 返回数据
    data = {"collections": collection_list,
            "current_page": current_page,
            "total_page": total_page}
    return render_template('news/user_collection.html', data=data)


@profile_blu.route('/news_release', methods=["GET", "POST"])
@user_login_data
def news_release():
    # GET请求
    user = g.user
    if request.method == "GET":

        # 1. 加载新闻分类数据
        # 2. 移除最新分类
        categories = Category.query.filter(Category.id > 1).all()

        # 返回数据
        data = {"categories": categories}
        return render_template("news/user_news_release.html", data=data)

    # 1. 获取要提交的数据
    if request.method == "POST":
        title = request.form.get("title")
        category_id = request.form.get("category_id")
        digest = request.form.get("digest")
        index_image = request.files.get("index_image")
        content = request.form["content"]

        # 校验参数
        if not all([title, category_id, digest, content]):
            return jsonify(errno=RET.DATAERR, errmsg="发布新闻信息不完整")

        # 3.取到图片，将图片上传到七牛云
        # try:
        #     index_image_data = index_image.read()
        #     # 上传到七牛云
        #     key = storage(index_image_data)
        # except Exception as e:
        #     current_app.logger.error(e)
        #     return jsonify(errno=RET.PARAMERR, errmsg="参数有误")

        # 保存数据
        news = News()
        news.title = title
        news.category_id = category_id
        news.digest = digest
        news.content = content
        news.source = "个人发布"
        news.user_id = user.id

        # 新闻状态,将新闻设置为1代表待审核状态
        news.status = 1
        # 手动设置新闻状态,在返回前commit提交
        db.session.add(news)
        db.session.commit()

        # 返回
        return jsonify(errno=RET.OK, errmsg="发布成功")


@profile_blu.route('/news_list')
@user_login_data
def user_news_list():
    # 查询数据
    user = g.user
    person_news = News.query.filter(News.source == "个人发布", News.user_id == user.id).all()
    news_list = []
    for i in person_news:
        news_list.append(i)

    # 返回数据
    data = {"news_list": news_list}
    return render_template('news/user_news_list.html', data=data)


@profile_blu.route('/user_follow')
@user_login_data
def user_follow():
    # 获取页数
    p = request.args.get("p", 1)
    try:
        p = int(p)
    except Exception as e:
        current_app.logger.error(e)
        p = 1

    user = g.user

    follows = []
    current_page = 1
    total_page = 1
    try:
        paginate = user.followed.paginate(p, constants.USER_FOLLOWED_MAX_COUNT, False)
        # 获取当前页数据
        follows = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)

    user_dict_li = []

    for follow_user in follows:
        user_dict_li.append(follow_user.to_dict())
    data = {"users": user_dict_li,
            "total_page": total_page,
            "current_page": current_page}
    return render_template('news/user_follow.html', data=data)


@profile_blu.route('/other_info')
@user_login_data
def other_info():
    user = g.user

    # 去查询其他人的用户信息
    other_id = request.args.get("user_id")

    if not other_id:
        abort(404)

    # 查询指定id的用户信息
    other = None
    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)

    if not other:
        abort(404)

    # 判断当前登录用户是否关注过该用户
    is_followed = False
    if other and user:
        if other in user.followed:
            is_followed = True

    data = {
        "is_followed": is_followed,
        "user": g.user.to_dict() if g.user else None,
        "other_info": other.to_dict()
    }
    return render_template('news/other.html', data=data)


@profile_blu.route('/other_news_list')
def other_news_list():
    """返回指定用户的发布的新闻"""

    # 1. 取参数
    other_id = request.args.get("user_id")
    page = request.args.get("p", 1)

    # 2. 判断参数
    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        other = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    if not other:
        return jsonify(errno=RET.NODATA, errmsg="当前用户不存在")

    try:
        paginate = other.news_list.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
        # 获取当前页数据
        news_li = paginate.items
        # 获取当前页
        current_page = paginate.page
        # 获取总页数
        total_page = paginate.pages
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据查询失败")

    news_dict_list = []
    for news_item in news_li:
        news_dict_list.append(news_item.to_basic_dict())

    data = {
        "news_list": news_dict_list,
        "total_page": total_page,
        "current_page": current_page
    }
    return jsonify(errno=RET.OK, errmsg="OK", data=data)




