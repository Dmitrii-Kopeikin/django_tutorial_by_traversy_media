from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
# from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import Room, Topic, Message
from .forms import RoomForm


def login_page(request):
    action = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')

        # try:
        #     user = User.objects.get(username=username)
        # except User.DoesNotExist:
        #     messages.error(request, 'User does not exists')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'User not exists or password is incorrect')

    context = {'action': action}
    return render(request, 'base/login_register.html', context=context)


def registration_page(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = UserCreationForm()

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration!')

    context = {
        'form': form,
    }
    return render(request, 'base/login_register.html', context=context)


def logout_user(request):
    logout(request)
    return redirect('home')


def home(request):
    q = request.GET.get('q')
    if q is None:
        q = ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()

    room_count = rooms.count()

    recent_messages = Message.objects.all()

    context = {
        'rooms': rooms,
        'room_count': room_count,
        'topics': topics,
        'recent_messages': recent_messages,
    }
    return render(request, 'base/home.html', context)


def room_page(request, pk):
    room = get_object_or_404(Room, pk=pk)
    room_messages = room.message_set.all().order_by('-created')
    participants = room.participants.all()

    if request.method == "POST":
        Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        if not room.participants.contains(request.user):
            room.participants.add(request.user)
        return redirect('room', pk=pk)

    context = {
        'room': room,
        'room_messages': room_messages,
        'participants': participants,
    }
    return render(request, 'base/room.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'base/room_form.html', context=context)


@login_required(login_url='login')
def update_room(request, pk):
    room = get_object_or_404(Room, pk=pk)
    form = RoomForm(instance=room)

    if request.user != room.host:
        return HttpResponse("It's not your Room!")

    if request.method == 'POST':
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('home')

    context = {'form': form}
    return render(request, 'base/room_form.html', context=context)


@login_required(login_url="login")
def delete_room(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.user != room.host:
        return HttpResponse("It's not your Room!")

    if request.method == "POST":
        room.delete()
        return redirect('home')

    context = {'obj': room}
    return render(request, 'base/delete.html', context=context)


@login_required(login_url='login')
def delete_message(request, pk):
    message = get_object_or_404(Message, pk=pk)

    if request.user != message.user:
        return HttpResponse("You are not allowed here!!!")

    if request.method == 'POST':
        message.delete()
        return redirect('home')

    context = {'obj': message}
    return render(request, 'base/delete.html', context=context)
