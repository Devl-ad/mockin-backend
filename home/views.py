from django.shortcuts import render


def home(request):
    return render(request, "home/index.html")


def about(request):
    return render(request, "home/about.html")


def contact(request):
    return render(request, "home/contact.html")


def plans(request):
    return render(request, "home/plans.html")


def faqs(request):
    return render(request, "home/faqs.html")
