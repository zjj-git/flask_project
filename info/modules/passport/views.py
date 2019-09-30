import random
import re

from flask import request, current_app, abort, make_response, jsonify, session, render_template

from info import redis_store, constants, db
from info.constants import SMS_CODE_REDIS_EXPIRES
from info.models import User
from info.response_code import RET
from info.utils.yuntongxun.sms import CCP
from . import passport_blu
from info.utils.captcha.captcha import captcha


@passport_blu.route('/image_code')
def get_image_code():
    '''
    生成图片验证码
    :return:
    '''
    # 1. 获取参数
    image_code = request.args.get("image_Code")

    # 2. 校验参数
    if not image_code:
        return abort(404)
    # 3. 生成图片验证码

    name, text, image = captcha.generate_captcha()
    print(text)
    # 4. 保存图片验证码

    try:
        redis_store.setex("image_code"+image_code, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.IOERR, errmsg="图形验证保存失败")

    # 5.返回图片验证码
    response = make_response(image)
    response.content_type = "image/jpg"
    return response


@passport_blu.route('/sms_code', methods=["POST"])
def send_sms_code():

    """
    发送短信的逻辑
    :return:
    """
    # 1.将前端参数转为字典
    mobile = request.json.get("mobile")
    image_code = request.json.get("image_code")
    image_code_id = request.json.get("image_code_id")

    # 2. 校验参数(参数是否符合规则，判断是否有值)
    # 判断参数是否有值
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.NODATA, errmsg="参数有误")

    # 3. 先从redis中取出真实的验证码内容
    real_image_code = redis_store.get("image_code" + image_code_id)

    # 4. 与用户的验证码内容进行对比，如果对比不一致，那么返回验证码输入错误
    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="图片验证码过期")

    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")

    phone_number = "^1[3,4,5,7,8]\d{9}$"
    re_result = re.match(phone_number, mobile)
    if not re_result:
        return jsonify(errno=RET.DATAERR, errmsg="请输入正确的电话号码")

    # 5. 如果一致，生成短信验证码的内容(随机数据)
    phone_msg = "%06d" % random.randint(0, 1000000)

    # 6. 发送短信验证码
    print(phone_msg)
    CCP().send_template_sms(mobile, [phone_msg, 5], '1')

    # 保存验证码内容到redis
    redis_store.setex(mobile, constants.SMS_CODE_REDIS_EXPIRES, phone_msg)

    # 7. 告知发送结果
    return jsonify(errno=RET.OK, errmsg="成功")


@passport_blu.route('/register', methods=["POST"])
def register():
    """
    注册功能
    :return:
    """
    # 1. 获取参数和判断是否有值
    mobile = request.json.get("mobile")
    smscode = request.json.get("smscode")
    password = request.json.get("password")

    if not all([mobile, smscode, password]):
        return jsonify(errno=RET.NODATA, errmsg="参数有误")
    # 2. 从redis中获取指定手机号对应的短信验证码的
    redis_phone_msg = redis_store.get(mobile)

    # 3. 校验验证码
    if not redis_phone_msg:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码过期")
    if smscode != redis_phone_msg:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码错误")

    # 4. 初始化 user 模型，并设置数据并添加到数据库
    user = User()
    user.nick_name = mobile
    user.password = password
    user.mobile = mobile

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="账户保存失败")

    # 5. 保存用户登录状态
    session["nick_name"] = user.nick_name

    # 6. 返回注册结果
    return jsonify(errno=RET.OK, errmsg="注册成功")


@passport_blu.route('/login', methods=["POST"])
def login():
    """
    登陆功能
    :return:
    """
    # 1. 获取参数和判断是否有值
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    if not all([mobile, password]):
        return jsonify(errno=RET.NODATA, errmsg="用户名或密码参数缺失")
    # 2. 从数据库查询出指定的用户
    db_user = User.query.filter(User.mobile == mobile).first()

    if not db_user:
        return jsonify(errno=RET.DBERR, errmsg="当前用户未注册")

    # 3. 校验密码
    if not db_user.check_password(password):
        return jsonify(errno=RET.NODATA, errmsg="用户密码错误")
    # 4. 保存用户登录状态
    session["user_id"] = db_user.id
    session["user_nick_name"] = db_user.nick_name
    # 5. 登录成功返回
    return jsonify(errno=RET.OK, errmsg="登录成功")


@passport_blu.route("/logout", methods=['POST'])
def logout():
    """
    清除session中的对应登录之后保存的信息
    :return:
    """
    session.pop("user_id")
    # 返回结果
    return jsonify(errno=RET.OK, errmsg="退出成功")
