import random

from flask import request, current_app, abort, make_response, jsonify

from info import redis_store, constants
from info.response_code import RET
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
        return jsonify(errno=RET.DBERR, errmsg="图形验证保存失败")
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
        return jsonify(errno=RET.DATAERR, errmsg="参数有误")
    # 3. 先从redis中取出真实的验证码内容
    real_image_code = redis_store.get("image_code"+image_code_id)

    if not real_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码过期")
    # 4. 与用户的验证码内容进行对比，如果对比不一致，那么返回验证码输入错误
    if real_image_code != image_code:
        return jsonify(errno=RET.DATAERR, errmsg="验证码错误")
    # 5. 如果一致，生成短信验证码的内容(随机数据)
    phone_msg = "%06d" % random.randint(0, 1000000)
    # 6. 发送短信验证码
    print(phone_msg)
    # 保存验证码内容到redis
    redis_store.setex(mobile, constants.SMS_CODE_REDIS_EXPIRES, phone_msg)
    # 7. 告知发送结果
    return jsonify(errno=RET.OK, errmsg="成功")
