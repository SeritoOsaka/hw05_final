from django.contrib.auth.models import User
from django.db import models


class Post(models.Model):
    FIRST_FIFTEEN_CHARACTERS = 15
    text = models.TextField(verbose_name='Текст статьи',
                            help_text='Введите текст статьи')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации',
                                    help_text='Укажите дату '
                                              'публикации')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='posts',
                               verbose_name='Автор статьи',
                               help_text='Укажите автора статьи')
    group = models.ForeignKey('Group', blank=True, null=True,
                              on_delete=models.SET_NULL,
                              related_name='posts',
                              verbose_name='Группа статей',
                              help_text='Выберите тематическую группу '
                                        'в выпадающем списке по желанию')
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.text[:Post.FIRST_FIFTEEN_CHARACTERS]


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название группы',
                             help_text='Введите название тематической группы')
    slug = models.SlugField(unique=True, verbose_name='Номер группы',
                            help_text='Укажите порядковый номер группы')
    description = models.TextField(verbose_name='Описание группы',
                                   help_text='Добавьте текст описания группы')

    class Meta:
        verbose_name = 'Группа статей'
        verbose_name_plural = 'Группы статей'
        ordering = ('-title',)

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='comments',
        verbose_name='Комментарии'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор публикации'
    )
    text = models.TextField(
        'Текст комментария',
        help_text='Напишите комментарий',
    )
    created = models.DateTimeField(
        'Дата комментария',
        auto_now_add=True,
    )

    def __str__(self):
        return self.text[:30]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'user'], name='unique_following'
            )
        ]
