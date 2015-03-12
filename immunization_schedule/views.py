from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.http import HttpResponseRedirect
from django.contrib import auth
import os
import requests
import json
import urllib

CLIENT_ID = os.environ.get('DRCHRONO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('DRCHRONO_CLIENT_SECRET')

base_url = 'https://drchrono.com'
# base_url = 'http://www.drchrono.l:8001'
token_url = base_url + '/o/token/'
authorize_url = base_url + '/o/authorize/'


def authorize_handler(request):
    redirect_uri = request.build_absolute_uri(reverse('retrieve'))
    authorize_url_with_redirect = authorize_url + '?redirect_uri=%s&response_type=code&client_id=%s' % (urllib.quote(redirect_uri), urllib.quote(CLIENT_ID))
    return HttpResponseRedirect(authorize_url_with_redirect)


def retrieve_tokens(request):
    code = request.GET['code']
    redirect_uri = request.build_absolute_uri(reverse('retrieve'))
    if code != "":
        token_retrieval_url = token_url + '?code=%s&grant_type=authorization_code&redirect_uri=%s&client_id=%s&client_secret=%s' % (code, urllib.quote(redirect_uri, ''), urllib.quote(CLIENT_ID, ''), urllib.quote(CLIENT_SECRET, ''))

        r = requests.post(token_retrieval_url)

        if r.status_code in [403, 400]:
            return HttpResponseRedirect(reverse('authorize'))

        access_token = json.loads(r.text)['access_token']
        refresh_token = json.loads(r.text)['refresh_token']

        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token

        return HttpResponseRedirect(reverse('list_patients'))
    else:
        return redirect(reverse('home:index'))


def refresh_access(authorized_user):
    token_refresh_url = token_url + "?refresh_token=%s&grant_type=refresh_token&client_id=%s&client_secret=%s" % (urllib.quote(authorized_user.refresh_token), urllib.quote(CLIENT_ID), urllib.quote(CLIENT_SECRET))
    r = requests.post(token_refresh_url)
    access_token = json.loads(r.text)['access_token']
    authorized_user.access_token = access_token
    authorized_user.save()
    return access_token


def list_patients(request):
    if not request.user.is_authenticated():
        return render(request, 'login_error.html')

    access_token = request.session.get('access_token')
    refresh_token = request.session.get('refresh_token')

    if access_token is None:
        return HttpResponseRedirect(reverse('authorize'))

    authorization_header = "Bearer %s" % urllib.quote(access_token)
    headers = {'Authorization': authorization_header}
    user_url = '/api/users/current'
    user_data = requests.get(base_url + user_url, headers=headers).json()
    doctor_url = user_data['doctor']
    doctor_data = requests.get(doctor_url, headers=headers).json()
    patients = retrieve_patients(access_token)
    print(patients[0])
    return render(request,
                  'list_patients.html',
                  {'user': user_data,
                   'doctor': doctor_data,
                   'patients': patients,
                   'refresh_token': refresh_token,
                   'access_token': access_token,
                   'url': doctor_url})


def retrieve_patients(access_token):
    authorization_header = "Bearer %s" % urllib.quote(access_token)
    headers = {'Authorization': authorization_header}
    patients = []
    patients_url = '/api/patients'
    while patients_url:
        data = requests.get(base_url + patients_url, headers=headers).json()
        patients.extend(data['results'])
        patients_url = data['next']  # A JSON null on the last page

    return patients


def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(reverse('home'))


def login(request):
    email = request.POST['email']
    pw = request.POST['password']
    user = authenticate(username=email, password=pw)

    if user is not None:
        if user.is_active:
            print("User is active, valid, and authed")
            auth.login(request, user)
            return HttpResponseRedirect(reverse('list_patients'))
        else:
            print("User is valid but disabled")
            return HttpResponseRedirect(reverse('home'))
    else:
        print("Username and pw were incorrect")
        return HttpResponseRedirect(reverse('home'))


def register(request):
    email = request.POST['email']
    u = User.objects.create_user(email, email, request.POST['password'])
    u.save()
    return HttpResponseRedirect(reverse('list_patients'))


def home(request):
    return render(request, 'index.html')
