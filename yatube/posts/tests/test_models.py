from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Group, Post, User

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test title',
            slug='Test slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Test text',
        )

    def test_models_have_correct_object_names(self):
        expected_str = [
            (self.post, self.post.text[:Post.FIRST_FIFTEEN_CHARACTERS]),
            (self.group, self.group.title)
        ]

        for model, expected in expected_str:
            with self.subTest(model=model):
                self.assertEqual(str(model), expected)

    def test_field_verbose(self):
        post = self.post
        field_verbose = (
            ('text', 'Текст статьи'),
            ('pub_date', 'Дата публикации'),
            ('group', 'Группа статей'),
        )
        for value, expected in dict(field_verbose).items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)
