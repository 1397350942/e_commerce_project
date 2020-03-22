from django.conf.urls import url
from .views import RegisterView, UsernameCountView, LoginView, LogoutView

urlpatterns = [
    # 用户注册
    url(r'^register/$', RegisterView.as_view(), name="register"),
    # 判断用户名是否重复注册
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', UsernameCountView.as_view()),
    # 用户登录
    url(r'^login/$', LoginView.as_view(), name="login"),
    # 用户退出登录
    url(r'^logout/$', LogoutView.as_view(), name="logout")
]
