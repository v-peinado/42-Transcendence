from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect

@login_required
@csrf_protect
def chat(request):
    return render(request, 'chat.html', {
        'user_id': request.user.id,
        'username': request.user.username,
    })

