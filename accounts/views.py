from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render, redirect


# Create your views here.

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.POST['next']:
                return redirect(request.POST['next'])
            else:
                return redirect('main.views.index')
        else:
            return render(request, 'accounts/login.html', context={
                "error": "Invalid login/password."
            })
    else:
        return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('accounts.views.login')
