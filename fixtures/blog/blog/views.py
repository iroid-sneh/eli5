from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import connection

from .models import Post, Comment


def post_list(request):
    posts = Post.objects.all()
    data = []
    for post in posts:
        comments = Comment.objects.filter(post=post)
        data.append({"title": post.title, "comments": comments.count()})
    return JsonResponse(data, safe=False)


def search(request):
    q = request.GET.get("q", "")
    with connection.cursor() as cur:
        cur.execute(f"SELECT id, title FROM blog_post WHERE title LIKE '%{q}%'")
        rows = cur.fetchall()
    return JsonResponse(rows, safe=False)


def admin_delete_post(request, pk):
    Post.objects.filter(pk=pk).delete()
    return JsonResponse({"ok": True})


@login_required
def create_post(request):
    try:
        post = Post.objects.create(title=request.POST["title"], body=request.POST["body"], author=request.user)
    except:
        pass
    return JsonResponse({"ok": True})


def newsletter_signup(request):
    # TODO: connect to the email provider
    raise NotImplementedError("newsletter not built yet")
