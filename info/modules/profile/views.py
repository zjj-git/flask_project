from flask import render_template, g, redirect, request, jsonify

from info import db
from info.constants import HOME_PAGE_MAX_NEWS
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
