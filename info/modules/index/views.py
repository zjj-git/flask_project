from info.constants import HOME_PAGE_MAX_NEWS
from info.response_code import RET
from info.utils.common import user_login_data
from . import index_blu
from flask import render_template, session, request, jsonify, g

from info.models import User, News, Category


# 测试
@index_blu.route('/')
@user_login_data
def index():
    # 获取到当前登录用户的id
    # current_user_id = session.get("user_id")
    #
    # current_user_info = User.query.filter(User.id == current_user_id).first()  # 获取当前用户的信息
    user = g.user

    # 按照点击量排序查询出点击最高的前10条新闻
    new_clicks = News.query.order_by(News.clicks.desc()).limit(10).all()  # 获取点击最多的10条新闻

    # 获取新闻分类数据
    category = Category.query.all()

    # 返回给前端查询结果
    data = {"user": user,
            "news_dict": new_clicks,
            "categories": category}

    return render_template("news/index.html", data=data)


@index_blu.route('/news_list')
def news_list():
    """
    获取首页新闻数据
    :return:
    """
    # 1. 获取参数,并指定默认为最新分类,第一页,一页显示10条数据
    page = request.args.get("page")
    cid = request.args.get("cid")
    per_page = request.args.get("per_page")

    # 2. 校验参数
    if not all([page, cid]):
        return jsonify(errno=RET.DATAERR, errmsg="参数错误")

    page = int(page)
    cid = int(cid)
    if not per_page:
        per_page = HOME_PAGE_MAX_NEWS
    else:
        per_page = int(per_page)
    # 默认选择最新数据分类
    # 3. 查询数据
    filters = [News.status == 0]
    if cid != 1:
        filters.append(News.category_id == cid)

    page_info = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page, per_page, False)

    total_page = page_info.pages
    cur_page = page_info.page
    page_news = page_info.items

    news_dict_list = []
    for i in page_news:
        news_dict_list.append(i.to_dict())

    # 将模型对象列表转成字典列表
    data = {"news_dict_list": news_dict_list,
            "total_page": total_page,
            "cur_page": cur_page}

    # 返回数据
    return jsonify(errno=RET.OK, errmsg="新闻首页获取成功", data=data)
