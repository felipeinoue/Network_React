import json
import requests

from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import *


def index(request):
    return render(request, "network/index.html")


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


# ############ APIs ############


def api_create_post(request):

    # Check request
    if request.method == "POST":

        # start variables
        data = json.loads(request.body)
        description = data.get('description')

        # check if description is empty
        if description == '':
            return JsonResponse({"error": "Description should not be empty."}, status=400)

        # get user
        try:
            user = User.objects.get(pk=request.user.id)
        except:
            pass

        # create post
        try:
            post = Post(
                user=user,
                description=description
            )
            post.save()
            return JsonResponse({"message": "Post succesfully created."}, status=201)
        except:
            return JsonResponse({"error": "There was a problem creating a new post."}, status=400)

    # Method invalid
    else:
        return JsonResponse({"error": "Invalid method."}, status=400)


def api_posts(request, type):

    # Check request
    if request.method == 'GET':

        # get posts

        # all
        if type == 'all':
            try:
                posts = Post.objects.all()
            except:
                return JsonResponse({"error": "There was an error to get all posts."}, status=400)
        
        # user_x
        elif 'user_' in type:
            user_id = type.replace('user_','')
            
            # get user
            try:
                user = User.objects.get(pk=user_id)
            except:
                return JsonResponse({"error": "There was an error to get the profile user."}, status=400)

            # get user posts
            try:
                posts = Post.objects.filter(user=user)
            except:
                return JsonResponse({"error": "There was an error to get the user posts."}, status=400)
        
        elif type == 'following':

            # get user
            try:
                follows = Follow.objects.filter(user=request.user.id)
            except:
                return JsonResponse({"error": "There was an error to get the users that the user follows."}, status=400)

            # create list with all users that the user follows
            ls_user_follow = []
            for follow in follows:
                ls_user_follow.append(follow.following.id)
            
            # get posts
            try:
                posts = Post.objects.filter(user__in=ls_user_follow)
            except:
                return JsonResponse({"error": "There was an error to get the posts from the users that the user follows."}, status=400)

        # invalid parameter
        else:
            return JsonResponse({"error": "parameter not found."}, status=400)


        # check if posts are not empty
        if not posts:
            return JsonResponse({"error": "No posts found."}, status=400)

        # start variables
        ls_posts = []

        # prepare data
        for post in posts:

            # start variables
            total_likes = 0
            is_liked = False
            posts_serialize = {}

            # get likes of the post
            try:
                users_like = post.likes.all()
                for user_like in users_like:
                    total_likes = total_likes + 1
                    if request.user.id == user_like.id:
                        is_liked = True
            except:
                pass

            # prepare data
            posts_serialize = {
                'post_id': post.id,
                'first_name': post.user.first_name,
                'last_name': post.user.last_name,
                'description': post.description,
                'date_created': post.date_created,
                'total_likes': total_likes,
                'is_liked': is_liked
            }

            # append to list
            ls_posts.append(posts_serialize)

        # create json
        serialize = {
            "ls_posts": ls_posts
        }
        return JsonResponse(serialize, status=200)

    # Method invalid
    else:
        return JsonResponse({"error": "Invalid method."}, status=400)


def api_profile(request, user_id):

    # Check request
    if request.method == 'GET':

        # get user
        try:
            user = User.objects.get(pk=user_id)
        except:
            return JsonResponse({"error": "User not found."}, status=404)

        # check if profile owner
        if user.id == request.user.id:
            is_profile_owner = True
        else:
            is_profile_owner = False

        # get following (users that the profile user is following)
        try:
            followings = Follow.objects.filter(user=user)
        except:
            pass

        # get total following
        total_following = 0
        for following in followings:
            total_following += 1

        # get followers (users that are following the profile user)
        try:
            followers = Follow.objects.filter(following=user)
        except:
            pass
        
        # get total followers and check if is follower
        total_followers = 0
        is_follower = False
        for follower in followers:
            total_followers += 1
            if follower.id == request.user.id:
                is_follower = True

        # create json
        serialize = {
            'user_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_profile_owner': is_profile_owner,
            'total_following': total_following,
            'total_followers': total_followers,
            'is_follower': is_follower
        }

        # return json
        return JsonResponse(serialize, status=200)

    # Method invalid
    else:
        return JsonResponse({"error": "Invalid method."}, status=400)


def api_follow(request, user_id):

    # Check request
    if request.method == 'POST':

        # get user
        try:
            user = User.objects.get(pk=request.user.id)
        except:
            return JsonResponse({"error": "User not found."}, status=404)

        # get user to be followed
        try:
            target_user = User.objects.get(pk=user_id)
        except:
            return JsonResponse({"error": "User to be followed not found."}, status=404)

        # check if user is trying to follow himself
        if (user == target_user):
            return JsonResponse({"error": "User canno't follow himself."}, status=400)

        # check if user is already following target user
        try:
            attempt = Follow.objects.get(user=user, following=target_user)
            return JsonResponse({"error": "User already follows this user."}, status=400)
        except:
            pass

        # attempt to follow
        try:
            follow = Follow(
                user=user,
                following=target_user
            )
            follow.save()
            return JsonResponse({"message": "Follow succesfully added."}, status=201)
        except:
            return JsonResponse({"error": "Couldn't Follow user."}, status=400)

    # Method invalid
    else:
        return JsonResponse({"error": "Invalid method."}, status=400)


def api_like(request, post_id):

    # Check request
    if request.method == 'POST':

        # get user
        try:
            user = User.objects.get(pk=request.user.id)
        except:
            return JsonResponse({"error": "User not found."}, status=404)

        # get post
        try:
            post = Post.objects.get(pk=post_id)
        except:
            return JsonResponse({"error": "Post not found."}, status=404)

        # check if user already liked the post
        likes = post.likes.all()
        liked = False
        for like in likes:
            if like.id == request.user.id:
                liked = True

        if not liked:
            # attemp to like post
            try:
                post.likes.add(user)
                return JsonResponse({"message": "Like succesfully added."}, status=201)
            except:
                return JsonResponse({"error": "There was an error adding the like to the post."}, status=400)
        else:
            # attemp to like post
            try:
                post.likes.remove(user)
                return JsonResponse({"message": "Like succesfully removed."}, status=201)
            except:
                return JsonResponse({"error": "There was an error removing the like from the post."}, status=400)

    # Method invalid
    else:
        return JsonResponse({"error": "Invalid method."}, status=400)