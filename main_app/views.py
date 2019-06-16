from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic import ListView, DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import uuid
import boto3
from .models import Dog, Toy, Photo
from .forms import FeedingForm


S3_BASE_URL = 'https://s3-us-west-1.amazonaws.com/'
BUCKET = 'dogcol'


def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)


# Create your views here.
class DogCreate(LoginRequiredMixin, CreateView):
    model = Dog
    # fields = '__all__'
    fields = ['breed', 'description', 'age']
    success_url = '/dogs/'


class DogUpdate(UpdateView):
    model = Dog
    # fields = '__all__'
    fields = ['breed', 'description', 'age']
    success_url = '/dogs/'
    
class DogDelete(DeleteView):
    model = Dog
    fields = ['breed', 'description', 'age']

def form_valid(self, form):
    form.instance.user = self.request.user
    return super().form_valid(form)

def home(request):
    return render(request,'home.html')

def about(request):
    return render(request, 'about.html')
@login_required
def index_dogs(request):
    dogs = Dog.objects.filter(user=request.user)
    return render(request, 'dogs/index.html', {'dogs': dogs})

# def detail(request, dog_id):
#     dog = Dog.objects.get(id=dog_id)
#     return render(request,'dogs/detail.html', {'dog':dog})


def detail(request, dog_id):
  dog = Dog.objects.get(id=dog_id)
  toys_dog_doesnt_have = Toy.objects.exclude(id__in = dog.toys.all().values_list('id'))
  feeding_form = FeedingForm()
  return render(request, 'dogs/detail.html', {
    'dog': dog, 'feeding_form': feeding_form,
    'toys': toys_dog_doesnt_have
  })

def add_feeding(request, dog_id):
  form = FeedingForm(request.POST)
  if form.is_valid():
    new_feeding = form.save(commit=False)
    new_feeding.dog_id = dog_id
    new_feeding.save()
  return redirect('detail', dog_id=dog_id)


def add_photo(request, dog_id):
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
    s3 = boto3.client('s3')
    key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
    try:
      s3.upload_fileobj(photo_file, BUCKET, key)
      url = f"{S3_BASE_URL}{BUCKET}/{key}"
      photo = Photo(url=url, dog_id=dog_id)
      photo.save()
    except:
      print('An error occurred uploading file to S3')
  return redirect('detail', dog_id=dog_id)


def assoc_toy(request, dog_id, toy_id):
  Dog.objects.get(id=dog_id).toys.add(toy_id)
  return redirect('detail', dog_id=dog_id)

def unassoc_toy(request, dog_id, toy_id):
  Dog.objects.get(id=dog_id).toys.remove(toy_id)
  return redirect('detail', dog_id=dog_id)



class ToyList(ListView):
  model = Toy

class ToyDetail(DetailView):
  model = Toy

class ToyCreate(CreateView):
  model = Toy
  fields = '__all__'

class ToyUpdate(UpdateView):
  model = Toy
  fields = ['name', 'color']

class ToyDelete(DeleteView):
  model = Toy
  success_url = '/toys/'