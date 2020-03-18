from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.urls import reverse
import re
from django.db import DatabaseError
from django.contrib.auth import login

from users.models import User
from meiduo_mall.utils.response_code import RETCODE


# Create your views here.
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
        # 四、响应结果:重定向到首页
        # return http.HttpResponse("注册成功,重定向到导首页")
        # return redirect('/')
        return redirect(reverse('contents:index'))
