import tempfile
import shutil

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.conf import settings

from posts.models import Group, Post, Comment, Follow
from posts.forms import PostForm, CommentForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='NoNameAuthor')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-slug',
            description='Тестовое описание группы',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.wrong_group = Group.objects.create(
            title='Тестовое название группы 2',
            slug='test-slug2',
            description='Тестовое описание группы 2'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_pages_with_posts_show_correct_context(self):
        """Шаблоны index, group_list и profile сформированы
        с правильным контекстом.
        """
        templates_page_names = {
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.post.author}),
        }
        for reverse_name in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertIn(self.post, response.context.get('page_obj'))

    def test_both_profile_and_group_show_correct_context(self):
        """Шаблоны group_posts и  profile сформированы
        с правильным контекстом
        """
        templates_page_names = [
            (reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
                'group',
                self.group),
            (reverse('posts:profile', kwargs={'username': self.user.username}),
                'author',
                self.user),
        ]
        for reverse_name, context_name, expected in templates_page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertEqual(response.context.get(context_name), expected)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        self.comment = Comment.objects.create(
            post_id=self.post.id,
            author=self.user,
            text='Тестовый коммент'
        )
        response = self.author_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context.get('form'), CommentForm)
        self.assertEqual(response.context.get('post'), self.post)

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        self.assertIsInstance(response.context.get('form'), PostForm)
        self.assertEqual(response.context.get(
            'form').instance,
            self.post
        )

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        self.assertIsInstance(response.context.get('form'), PostForm)

    def test_new_post_not_in_a_wrong_group(self):
        """Пост не появляется в не своей группе"""
        response = self.author_client.get(
            reverse('posts:group_posts', kwargs={
                'slug': self.wrong_group.slug
            })
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))

    def test_cache_index_page(self):
        reverse_name = reverse('posts:index')
        response_start = self.guest_client.get(reverse_name)
        post = Post.objects.create(
            text='Test Text',
            author=self.user,
            group=self.group,
        )
        response_after_post_create = self.guest_client.get(reverse_name)
        post.delete()
        response_after_post_delete = self.guest_client.get(reverse_name)
        self.assertEqual(response_after_post_create.content,
                         response_after_post_delete.content)
        cache.clear()
        response_cache_cleared = self.guest_client.get(reverse_name)
        self.assertEqual(response_start.content,
                         response_cache_cleared.content)


class FollowPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create_user(username='TestFollower')
        cls.following = User.objects.create_user(username='TestFollowing')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.following,
        )

    def setUp(self):
        self.follower_client = Client()
        self.following_client = Client()
        self.follower_client.force_login(self.follower)
        self.following_client.force_login(self.following)

    def test_follow(self):
        """Подписка на другого пользователя работает корректно"""
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.following.username}))
        self.assertTrue(Follow.objects.filter(
            user=self.follower,
            author=self.following)
        )

    def test_unfollow(self):
        """Отписка от другого пользователя работает корректно"""
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.following.username}))
        self.follower_client.get(reverse('posts:profile_unfollow',
                                 kwargs={'username': self.following.username}))
        self.assertFalse(Follow.objects.filter(
            user=self.follower,
            author=self.following)
        )

    def test_new_following_post_shows_only_in_followers_page(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        self.follower_client.get(reverse('posts:profile_follow',
                                 kwargs={'username': self.following.username}))
        is_following = Follow.objects.filter(user=self.follower,
                                             author=self.following).exists()
        self.assertTrue(is_following)
        response = self.follower_client.get(reverse('posts:follow_index'))
        follow_posts_count = len(response.context.get('page_obj'))
        self.assertIn(self.post, response.context.get('page_obj').object_list)
        self.follower_client.get(reverse('posts:profile_unfollow',
                                 kwargs={'username': self.following.username}))
        is_following = Follow.objects.filter(user=self.follower,
                                             author=self.following).exists()
        self.assertFalse(is_following)
        response = self.follower_client.get(reverse('posts:follow_index'))
        unfollow_posts_count = len(response.context.get('page_obj'))
        self.assertEqual(follow_posts_count - 1, unfollow_posts_count)
