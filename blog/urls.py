from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'blog'  # 命名空间

urlpatterns = [
    # 首页
    path('', views.index, name='index'),

    # 文章详情
    path('post/<int:pk>/', views.post_detail, name='post_detail'),

    # 收藏功能
    path('post/<int:pk>/favorite/', views.toggle_favorite, name='toggle_favorite'),

    # 用户认证
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='blog/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]