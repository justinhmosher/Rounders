from django.contrib import admin
from django.urls import path,include
from django.views.generic import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
	path('',views.home,name="home"),
	path('signin/',views.signin,name="signin"),
	path('accept-invite/<str:token>/',views.owner_signup,name="owner_signup"),
	path('staff/',views.staff,name="staff")
]