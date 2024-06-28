from django.shortcuts import render

from users.models import Packages


def home(request):
    packages = Packages.objects.all()
    return render(request, "home/index.html", {"packages": packages})


def about(request):
    return render(request, "home/about.html")


def contact(request):
    return render(request, "home/contact.html")


def plans(request):
    return render(request, "home/plans.html")


def faqs(request):
    return render(request, "home/faqs.html")
