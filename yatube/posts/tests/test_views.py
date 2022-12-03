from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User, Follow
from posts.forms import PostForm


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='FirstTestUser')
        cls.group = Group.objects.create(
            title='Test group title 1',
            slug='first_test_slug',
            description='Test group description 1',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Body of test post',
            group=cls.group,
        )
        cls.user2 = User.objects.create_user(username='SecondTestUser')
        cls.group2 = Group.objects.create(
            title='Test group title 2',
            slug='second_test_slug',
            description='Test group description 2',
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Second post Body',
            group=cls.group2,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def collected_asserts(self, obj):
        self.assertEqual(obj.pk, self.post.pk)
        self.assertEqual(obj.text, self.post.text)
        self.assertEqual(obj.group.slug, self.group.slug)

    def test_main_page_context(self):
        response = self.authorized_client.get(reverse('posts:index_page'))
        self.assertNotAlmostEqual(len(response.context.get('page_obj')), 0)
        first_object = response.context.get('page_obj')[1]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.collected_asserts(first_object)

    def test_group_page_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'first_test_slug'}))
        self.assertNotAlmostEqual(len(response.context.get('page_obj')), 0)
        first_object = response.context.get('page_obj')[0]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.assertEqual(first_object.group, self.post.group)
        self.collected_asserts(first_object)

    def test_profile_page_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author}))
        self.assertNotAlmostEqual(len(response.context.get('page_obj')), 0)
        first_object = response.context.get('page_obj')[0]
        self.assertIn(self.post, response.context.get('page_obj'))
        self.assertEqual(first_object.author, self.post.author)
        self.collected_asserts(first_object)

    def test_post_detail_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}))
        first_obj = response.context.get('post')
        self.assertEqual(first_obj.author, self.post.author)
        self.collected_asserts(first_obj)

    def test_post_edit_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse(
            'posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_context(self):
        templates_pages_names = {
            reverse('posts:index_page'),
            reverse('posts:group_list', kwargs={'slug': self.group2.slug}),
            reverse('posts:profile', kwargs={'username': self.user2.username}),
        }
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                first_object = response.context.get('page_obj')
                self.assertIn(self.post2, first_object)

    def test_not_in_context(self):
        url = reverse('posts:group_list', kwargs={'slug': self.group.slug})
        response = self.guest_client.get(url)
        self.assertNotIn(self.post2, response.context.get('page_obj'))

    def test_cache_context(self):
        before_create_post = self.authorized_client.get(
            reverse('posts:index_page'))
        first_item_before = before_create_post.content
        Post.objects.create(
            author=self.user,
            text='Cash test',
            group=self.group)
        after_create_post = self.authorized_client.get(
            reverse('posts:index_page'))
        first_item_after = after_create_post.content
        self.assertEqual(first_item_after, first_item_before)
        cache.clear()
        after_clear = self.authorized_client.get(reverse('posts:index_page'))
        self.assertNotEqual(first_item_after, after_clear)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth1')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.author = User.objects.create_user(username='someauthor')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_user_following_authors(self):
        count_follow = Follow.objects.filter(user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = reverse(
            'posts:profile',
            kwargs={'username': FollowViewsTest.author.username})
        response = self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                'username': FollowViewsTest.author.username}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertTrue(Follow.objects.filter(
                        user=FollowViewsTest.user,
                        author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow + 1, new_count_follow)

    def test_user_unfollower_authors(self):
        count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        data_follow = {'user': FollowViewsTest.user,
                       'author': FollowViewsTest.author}
        url_redirect = ('/auth/login/?next=/profile/'
                        f'{self.author.username}/unfollow/')
        response = self.guest_client.post(
            reverse('posts:profile_unfollow', kwargs={
                'username': FollowViewsTest.author}),
            data=data_follow, follow=True)
        new_count_follow = Follow.objects.filter(
            user=FollowViewsTest.user).count()
        self.assertFalse(Follow.objects.filter(
            user=FollowViewsTest.user,
            author=FollowViewsTest.author).exists())
        self.assertRedirects(response, url_redirect)
        self.assertEqual(count_follow, new_count_follow)

    def test_follower_see(self):
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='test text')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_follower = self.authorized_client.get(
            reverse('posts:follow_index'))
        new_posts = response_follower.context['page_obj']
        self.assertIn(new_post_follower, new_posts)

    def test_unfollower_no_see(self):
        new_post_follower = Post.objects.create(
            author=FollowViewsTest.author,
            text='test text')
        Follow.objects.create(user=FollowViewsTest.user,
                              author=FollowViewsTest.author)
        response_unfollower = self.authorized_client2.get(
            reverse('posts:follow_index'))
        new_post_unfollower = response_unfollower.context['page_obj']
        self.assertNotIn(new_post_follower, new_post_unfollower)
