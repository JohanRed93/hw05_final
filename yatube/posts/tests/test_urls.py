from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post_creator = User.objects.create_user(username='post_author')
        cls.random_user = User.objects.create_user(username='User')
        cls.group = Group.objects.create(
            title="Test title",
            slug="test_slug",
            description="Test description",
        )
        cls.post = Post.objects.create(
            text="Body of test text",
            author=PostURLTests.post_creator,
        )
        cls.pages_guest = (
            '/',
            f'/group/{cls.group.slug}/',
            f'/profile/{cls.post.author}/',
            f'/posts/{cls.post.pk}/',
        )
        cls.pages_authorized = (
            '/create/',
            f'/posts/{cls.post.pk}/edit/',
        )

    def setUp(self):
        self.guest_client = Client()
        self.post_author = Client()
        self.post_author.force_login(self.post_creator)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.random_user)

    def test_correct_template(self):
        templates_url = self.pages_guest + self.pages_authorized
        templates = [
            'posts/index.html',
            'posts/group_list.html',
            'posts/profile.html',
            'posts/post_detail.html',
            'posts/create_post.html',
            'posts/create_post.html',
        ]
        test_data = {templates_url[item]: templates[item]
                     for item in range(len(templates_url))}
        for url, templates in test_data.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, templates)

    def test_pages_location_close_for_guest(self):
        for page in self.pages_authorized:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_pages_location(self):
        for page in self.pages_guest:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_close_for_not_author(self):
        response = self.authorized_client.get(self.pages_authorized[-1])
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404_page(self):
        response = self.guest_client.get('/404_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_only_author_post_edit(self):
        response = self.post_author.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_post_create(self):
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest_on_login(self):
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')
