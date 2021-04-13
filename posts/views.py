from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
User = get_user_model()


def page_paginator(request, post_list):
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return page


def index(request):
    post_list = Post.objects.all()
    return render(request, 'posts/index.html',
                  {'page': page_paginator(request, post_list)})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    return render(request, 'posts/group.html',
                  {'group': group,
                   'page': page_paginator(request, post_list)})


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:index')
    return render(request, 'posts/new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    follower = author.follower.count()
    following = author.following.count()
    post_list = author.posts.all()
    post_count = author.posts.count()
    current_user = request.user.username
    context = {'post_count': post_count,
               'author': author,
               'follower': follower,
               'following': following,
               'current_user': current_user,
               'page': page_paginator(request, post_list)}
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    author = User.objects.get(username=username)
    post_count = author.posts.count()
    post = Post.objects.get(id=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {'post_count': post_count,
               'post': post,
               'author': author,
               'comments': comments,
               'form': form}
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = post.author
        comment.save()
        return redirect('posts:post', username, post_id)
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, username, post_id):
    user = get_object_or_404(User, username=username)

    if request.user != user:
        return redirect('posts:post', username, post_id)

    if request.method == 'GET':
        post = get_object_or_404(Post, id=post_id)
        form = PostForm({'text': post.text, 'group': post.group_id})
        return render(request, 'posts/new.html', {'form': form, 'post': post})

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = Post.objects.get(id=post_id)
            form = PostForm(request.POST,
                            files=request.FILES or None,
                            instance=post)
            form.save()
            return redirect('posts:post', username, post_id)


@login_required
def add_comment(request, username, post_id):
    form = CommentForm(request.POST or None)
    post = Post.objects.get(id=post_id)
    author = User.objects.get(username=request.user)
    if request.method == 'POST' and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = author
        comment.save()
        return redirect('posts:post', username, post_id)
    return render(request, 'posts/comments.html', {'form': form})


def page_not_found(request, exception):
    return render(request, 'misc/404.html', {'path': request.path}, status=404)


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def follow_index(request):
    user = get_object_or_404(User, username=request.user)
    follow = Follow.objects.filter(user=user)
    follow_author = follow.author
    post_list = Post.objects.filter(author=follow_author)
    context = {'page': page_paginator(request, post_list)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not (
            Follow.objects.filter(user=request.user, author=author).exists()
    ):
        follow = Follow(user=request.user, author=author)
        follow.save()
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username)
