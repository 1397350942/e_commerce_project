from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.urls import reverse
import re
from django.db import DatabaseError
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import User
from meiduo_mall.utils.response_code import RETCODE


class UserInfoView(LoginRequiredMixin, View):
    """用户中心"""

    def get(self, request):
        """提供用户中心的页面"""
        # if request.user.is_authenticated:
        #     return render(request, 'user_center_info.html')
        # else:
        #     return redirect(reverse("users:login"))

        # login_url = "/login/"
        # redirect_field_name = ""
        return render(request, 'user_center_info.html')


# Create your views here.
class LogoutView(View):
    """用户退出登录"""

    def get(self, request):
        """实现用户退出登录的逻辑"""
        # 清除状态保持信息
        logout(request)
        # 删除cookies的用户名
        response = redirect(reverse("contents:index"))
        response.delete_cookie("username")
        return response


class LoginView(View):
    """用户登录"""

    def get(self, request):
        """提供用户登录页面"""
        return render(request, 'login.html')

    def post(self, request):
        """实现用户登录逻辑"""
        # 接收参数
        username = request.POST.get("username")
        password = request.POST.get("password")
        remembered = request.POST.get("remembered")
        # 校验参数
        if not all([username, password]):
            return http.HttpResponseForbidden("缺少必传参数")
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden("请输入正确的用户名或者手机号")
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden("密码最少8位,最长20位")
        # 认证用户: 使用账号查询用户是否存在,如果存在,再校验密码是否正确
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'login.html', {"account_errmsg": "账号或密码错误"})
        # 状态保持
        login(request, user)
        # 使用 rememberd确定状态保持周期(实现登录)
        if remembered != "on":
            # 没有记住登录：状态保持在浏览器会话结束就销毁
            request.session.set_expiry(0)
        else:
            # 记住登录: 状态保持周期为两周  默认两周,所以传None
            request.session.set_expiry(None)

        # 先取出next
        next = request.GET.get("next")
        if next:
            # 重定向到next
            response = redirect(next)
        else:
            # 重定向到首页
            # 为了实现再首页右上角展示用户名信息,我们需要将用户名信息缓存到cookie中
            response = redirect(reverse("contents:index"))
        response.set_cookie("username", user.username, max_age=3600 * 24 * 15)
        # 响应结果: 重定向到首页
        # return redirect(reverse("contents:index"))
        return response


class UsernameCountView(View):
    def get(self, request, username):
        """
        :param username: 用户名
        :return: JSON
        """
        # 接收和校验参数
        # 实现主体业务逻辑: 使用username查询对应的记录的条数
        count = User.objects.filter(username=username).count()
        # 响应结果
        return http.JsonResponse({"count": count, "code": RETCODE.OK, "errmsg": "OK"})


class RegisterView(View):
    """用户注册"""

    def get(self, request):
        """提供用户注册页面"""
        return render(request, 'register.html')

    def post(self, request):
        """实现用户注册业务逻辑"""
        # 一、接收参数：表单参数
        username = request.POST.get("username", None)
        password = request.POST.get("password", None)
        password2 = request.POST.get("password2", None)
        mobile = request.POST.get("mobile", None)
        sms_code_client = request.POST.get("sms_code")
        allow = request.POST.get("allow", None)

        # 二、校验参数: 前后端的校验要分开,避免恶意用户越过前端逻辑发请求,要保证后端安全,前后端的校验逻辑要相同
        # 1) 判断参数是否齐全： all([列表])会去校验列表中的元素是否为空,只要有一个为空,返回false
        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden("缺少必传参数")
        # 2) 判断用户名是否是5～20个字符
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden("请输入5～20个字符的用户名")
        # 3) 判断密码是否是8～20个字符
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden("请输入8～20位密码")
        # 4) 判断两次输入的密码是否一致
        if password != password2:
            return http.HttpResponseForbidden("两次输入的密码不一致")
        # 5) 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden("请输入正确的手机号码")
        #  追加业务: 判断短信验证码是否输入正确(对比用户输入的验证码以及redis里面存储的验证码)
        redis_conn = get_redis_connection("verify_code")
        sms_code_server = redis_conn.get("sms_%s" % mobile)
        if sms_code_server is None:
            return render(request, 'register.html', {"sms_code_errmsg": "短信验证码已失效"})
        if sms_code_client != sms_code_server.decode():
            return render(request, 'register.html', {"sms_code_errmsg": "输入短信验证码有误"})
        # 6) 判断用户是否勾选协议
        if allow != "on":
            return http.HttpResponseForbidden("请勾选用户协议")

        # 三、保存注册数据: 是注册业务的核心
        # return render(request, 'register.html', {"register_errmsg": "注册失败"})
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {"register_errmsg": "注册失败"})
        # 实现状态保持
        login(request, user)
        # # 四、响应结果:重定向到首页
        # # return http.HttpResponse("注册成功,重定向到导首页")
        # # return redirect('/')
        # return redirect(reverse('contents:index'))

        # 为了实现再首页右上角展示用户名信息,我们需要将用户名信息缓存到cookie中
        response = redirect(reverse("contents:index"))
        response.set_cookie("username", user.username, max_age=3600 * 24 * 15)
        # 响应结果: 重定向到首页
        # return redirect(reverse("contents:index"))
        return response
