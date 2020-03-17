from django.conf.urls import url
from .views import RegisterView

urlpatterns = [
    # 用户注册
    url(r'^register/$', RegisterView.as_view(), name="register")
]
