from http import HTTPStatus

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from posts.forms import PostForm

TEST_NUMBER_OF_POST = 11


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='post_author',
        )
        cls.second_user = User.objects.create_user(
            username='another_user',
        )
        cls.group = Group.objects.create(
            title='Test title',
            slug='test-slug',
            description='Test description',
        )
        cls.group2 = Group.objects.create(
            title='Test title2',
            slug='test-slug-2',
            description='Test description2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Body of test post',
            group=cls.group,
        )
        cls.form = PostForm()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.anouther_user = Client()
        self.anouther_user.force_login(self.second_user)

    def collected_asserts(self, obj, inp):
        self.assertEqual(obj.author, self.post.author)
        self.assertEqual(obj.text, inp['text'])
        self.assertEqual(obj.group.id, inp['group'])

    def test_create_form(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(),
                         posts_count + 1)
        first_post = Post.objects.first()
        self.collected_asserts(first_post, form_data)

    def test_post_edit(self):
        form_data_edit = {
            'text': 'Corrected post',
            'group': self.group2.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data_edit)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}))
        first_post = Post.objects.first()
        self.collected_asserts(first_post, form_data_edit)

    def test_guest_client_create_post(self):
        form_data = {
            'text': 'Post text',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data)
        login = reverse('login')
        new = reverse('posts:post_create')
        redirect = login + '?next=' + new
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), 1)

    def test_guest_client_cant_edit_posts(self):
        form_data_edit = {
            "text": "Corrected post",
            "group": self.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data_edit)
        self.assertRedirects(response, reverse(
            'users:login') + '?next=/posts/1/edit/')

    def test_another_user_edit_post(self):
        posts_count = Post.objects.count()
        form_data_edit = {
            'text': 'New post text',
            'group': self.group.id
        }
        response = self.anouther_user.post(reverse(
            'posts:post_edit',
            kwargs={
                'post_id': self.post.id,
            }),
            data=form_data_edit,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': self.user.username,
            }),)
        self.assertEqual(posts_count,
                         Post.objects.count())
        self.assertNotEqual(self.post.text,
                            form_data_edit['text'])


class PaginatorViewsTest(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        test_posts = []
        for i in range(TEST_NUMBER_OF_POST):
            test_posts.append(Post(text=f'Тестовый текст {i}',
                                   group=self.group,
                                   author=self.user))
        Post.objects.bulk_create(test_posts)

    def test_paginator_context_in_guest_client(self):
        pages = (reverse('posts:index_page'),
                 reverse('posts:profile',
                         kwargs={'username': f'{self.user.username}'}),
                 reverse('posts:group_list',
                         kwargs={'slug': f'{self.group.slug}'}))
        for page in pages:
            response1 = self.guest_client.get(page)
            response2 = self.guest_client.get(page + '?page=2')
            count_posts1 = len(response1.context['page_obj'])
            count_posts2 = len(response2.context['page_obj'])
            self.assertEqual(
                count_posts1,
                settings.DEFAULT_POSTS_PER_PAGE,
            )
            self.assertEqual(
                count_posts2,
                TEST_NUMBER_OF_POST - settings.DEFAULT_POSTS_PER_PAGE,
            )
