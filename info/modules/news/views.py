from flask import render_template, g, abort

from info import constants
from info.models import News
from info.modules.news import news_blu
from info.utils.common import user_login_data


@news_blu.route('/<int:news_id>')
@user_login_data
def news_detail(news_id):

    user = g.user  # 通过g拿到当前用户的信息

    # 查询新闻数据
    new_info = News.query.get(news_id)

    # 按照点击量排序查询出点击最高的前10条新闻
    new_clicks = News.query.order_by(News.clicks.desc()).limit(constants.HOME_PAGE_MAX_NEWS).all()  # 获取点击最多的10条新闻

    # 校验报404错误
    if not new_info:
        abort(404)

    # 进入详情页后要更新新闻的点击次数
    new_info.clicks += 1

    # 返回数据
    data = {"user": user.to_dict() if user else None,
            "news": new_info,
            "news_dict": new_clicks}
    return render_template('news/detail.html', data=data)
