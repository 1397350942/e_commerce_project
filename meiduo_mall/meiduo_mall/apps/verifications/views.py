from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from django import http
import random, logging

from . import constants
from meiduo_mall.utils.response_code import RETCODE
from verifications.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import send_sms_code
from verifications.libs.captcha.captcha import captcha

# 创建日志输出器
logger = logging.getLogger("django")


# Create your views here.
class ImageCodeView(View):
    """图形验证码"""

    def get(self, request, uuid):
        """
        :param uuid: 通用唯一识别码,用于唯一标识该图形验证码属于哪个用户的
        :return: image/jpg
        """
        # 接收和校验参数
        # 实现主体业务逻辑: (生成、保存、响应图形验证码)
        # 1）生成图形验证码
        text, image = captcha.generate_captcha()
        # 2）保存图形验证码
        redis_conn = get_redis_connection("verify_code")
        redis_conn.setex("img_%s" % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        # 3）响应图形验证码
        # 响应结果
        return http.HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    """短信验证码"""

    def get(self, request, mobile):
        """
        :param mobile: 手机号
        :return: JSON
        """
        # 一、接收参数
        image_code_client = request.GET.get("image_code")
        uuid = request.GET.get("uuid")
        # 二、校验参数
        if not all([image_code_client, uuid]):
            return http.HttpResponseForbidden("缺少必传的参数")
        # 追加业务:判断用户是否频繁发送短信验证码 提取发送短信验证码的标记
        redis_conn = get_redis_connection("verify_code")
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:  # 防止频繁发送
            return http.JsonResponse({"code": RETCODE.THROTTLINGERR, "errmsg": "发送短信过于频繁"})
        # 三、主体业务逻辑
        # 1) 提取图形验证码

        image_code_server = redis_conn.get("img_%s" % uuid)
        if image_code_server is None:
            return http.JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "图形验证码已失效"})
        # 2) 删除图形验证码
        redis_conn.delete("img_%s" % uuid)
        # 3) 对比图形验证码
        image_code_server = image_code_server.decode()  # 将bytes转字符串,再比较
        if image_code_client.lower() != image_code_server.lower():  # 转小写,再比较
            return http.JsonResponse({"code": RETCODE.IMAGECODEERR, "errmsg": "输入图形验证码有误"})
        # 4) 生成短信验证码: 随机6位数字
        sms_code = "%06d" % random.randint(0, 999999)
        logger.info(sms_code)  # 手动输出日志,记录短信验证码

        # 创建redis管道--> 将命令添加到队列中 --> 执行
        pl = redis_conn.pipeline()  # 创建redis管道
        # 5) 保存短信验证码
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 追加业务: 保存发送短信验证码的标记
        pl.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()  # 执行
        # # 5) 保存短信验证码
        # redis_conn.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # # 追加业务: 保存发送短信验证码的标记
        # redis_conn.setex("send_flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)

        # 6）发送短信验证码
        # CCP().send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)], 1)
        # 使用celery发送短信验证码
        # send_sms_code(mobile, sms_code) 这是错误的写法
        send_sms_code.delay(mobile, sms_code)  # 千万不要忘记写delay
        # 7) 相应结果
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "发送短信成功"})
