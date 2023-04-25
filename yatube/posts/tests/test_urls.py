from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            author=PostsURLTests.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.urls = {
            "index": '/',
            "group_list": f'/group/{cls.group.slug}/',
            "profile": '/profile/User/',
            "post_detail": f'/posts/{PostsURLTests.post.id}/',
            "post_edit": f'/posts/{PostsURLTests.post.id}/edit/',
            "post_create": '/create/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_names(self):
        urls_names = [
            ("index", "/"),
            ("group_list", reverse("posts:group_list",
                                   args=[PostsURLTests.group.slug])),
            ("profile", reverse("posts:profile",
                                args=[PostsURLTests.user.username])),
            ("post_detail", reverse("posts:post_detail",
                                    args=[PostsURLTests.post.id])),
            ("post_edit", reverse("posts:post_edit",
                                  args=[PostsURLTests.post.id])),
            ("post_create", "/create/"),
        ]
        for name, url in urls_names:
            with self.subTest(name=name):
                self.assertEqual(url, PostsURLTests.urls[name])

    def test_redirect_if_not_logged_in(self):
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsURLTests.post.id})
        ]
        for url in urls:
            response = self.guest_client.get(url, follow=True)
            expected_url = reverse('login') + f'?next={url}'
            self.assertRedirects(response, expected_url)

    def test_post_edit_redirect_not_author(self):
        response = self.guest_client.get(
            reverse("posts:post_edit", args=[PostsURLTests.post.id])
        )
        expected_url = (
            f'{reverse("login")}?next='
            f'{reverse("posts:post_edit", args=[PostsURLTests.post.id])}'
        )
        self.assertRedirects(response, expected_url)

    def test_urls_uses_correct_template(self):
        templates_url_names = [
            (reverse("posts:index"), 'posts/index.html'),
            (reverse("posts:group_list", kwargs={"slug": self.group.slug}),
             'posts/group_list.html'),
            (reverse("posts:profile", kwargs={"username": self.user.username}),
             'posts/profile.html'),
            (reverse("posts:post_detail", kwargs={"post_id": self.post.id}),
             'posts/post_detail.html'),
            (reverse("posts:post_create"), 'posts/post_create.html'),
            (reverse("posts:post_edit", kwargs={"post_id": self.post.id}),
             'posts/post_create.html'),
        ]
        for address, template in templates_url_names:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls(self):
        urls = [
            ("posts:index", {}, 200, self.guest_client),
            ("posts:group_list",
             {"slug": self.group.slug}, 200, self.guest_client),
            ("posts:profile",
             {"username": self.user.username}, 200, self.guest_client),
            ("posts:post_detail",
             {"post_id": self.post.id}, 200, self.guest_client),
            ("posts:post_create",
             {}, 200, self.authorized_client),
            ("posts:post_edit",
             {"post_id": self.post.id}, 200, self.authorized_client),
            ("posts:group_list",
             {"slug": self.group.slug + "x"}, 404, self.guest_client),
        ]
        for url_name, url_kwargs, expected_status_code, client in urls:
            with self.subTest(url_name=url_name, url_kwargs=url_kwargs):
                url = reverse(url_name, kwargs=url_kwargs)
                response = client.get(url)
                self.assertEqual(response.status_code, expected_status_code)
