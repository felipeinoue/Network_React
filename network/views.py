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


def api_profile(request, user_id):

    # Check request
    if request.method == 'GET':

        # get user
        try:
            user = User.objects.get(pk=user_id)
        except:
            return JsonResponse({"error": "User not found."}, status=404)

        # get following
        try:
            following = Follow.objects.filter(user=user)
        except:
            pass

        # get followers
        try:
            followers = Follow.objects.filter(following=user)
        except:
            pass

        # fill following
        ls_following =[]
        try:
            for i in following:
                ls_following.append(i.id)
        except:
            pass
            
        # fill followers
        ls_followers =[]
        try:
            for i in followers:
                ls_followers.append(i.id)
        except:
            pass

        # create json
        serialize = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'ls_following': ls_following,
            'following_total': len(ls_following),
            'ls_followers': ls_followers,
            'followers_total': len(ls_followers)
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

        # get following
        try:
            target_user = User.objects.get(pk=user_id)
        except:
            return JsonResponse({"error": "User not found."}, status=404)

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