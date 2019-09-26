from qiniu import Auth, put_data

access_key = 'jfqPjtmymYc5o1KVOOt1m4cLmX5AEeCaM5Ccnw5q'
secret_key = 'oTX1HPerW1ZEYzz0Hv7pG_4RGYGoxouBcdsihQep'
# 七牛云创建的储存空间名称
bucket_name = 'zjj-flask'


def storage(data):
    try:
        q = Auth(access_key, secret_key)
        token = q.upload_token(bucket_name)
        ret, info = put_data(token, None, data)
        print(ret, info)
    except Exception as e:
        raise e

    if info.status_code != 200:
        raise Exception('上传图片失败')
    return ret['key']

