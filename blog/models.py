from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User


class Category(models.Model):
    """文章分类"""
    name = models.CharField('分类名', max_length=50, unique=True)
    slug = models.SlugField('URL标识', max_length=50, unique=True)

    class Meta:
        verbose_name = '分类'
        verbose_name_plural = '分类'

    def __str__(self):
        return self.name


class Post(models.Model):
    """博客文章"""
    title = models.CharField('标题', max_length=200)
    slug = models.SlugField('URL标识', max_length=200, unique=True)
    summary = models.TextField('摘要', blank=True)
    content = models.TextField('正文')

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        verbose_name='分类',
        related_name='posts'
    )

    favorites = models.ManyToManyField(
        User,
        related_name='favorite_posts',
        verbose_name='收藏者',
        blank=True
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '文章'
        verbose_name_plural = '文章'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', kwargs={'pk': self.pk})

    def total_favorites(self):
        """获取收藏总数"""
        return self.favorites.count()