import shutil
import tempfile
from http import HTTPStatus

from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, User, Comment, Follow
from posts.forms import PostForm

TEST_NUMBER_OF_POST = 11
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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
            image=None
        )
        cls.form = PostForm()

    def setUp(self):
        self.gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.easy = SimpleUploadedFile(name='easy.gif',
                                       content=self.gif,
                                       content_type='image/gif')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.anouther_user = Client()
        self.anouther_user.force_login(self.second_user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def collected_asserts(self, obj, inp):
        self.assertEqual(obj.author, self.post.author)
        self.assertEqual(obj.text, inp['text'])
        self.assertEqual(obj.group.id, inp['group'])
        self.assertEqual(obj.image.name, f'posts/{inp["image"].name}')

    def test_create_form(self):
        self.gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.itemgif = SimpleUploadedFile(name='easy_2.gif',
                                          content=self.gif,
                                          content_type='image/gif')
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.id,
            'image': self.itemgif,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(),
                         posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        first_post = Post.objects.first()
        self.collected_asserts(first_post, form_data)

    def test_post_edit(self):
        form_data_edit = {
            'text': 'Corrected post',
            'group': self.group2.pk,
            'image': self.easy
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
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.author = User.objects.create_user(username='someauthor')

    def setUp(self):
        self.guest_client = Client()
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
                                   author=PaginatorViewsTest.author))
        Post.objects.bulk_create(test_posts)

    def test_paginator_context_in_guest_client(self):
        pages = (reverse('posts:index_page'),
                 reverse('posts:profile',
                         kwargs={'username':
                                 f'{PaginatorViewsTest.author.username}'}),
                 reverse('posts:group_list',
                         kwargs={'slug': f'{self.group.slug}'}),
                 reverse('posts:follow_index')
                 )
        Follow.objects.create(user=PaginatorViewsTest.user,
                              author=PaginatorViewsTest.author)

        for page in pages:
            response1 = self.authorized_client.get(page)
            response2 = self.authorized_client.get(page + '?page=2')
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


class CommentFormTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Test group',
                                          slug='test-group',
                                          description='Description')
        self.post = Post.objects.create(text='Test text',
                                        author=self.user,
                                        group=self.group)
        self.comment = Comment.objects.create(post_id=self.post.id,
                                              author=self.user,
                                              text='Test comment')

    def test_create_comment(self):
        comment_count = Comment.objects.count()
        form_data = {'post_id': self.post.id,
                     'text': 'Test comment2'}
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': self.post.id}),
            data=form_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(Comment.objects.filter(
                        text='Test comment2',
                        post=self.post.id,
                        author=self.user
                        ).exists())
        self.assertEqual(Comment.objects.count(),
                         comment_count + 1)

    def test_no_edit_comment(self):
        posts_count = Comment.objects.count()
        form_data = {'text': 'Test comment2'}
        response = self.guest_client.post(reverse('posts:add_comment',
                                          kwargs={'post_id': self.post.id}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotEqual(Comment.objects.count(),
                            posts_count + 1
                            )
