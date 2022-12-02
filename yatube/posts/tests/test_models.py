from django.conf import settings
from django.test import TestCase

from ..models import Group, Post, User


class ModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.group = Group.objects.create(
            title='Test title',
            slug='slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='More text' * 100,
        )

    def test_object_names(self):
        test_data = {
            self.post: self.post.text[:settings.DEFAULT_POSTS_PER_PAGE],
            self.group: self.group.title,
        }
        for field, expected_value in test_data.items():
            with self.subTest(field=field):
                self.assertEqual(
                    field.__str__(),
                    expected_value
                )
