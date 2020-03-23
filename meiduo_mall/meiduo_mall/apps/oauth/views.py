from django.shortcuts import render, redirect, reverse
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
import logging
from django_redis import get_redis_connection
import re
from django.contrib.auth import login
from . import utils

from meiduo_mall.utils.response_code import RETCODE
from .models import OAuthQQUser
from users.models import User

# 创建日志输出器
logger = logging.getLogger("django")


# Create your views here.
class QQAuthUserView(View):
    """处理QQ登录回调: oauth_callback"""

    def get(self, request):
        # 获取code
        code = request.GET.get("code")
        # print(code)
        if not code:
            # return http.HttpResponseServerError("获取code失败")
            return http.HttpResponseForbidden("获取code失败")
        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            # 使用code获取 access_token
            access_token = oauth.get_access_token(code)
            # 使用access_token 获取openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError("OAuth2.0认证失败")
        # print(openid)
        # 使用openid判断该QQ用户是否绑定商城的用户
        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # openid 未绑定用户
            access_token_openid = utils.generate_access_token(openid)
            context = {"access_token_openid": access_token_openid}
            return render(request, "oauth_callback.html", context)
        else:
            # openid 已绑定商城用户 oauth_user.user 表示从QQ登录模型类中找到对应的用户模型类对象
            login(request, oauth_user.user)
            # 从哪里来 QQ登录完了 回哪里去
            next = request.GET.get("state")
            response = redirect(next)
            response.set_cookie("username", oauth_user.user.username, max_age=3600 * 24 * 15)
            # 响应QQ登录的结果
            return response

    def post(self, request):
        """实现绑定用户的逻辑"""
        # 接收参数
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        sms_code_client = request.POST.get("sms_code")
        access_token_openid = request.POST.get("access_token_openid")
        # 校验参数
        # 判断参数是否齐全
        if not all([mobile, password, sms_code_client]):
            return http.HttpResponseForbidden("缺少必传参数")
        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden("请输入正确的手机号码")
        # 判断密码是否合格
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden("请输入8-20位的密码")
        # 判断短信验证码是否一致
        redis_conn = get_redis_connection("verify_code")
        sms_code_server = redis_conn.get("sms_%s" % mobile)
        if sms_code_client is None:
            return render(request, "oauth_callback.html", {"sms_code_errmsg": "无效的短信验证码"})
        if sms_code_client != sms_code_server.decode():
            return render(request, "oauth_callback.html", {"sms_code_errmsg": "输入短信验证码错误"})
        # 判断openid是否有效: openid使用itdangeroius签名后只有600S有效期
        openid = utils.check_access_token(access_token_openid)
        if not openid:
            return render(request, "oauth_callback.html", {"openid_errmsg": "openid已失效"})
        # 使用手机号查询对应的用户是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 如果手机号用户不存在,新建用户
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            # 如果手机号用户存在,需要校验密码
            if not user.check_password(password):
                return render(request, "oauth_callback.html", {"account_errmsg": "账号或者密码错误"})

        # 将用户绑定到openid
        # oauth_qq_user = OAuthQQUser(user=user, openid=openid)
        # oauth_qq_user.save()
        try:
            oauth_qq_user = OAuthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            logger.error(e)
            return render(request, "oauth_callback.html", {"qq_login_errmsg": "账号或者密码错误"})

        # openid 已绑定商城用户 oauth_user.user 表示从QQ登录模型类中找到对应的用户模型类对象
        login(request, oauth_qq_user.user)
        # 重定向到state: 从哪里来 QQ登录完了 回哪里去
        next = request.GET.get("state")
        response = redirect(next)
        response.set_cookie("username", oauth_qq_user.user.username, max_age=3600 * 24 * 15)
        # 响应QQ登录的结果
        return response


class QQAuthURLView(View):
    """提供QQ登录扫码"""

    def get(self, request):
        # 接收参数 next
        next = request.GET.get("next")

        # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID, client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        # 生成QQ登录扫码链接地址
        login_url = oauth.get_qq_url()
        # 响应
        return http.JsonResponse({"code": RETCODE.OK, "errmsg": "OK", "login_url": login_url})
