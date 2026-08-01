from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Post, Category
from .forms import RegisterForm


def index(request):
    """博客首页：文章列表 + 分类筛选 + 关键词搜索"""
    posts = Post.objects.all().order_by('-created_at')

    category_slug = request.GET.get('category', '')
    keyword = request.GET.get('q', '')

    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    if keyword:
        posts = posts.filter(
            Q(title__icontains=keyword) | Q(summary__icontains=keyword)
        )

    categories = Category.objects.all()

    context = {
        'posts': posts,
        'categories': categories,
        'category_slug': category_slug,
        'keyword': keyword,
        'title': 'LZZ 博客 - 首页',
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, pk):
    """文章详情页"""
    post = get_object_or_404(Post, pk=pk)
    context = {
        'post': post,
        'title': f'{post.title} - LZZ 博客'
    }
    return render(request, 'blog/post_detail.html', context)


def register(request):
    """用户注册"""
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'注册成功，欢迎你，{user.username}！')
            return redirect('index')
    else:
        form = RegisterForm()

    return render(request, 'blog/register.html', {
        'form': form,
        'title': '注册 - LZZ 博客'
    })


@login_required
def toggle_favorite(request, pk):
    """切换收藏状态"""
    post = get_object_or_404(Post, pk=pk)

    if post.favorites.filter(id=request.user.id).exists():
        post.favorites.remove(request.user)
        messages.info(request, f'已取消收藏「{post.title}」')
    else:
        post.favorites.add(request.user)
        messages.success(request, f'已收藏「{post.title}」')

    return redirect(request.META.get('HTTP_REFERER', 'index'))