import math

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings

from posts.models import Group, Post

User = get_user_model()


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoNameAuthor')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        cls.POSTS_NUMBER = 15
        pile_of_posts = [Post(
            author=cls.user,
            group=cls.group,
            text=f'Тестовый пост {str(number)}'
        )
            for number in range(cls.POSTS_NUMBER)
        ]
        Post.objects.bulk_create(pile_of_posts)

    def setUp(self):
        self.guest_client = Client()

    def test_first_two_pages_contain_ten_and_thirteen_records(self):
        """Вывод 10 постов на странице, а так же остаточного кол-ва постов
        на последней странице
        """
        last_page_posts = int(self.POSTS_NUMBER - (math.ceil(self.POSTS_NUMBER
                              / settings.POSTS_LIMIT) - 1)
                              * settings.POSTS_LIMIT)
        pages_with_pagination = {
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        }
        for reverse_name in pages_with_pagination:
            response = self.guest_client.get(reverse_name)
            self.assertEqual(
                len(response.context['page_obj']),
                settings.POSTS_LIMIT
            )
            response = self.guest_client.get(
                reverse_name + '?page=' + str(
                    math.ceil(self.POSTS_NUMBER / settings.POSTS_LIMIT)
                )
            )
            self.assertEqual(
                len(response.context['page_obj']), last_page_posts)
