from django.core.paginator import Paginator
from django.conf import settings


def get_paginate(page_number, post_list):
    paginator = Paginator(post_list, settings.POSTS_LIMIT)
    page_obj = paginator.get_page(page_number)
    return page_obj
