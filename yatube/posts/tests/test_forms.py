from posts.models import Group, Post, Comment, User
from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='Group description'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    def setUp(cls):
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_post_with_picture(self):
        # удаляем все посты из базы данных
        Post.objects.all().delete()
        form_data = {
            'text': 'Test text',
            'group': self.group.pk,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.last()
        self.assertEqual(self.uploaded, form_data['image'])
        self.assertEqual(post.group.id, form_data['group'])
        self.assertEqual(post.author, PostCreateFormTests.user)
        self.assertEqual(post.text, form_data['text'])

    def test_guest_create_post(self):
        form_data = {
            'text': 'Non authorized test post',
            'group': self.group.pk,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text']
            ).exists()
        )

    def test_authorized_edit_post(self):
        form_data = {
            'text': 'Edited post',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        edit_post = Post.objects.get(pk=self.post.pk)
        self.assertEqual(edit_post.group.id, form_data['group'])
        self.assertEqual(edit_post.author, self.post.author)
        self.assertEqual(edit_post.text, form_data['text'])

    def test_add_comment(self):
        Comment.objects.all().delete()
        form_data = {
            'text': 'Test comment',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.id,)),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=(self.post.id,)))
        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.last()
        self.assertEqual(comment.post.id, self.post.id)
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(comment.author, self.user)
