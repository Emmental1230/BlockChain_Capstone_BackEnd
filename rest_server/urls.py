"""rest_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.urls import path
from django.contrib import admin
from rest_framework import routers
from rest_framework_swagger.views import get_swagger_view
from member import views
import member.api


app_name = 'member'

router = routers.DefaultRouter()
router.register('members', member.api.MemberViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/doc', get_swagger_view(title='Rest API Document')),
    path('api-auth/', include('rest_framework.urls')),
    # path('api/', include((router.urls, 'member'), namespace='api')),

    path('api/members/', views.member_list),
    path('api/password/', views.password),
    #path('api/members/<word>', views.member),
    # path('api/generatedid/', views.generate_did),
    path('api/authkey/', views.auth_key),
    path('api/regeneratedid/', views.regenerate_did),
    path('api/getdid/', views.get_did),
    path('api/findmyinfo/', views.findmyinfo),
    path('api/getentry/', views.get_entry),
    path('api/generateentry/', views.generate_entry),
    path('api/entry/', views.entry_list),
    path('api/entryadmin/', views.entry_admin),
    #path('readdid/', readDID),
]
