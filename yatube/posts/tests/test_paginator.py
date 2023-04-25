import math

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PaginatorViewsTest(TestCase):

    INDEX = reverse('posts:index')
    PROFILE = reverse('posts:profile', kwargs={'username': 'User'})
    GROUP_PAGE_URL = reverse('posts:group_list', kwargs={'slug': 'test-slug'})

    @classmethod
    @transaction.atomic
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Описание тестовой группы',
        )
        cls.NUM_POSTS_TO_CREATE = 13
        posts_to_create = []
        for _ in range(cls.NUM_POSTS_TO_CREATE):
            posts_to_create.append(Post(author=cls.user, group=cls.group))
        Post.objects.bulk_create(posts_to_create)
        cls.num_pages = math.ceil(
            cls.NUM_POSTS_TO_CREATE / settings.VIEW_COUNT)
        cls.TEST_URLS = [cls.INDEX, cls.GROUP_PAGE_URL, cls.PROFILE]

    def setUp(self):
        self.authorized_client = Client()

    def test_first_page_contains_ten_records(self):
        for url in self.TEST_URLS:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']), settings.VIEW_COUNT)

    def test_second_page_contains_correct_number_of_records(self):
        for url in self.TEST_URLS:
            with self.subTest(url=url):
                response = self.authorized_client.get(url,
                                                      {'page': self.num_pages})
                expected_last_page_post_count = (
                    self.NUM_POSTS_TO_CREATE
                    - settings.VIEW_COUNT * (self.num_pages - 1)
                )
                self.assertEqual(len(response.context['page_obj']),
                                 expected_last_page_post_count)
