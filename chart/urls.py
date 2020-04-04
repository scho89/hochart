from django.urls import path
from . import views

#/chart

app_name = 'chart'

urlpatterns=[
    path('',views.index,name='index'),
    path('signin/',views.signin,name='signin'),
    path('callback/',views.callback,name='callback'),
    path('detail/<uuid:groupid>',views.detail,name='detail'),
    path('sethab/',views.sethab,name='sethab'),
    path('deletehab/',views.deletehab,name='deletehab'),
    path('tree/<uuid:groupid>',views.tree,name='tree'),
    path('tree/',views.treeroot,name='treeroot'),
    path('hab/',views.hab,name='hab'),
    path('who/',views.who,name='who'),
    path('who/search',views.searchLast4,name='searchLast4'),
    ]