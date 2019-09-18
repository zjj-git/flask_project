from flask import render_template, g, abort, request, jsonify

from info import constants, db
from info.models import News, Comment
from info.modules.news import news_blu
from info.response_code import RET
from info.utils.common import user_login_data


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    user = g.user  # 通过g拿到当前用户的信息

    is_collected = False  # 判断是否收藏该新闻，默认值为 false

    # 查询新闻数据
    new_info = News.query.get(news_id)

    # 按照点击量排序查询出点击最高的前10条新闻
    new_clicks = News.query.order_by(News.clicks.desc()).limit(constants.HOME_PAGE_MAX_NEWS).all()  # 获取点击最多的10条新闻

    # 校验报404错误
    if not new_info:
        abort(404)

    # 进入详情页后要更新新闻的点击次数
    new_info.clicks += 1

    # 获取当前新闻最新的评论,按时间排序
    new_comment = Comment.query.filter(Comment.news_id == new_info.id).order_by(Comment.create_time.desc()).all()

    comments = []
    for comment in new_comment:
        comments.append(comment.to_dict())  # 拿到的是对象的list,需要将每个对象通过to_dict()方法进行拼接(拼接过程会添加user对象)

    if user:
        if new_info in user.collection_news:
            is_collected = True

    # 返回数据
    data = {"user": user.to_dict() if user else None,
            "news": new_info,
            "news_dict": new_clicks,
            "is_collected": is_collected,
            "comments": comments
            }
    print(data)

    return render_template('news/detail.html', data=data)


@news_blu.route("/news_collect", methods=['POST'])
@user_login_data
def news_collect():
    """新闻收藏"""
    user = g.user

    # 获取参数
    news_id = request.json.get("news_id")
    action = request.json.get("action")

    # 判断参数
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg="请登录后进行收藏")

    if not all([news_id, action]):
        return jsonify(errno=RET.DATAERR, errmsg="缺少参数")

    # action在不在指定的两个值：'collect', 'cancel_collect'内
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.DATAERR, errmsg="action:参数错误")

    new_info = News.query.get(news_id)

    if not new_info:
        return jsonify(errno=RET.DBERR, errmsg="新闻不存在")

    # 收藏/取消收藏
    if action == "collect":
        # 收藏
        if new_info not in user.collection_news:
            user.collection_news.append(new_info)
            return jsonify(errno=RET.OK, errmsg="收藏成功")

    else:
        # 取消收藏
        if new_info in user.collection_news:
            user.collection_news.remove(new_info)
            return jsonify(errno=RET.OK, errmsg="取消收藏成功")


@news_blu.route('/news_comment', methods=["POST"])
@user_login_data
def add_news_comment():
    """添加评论"""

    # 用户是否登陆
    user = g.user

    if not user:
        return jsonify(errno=RET.LOGINERR, errmsg="请先进行登录")

    # 获取参数
    news_id = request.json.get("news_id")
    news_comment = request.json.get("comment")

    # 判断参数是否正确
    if not all([news_id, news_comment]):
        return jsonify(errno=RET.DATAERR, errmsg="参数不完整")

    # 查询新闻是否存在并校验
    new_info = News.query.get(news_id)
    if not new_info:
        return jsonify(errno=RET.DBERR, errmsg="新闻不存在")

    # 初始化评论模型，保存数据
    comment = Comment()
    # 配置文件设置了自动提交,自动提交要在return返回结果以后才执行commit命令,如果有回复
    # 评论,先拿到回复评论id,在手动commit,否则无法获取回复评论内容
    comment.user_id = user.id
    comment.news_id = news_id
    comment.content = news_comment
    db.session.add(comment)
    db.session.commit()
    # 返回响应
    return jsonify(errno=RET.DBERR, errmsg="评论成功", data=comment.to_dict())
