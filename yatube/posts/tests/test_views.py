import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Follow, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image_name = 'small.gif'
        cls.uploaded = SimpleUploadedFile(
            name=cls.image_name,
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='test_user')
        cls.user_without_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
            image=cls.uploaded
        )
        cls.urls = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username':
                                             cls.post.author.username}):
            'posts/profile.html',
        }
        cls.group_without_posts = Group.objects.create(
            title='Второй тестовый заголовок',
            slug='test_slug3',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_2 = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2.force_login(self.user_without_post)
        cache.clear()

    def _assert_post_has_attribs(self, post):
        self.assertEqual(post.id, self.post.id)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.image, f'posts/{self.uploaded}')

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group = response.context['group']
        self.assertEqual(group.title, self.group.title)
        self.assertEqual(group.slug, self.group.slug)

    def test_post_on_pages(self):
        """Новый пост отображается на нужных страницах"""
        for url in self.urls:
            with self.subTest():
                response = self.client.get(url)
                self.assertIn(
                    self.post.text,
                    response.context['page_obj'][0].text
                )

    def test_post_another_group(self):
        """Пост не попал в другую группу где этого поста нет"""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group_without_posts.slug})
        )
        self.assertNotEqual(
            self.post.group,
            response.context['page_obj'] == [0]
        )

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username':
                                             self.post.author.username})
        )
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post = response.context['post']
        self._assert_post_has_attribs(post)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_add_comment(self):
        """Авторизированный пользователь может оставить коментарий"""

        coments = {'text': 'тестовый комментарий'}
        self.authorized_client_2.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=coments, follow=True
        )
        response = self.authorized_client_2.get(f'/posts/{self.post.id}/')
        self.assertContains(response, coments['text'])

    def test_anonym_cannot_add_comments(self):
        """НЕ Авторизированный пользователь не может оставить коментарий"""
        coments = {'text': 'комент не пройдет'}
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=coments, follow=True
        )
        response = self.guest_client.get(f'/posts/{self.post.id}/')
        self.assertNotContains(response, coments['text'])

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='новейший пост',
            author=self.post.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.author = cls.user
        cls.group = Group.objects.create(
            title='Заголовок для тестовой группы',
            slug='test_slug',
            description='Тестовое описание')
        cls.posts = []
        cls.url_params = ''
        cls.templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}):
                        'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': cls.author}):
                        'posts/profile.html',
        }

        for i in range(13):
            cls.posts.append(Post(
                text=f'Тестовый пост {i}',
                author=cls.author,
                group=cls.group
            ))
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def _test_pagination(self, expected_count, url_params=''):
        for reverse_name, template in self.templates_pages_names.items():
            with self.subTest(template=template):
                response = self.client.get(reverse_name + url_params)
                self.assertEqual(
                    len(response.context['page_obj']), expected_count
                )

    def test_first_page_contains_ten_records(self):
        """ Проверяем что пагинатор выдает 10 записей на первой странице"""
        self._test_pagination(10)

    def test_second_page_contains_three_records(self):
        """ Проверяем что пагинатор выдает 3 записи на второй странице"""

        self._test_pagination(3, '?page=2')


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.user_following = User.objects.create_user(username='test_user2')
        cls.user_without_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.group = Group.objects.create(
            title='Заголовок для 1 тестовой группы',
            slug='test_slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания 1 поста',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.client_auth_following = Client()
        self.authorized_client.force_login(self.user)
        self.client_auth_following.force_login(self.user_following)

    def test_follow_authorized(self):
        """ Авторизованный пользователь может подписываться"""
        self.client_auth_following.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_follow_guest(self):
        """ не Авторизованный пользователь  не может подписываться"""
        self.guest_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_unfollow(self):
        """
        Авторизованный пользователь может подписываться и отписаться от автора
        """
        self.client_auth_following.get(
            reverse('posts:profile_follow', kwargs={'username':
                                                    self.user.username})
        )

        self.client_auth_following.get(
            reverse('posts:profile_unfollow', kwargs={'username':
                                                      self.user.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """запись появляется в ленте подписчиков"""
        response = self.client_auth_following.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj'][0].text
        self.assertEqual(post, self.post.text)

    def test_subscription_feed(self):
        """Запись не появляется у неподписанных пользователей"""
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotContains(response, self.post.text)
