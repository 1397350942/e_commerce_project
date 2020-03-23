from django.shortcuts import render
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from django.conf import settings
from django import http
from meiduo_mall.utils.response_code import RETCODE
import logging

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
        return


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
