import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug5'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания нового поста',
            group=cls.group,

        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

    def test_post(self):
        """ Проверка валидного поста"""
        count_posts = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='small/gif'
        )
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile',
                    kwargs={'username': (self.post.author.username)})
        )

        self.assertEqual(Post.objects.count(), count_posts + 1)

        self.assertTrue(
            Post.objects.filter(
                text='Данные из формы',
                image='posts/small.gif'
            ).exists()
        )

    def test_guest_new_post(self):
        """
        Проверка что неавторизоанный пользователь не может создавать посты
        """
        count_posts = Post.objects.count()
        form_data = {
            'text': 'Пост от неавторизованного пользователя',
            'group': self.group.id,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertFalse(
            Post
            .objects
            .filter(text=form_data['text'])
            .exists()
        )

    def test_authorized_edit_post(self):
        """Проверка правльности редактирования"""
        count_posts = Post.objects.count()
        uploaded = SimpleUploadedFile(
            name='small1.gif',
            content=self.small_gif,
            content_type='small/gif'
        )
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.id,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            form_data['text'],
            Post.
            objects.
            get(pk=self.post.pk).
            text
        )
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст',
                image='posts/small1.gif'
            ).exists()
        )
