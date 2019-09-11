from . import index_blu
from flask import render_template


# 测试
@index_blu.route('/')
def index():
    data = {}
    return render_template("/news/index.html", data=data)
