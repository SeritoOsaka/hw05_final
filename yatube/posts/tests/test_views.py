from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.forms import PostForm
from ..models import Group, Follow, Post

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
            user=cls.test_user,
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewsTests.user)

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
        ]
        for url in urls:
            with self.subTest(msg=f'Test {url} page'):
                response = self.authorized_client.get(url)
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

    def test_cache(self):
        post = Post.objects.create(
            text='text',
            author=self.user,
            group=self.group
        )
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(response, post.text)
        post.delete()
        second_response = self.authorized_client.get(reverse('posts:index'))
        self.assertContains(second_response, post.text)
        cache.clear()
        third_response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, third_response.content)


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
        follower_count = Follow.objects.count()
        self.client.get(reverse(
            'posts:profile_follow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count + 1)
        follow = Follow.objects.latest('id')
        self.assertEqual(follow.author, self.user_following)
        self.assertEqual(follow.user, self.user_follower)

    def test_unfollow(self):
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        follower_count = Follow.objects.count()
        self.assertEqual(follow.author, self.user_following)
        self.assertEqual(follow.user, self.user_follower)
        self.client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_following.username,)))
        self.assertEqual(Follow.objects.count(), follower_count - 1)
        self.assertQuerysetEqual(
            Follow.objects.filter(
                user=self.user_follower,
                author=self.user_following
            ),
            []
        )

    def test_new_post_see_follower(self):
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_following,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_following
        )
        response = self.client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        second_response = self.client.get(reverse('posts:follow_index'))
        self.assertNotIn(post, second_response.context['page_obj'])
