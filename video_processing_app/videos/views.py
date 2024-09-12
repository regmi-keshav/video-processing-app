from django.shortcuts import render
from django.views.generic import TemplateView


class HelloWorldView(TemplateView):
    template_name = 'index.html'
