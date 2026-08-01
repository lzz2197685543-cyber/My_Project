from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    """自定义注册表单"""
    email = forms.EmailField(
        label='邮箱',
        required=True,
        help_text='请输入有效的邮箱地址。'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': '用户名',
            'email': '邮箱',
            'password1': '密码',
            'password2': '确认密码',
        }