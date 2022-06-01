from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_without_post = User.objects.create_user(
            username='test_user_2'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая запись для создания нового поста',
        )

        cls. group = Group.objects.create(
            title=('Заголовок для тестовой группы'),
            slug='test_slug'
        )
        cls.url_names = (
            '/',
            '/group/test_slug/',
            '/profile/test_user/',
            '/posts/1/',
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:profile',
                    kwargs={'username':
                            cls.post.author.username}): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            cls.post.pk}): 'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            cls.group.slug}): 'posts/group_list.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            cls.post.pk}): 'posts/post_create.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(
            self.user_without_post
        )

    def test_public_url(self):
        """страницы доступные всем"""
        for adress in self.url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_list_url_redirect_anonymous_on_admin_login(self):
        """Страница /create/ перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_edit_author(self):
        """ URL доступен только для автора"""
        response = self.authorized_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_edit_non_authorized(self):
        """ URL не доступен неавторизированному клиету"""
        response = self.guest_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_edit__authorized(self):
        """ URL не доступен авторизированному клиету если он не автор """
        response = self.authorized_client_2.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_pages_uses_correct_template(self):
        """URL-адреса используют соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_page_404(self):
        response = self.guest_client.get('/qwerty228/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
