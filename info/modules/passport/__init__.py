from flask import Blueprint


# 创建蓝图对象
passport_blu = Blueprint('passport', __name__, url_prefix="/passports")
from . import views