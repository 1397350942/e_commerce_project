# 自定义用户认证的后端: 实现多账号登录
from django.contrib.auth.backends import ModelBackend
import re
from users.models import User


def get_user_by_account(account):
    """
    通过账号获取用户
    :param account: 用户名或者手机号
    :return: user
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):
            # username == 手机号
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):
    """自定义用户认证后端"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        """重写用户认证的方法
        :param username 用户名或者手机号
        :param password 密码
        :param kwargs 额外参数
        :return user
        """
        # 校验username参数是用户名还是手机号
        # try:
        #     if re.match(r'^1[3-9]\d{9}$', username):
        #         # username == 手机号
        #         user = User.objects.get(mobile=username)
        #     else:
        #         user = User.objects.get(username=username)
        # except User.DoesNotExist:
        #     return None
        # else:
        #     return user
        # 使用账号查询用户
        user = get_user_by_account(username)
        # 如果能够查询到用户,还需要校验密码是否正确
        if user and user.check_password(password):
            # 返回user
            return user
        else:
            return None
