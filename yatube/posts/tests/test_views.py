from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.forms import PostForm
from ..models import User, Group, Follow, Post

User = get_user_model()


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.test_user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.another_group = Group.objects.create(
            title='Группа 2',
            slug='new_group_slug',
            description='Описание группы 2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )
        cls.follow = Follow.objects.create(
            author=cls.user,
            user=cls.test_user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)
        self.follow_client = Client()
        self.follow_client.force_login(PostViewsTests.test_user)

    def test_author_object(self):
        url = reverse('posts:profile', kwargs={'username': self.user})
        response = self.client.get(url)
        self.assertEqual(response.context['author'], self.user)

    def test_group_object(self):
        url = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        response = self.guest_client.get(url)
        self.assertEqual(response.context['group'], self.group)

    def test_post_not_in_another_group(self):
        url = reverse('posts:group_list',
                      kwargs={'slug': self.another_group.slug})
        response = self.guest_client.get(url)
        test_posts = response.context.get('page_obj').object_list
        self.assertNotIn(self.post, test_posts)

    def test_post_context(self):
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': self.post.author.username}),
            reverse('posts:follow_index'),
        ]
        for url in urls:
            with self.subTest(msg=f'Test {url} page'):
                response = self.follow_client.get(url)
                test_post = response.context.get('page_obj')[0]
                self.assertEqual(test_post, self.post)

    def test_post_detail_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post.id})
        )
        test_post = response.context['post']
        test_post_count = response.context['posts_count']
        self.assertEqual(test_post, self.post)
        self.assertEqual(test_post_count, self.post.author.posts.count())

    def test_edit_post_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )

        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context.get('form').instance, self.post)
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_create_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))

        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_cache_index(self):
        response_before_change = self.authorized_client.get(reverse
                                                            ('posts:index'))
        post = Post.objects.first()
        post.text = 'Измененный текст'
        post.save()
        response_after_change = self.authorized_client.get(reverse
                                                           ('posts:index'))
        self.assertEqual(response_before_change.content,
                         response_after_change.content)
        cache.clear()
        response_after_clear = self.authorized_client.get(reverse
                                                          ('posts:index'))
        self.assertNotEqual(response_before_change.content,
                            response_after_clear.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_following = User.objects.create_user(username='follow_user')
        cls.post = Post.objects.create(
            author=cls.user_following,
            text='Тестовый текст',
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user_follower)

    def test_follow(self):
        Follow.objects.count()
        self.client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,)))
        self.assertTrue(
            Follow.objects.filter(author=self.user_following,
                                  user=self.user_follower).exists()
        )

    def test_unfollow(self):
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )

        self.client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,)
        ))

        self.assertFalse(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ).exists()
        )
