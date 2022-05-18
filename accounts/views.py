from concurrent.futures import process
from django.shortcuts import render
from django.views import View
from pandas import read_excel
from .validations import *
from django.http import FileResponse, HttpResponseRedirect, JsonResponse
from .models import *
import hashlib
import random
from django.utils import timezone
from datetime import date
import datetime
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.sessions.models import Session

# Create your views here.

df = read_excel('accounts/static/accounts/textdb.xlsx') ## Initialize wordsdb
language = 'pt-br'
paginatorDefault = 10

##Require beeing the administrator
class sessionsView(View):
    def get(self,request):
        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)

        sessionlist = createSessionObject()

        context = {
           "session" : request.session,
            "texts" : texts,
            "objects": sessionlist
            
        }
        
        return render(request, 'accounts/sessions.html', context)

        

##Require beeing the user or the administrator
class passchangeView(View):
    def get(self,request, id):
        texts = initializeTextDB(df,language)
        context = {
           "session" : request.session,
            "texts" : texts,
            "id": id 
        }
        if isauth(request.session) and (isadmin(request.session) or issameuser(request.session,id)):
            return render(request, 'accounts/changepass.html', context)

        return HttpResponseRedirect(reverse('login_page'))
    def post(self,request,id):
        texts = initializeTextDB(df,language)
        context = {
            "session" : request.session,
            "texts" : texts,
            "id": id 
        }
        resposta = processRequest(request)
        if isauth(request.session) and (isadmin(request.session) or issameuser(request.session,id)):
            if resposta and resposta['key'] == 'resetpass':
                context['key'] = texts['goodkey']
                context['return'] = ''
                textoretorno = functionvalidatePassword(resposta['password'],texts)
                getuser = users.objects.filter(id=id)

                if resposta['mainpassword'] == '' or resposta['password'] == '' or resposta['repassword'] == '':
                    context['return'] = {'data': texts['emptyfield']} 
                    print(context['return'])

                elif textoretorno['data'] != '':
                    context['return'] =  textoretorno
                    print(context['return'])

                elif resposta['password'] != resposta['repassword']:
                    context['return'] = {'data': texts['passwordmismatch']}

                elif validatePassword(resposta['mainpassword'],getuser[0].salt,getuser[0].createdate) != getuser[0].password:
                    context['return'] = {'data': texts['wrongpass']}
                
                
                print(context['return'])
                if context['return'] == '':
                    salt = randomstring(random.randint(5,10))
                    print('entrouaqui')
                    getuser.update(
                        password = validatePassword(resposta['password'],salt,getuser[0].createdate),
                        salt = salt
                    ) 
                    context['key'] = texts['acceptkey']
                    user_log(id_user = getuser[0], task = 'resetpassword', ip=getuser[0].ip,
                    session_key = getuser[0].session_key, description = getuser[0].password).save()

                return render(request, 'accounts/response/validations.html', context)


        return HttpResponseRedirect(reverse('login_page'))

##Require beeing an administrator
class eachaccountView(View):
    def get(self, request, id):
        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        se = users.objects.filter(id = id)[0]

        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))

        #Chaves geradas serverside
        keys = [
            'username', 'status', 'profile_type', 'email',
            'first_name', 'last_name', 'last_login',
             'online', 'expire_pwd','ip', 'session_key' 
             ]
            
        #Labels formados serverside
        labels = [
            texts['username'], texts['txtStatus'], texts['txtPerfil'], texts['email'],
            texts['firstname'], texts['lastname'], texts['txtLastLogin'], 
            texts['txtOnline'], texts['txtExpirepwd'],texts['txtIp'], texts['txtSessionKey'] 
            ]

        #Data serverside
        data = [se.username, se.status, se.profile_type, se.email, se.first_name,
        se.last_name, datetime.datetime.strftime(se.last_login, "%Y/%m/%d %H:%M:%S"),
        se.online, datetime.datetime.strftime(se.expire_pwd, "%Y/%m/%d"), se.ip, se.session_key]

        #Item editável ? 1 = sim, 0 = não
        editable = [1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 0]

        #Descrições de cada item individual
        desc = ['', f"0 - {texts['Active']}, 1 - {texts['Password_Blocked']}, 2 - {texts['Inactive']}",
        f"1 - {texts['administrator_text']}, 2 - {texts['manager_text']}, 4 - {texts['client_text']}", '', '', '', '', '', '', '', '']


        combined = {}
        for x in range(len(keys)):
            combined[keys[x]] = {'data':data[x], 'label':labels[x], 'editable': editable[x], "desc": desc[x]}

        userlog = user_log.objects.filter(id_user=id).order_by('-id')

        paginator = Paginator(userlog,paginatorDefault)
        userlog = paginator.get_page(1)

        loginlog = login_log.objects.filter(username=se.username).order_by('-id')

        paginator = Paginator(loginlog,paginatorDefault)
        loginlog = paginator.get_page(1)
        
        try:
            userlogheaders = list(userlog[0].__dict__.keys())[1:]
        except:
            userlogheaders = []

        try:
            loginlogheaders = list(loginlog[0].__dict__.keys())[1:]
        except:
            loginlogheaders = []

        context = {
           "session" : request.session,
            "texts" : texts,
            "combined":combined,
            "userlogheaders": userlogheaders,
            "userlog":userlog,
            "loginlogheaders": loginlogheaders,
            "loginlog": loginlog,
            "id": id
        }

        return render(request, 'accounts/eachaccount.html', context)

    def post(self,request,id):
        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        resposta = processRequest(request)
        se = users.objects.filter(id = id)[0]
        context = {
            "session" : request.session,
            "texts" : texts,
            "id":id
        }

        if resposta and resposta['key'] == 'activities':

            userlog = user_log.objects.filter(id_user=id).order_by('-id')
            paginator = Paginator(userlog,paginatorDefault)
            userlog = paginator.get_page(resposta['page'])
            context['userlogheaders'] = list(userlog[0].__dict__.keys())[1:]
            context['userlog'] = userlog
            return render(request, 'accounts/modals/activities.html', context)

        elif resposta and resposta['key'] == 'logintry':
            

            loginlog = login_log.objects.filter(username=se.username).order_by('-id')
            paginator = Paginator(loginlog,paginatorDefault)
            loginlog = paginator.get_page(resposta['page'])
            context['loginlogheaders'] = list(loginlog[0].__dict__.keys())[1:]
            context['loginlog'] = loginlog
            return render(request, 'accounts/modals/logintry.html', context)

        elif resposta and resposta['key'] == 'change':
            context['key'] = texts['acceptkey']
            position = ''
            try:
                position = 'username'
                if resposta['username'] != se.__dict__['username']:
                    available = functionvalidateUsername(resposta['username'], texts)
                    if  available['data'] == '':
                        se.__dict__['username'] = resposta['username']
                    else:
                        raise Exception(available['data'])
                    

                position = 'status'
                if int(resposta['status']) != int(se.__dict__['status']):
                    available = [0,1,2]
                    if int(resposta['status']) in available:
                        se.__dict__['status'] = int(resposta['status'])
                    else:
                        raise Exception(f'Error, only available: {available}')

                position = 'profile_type'
                if int(resposta['profile_type']) != int(se.__dict__['profile_type']):
                    available = [1,2,4]
                    if int(resposta['profile_type']) in available:
                        se.__dict__['profile_type'] = int(resposta['profile_type'])
                    else:
                        raise Exception(f'Error, only available: {available}')

                position = 'email'
                if resposta['email'] != se.__dict__['email']:
                    available = functionvalidateEmail(resposta['email'], texts)
                    print(available)
                    if  available['data'] == '':
                        se.__dict__['email'] = resposta['email']
                    else:
                        raise Exception(available['data'])
                
                position = 'first_name'
                if resposta['first_name'] != se.__dict__['first_name']:
                    se.__dict__['first_name'] = resposta['first_name']

                position = 'last_name'
                if resposta['last_name'] != se.__dict__['last_name']:
                    se.__dict__['last_name'] = resposta['last_name']
                position = 'expire_pwd'
                if resposta['expire_pwd'] != datetime.datetime.strftime(se.__dict__['expire_pwd'], "%Y/%m/%d"):
                    try:
                        se.__dict__['expire_pwd'] = datetime.datetime.strptime(resposta['expire_pwd'], "%Y/%m/%d")
                    except:
                        raise Exception(texts['wrongdate'])
                se.save()

            except Exception as Err:
                context['return'] = {'data': f"{Err} {texts['txtat']} {texts['txtfield']} {position}"}
                context['key'] = texts['goodkey']
                pass
        

            
            return render(request, 'accounts/response/validations.html', context)
    

##Require loggedin
class manageView(View):
    def get(self, request):
        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        
        context = {
           "session" : request.session,
            "texts" : texts 
        }
        return render(request, 'accounts/manage.html', context)
    def post(self, request):
        if not isadmin(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        retorno = processRequest(request)
        print(retorno)
        searched = users.objects.all()
        if retorno and retorno['key'] == 'search' and retorno['mainusername']:
            searched = searched.filter(username = retorno['mainusername'])
        if retorno and retorno['key'] == 'search' and retorno['firstname']:
            searched = searched.filter(first_name__contains = retorno['firstname'])

        print(searched)

        context = {
           "session" : request.session,
            "texts" : texts,
            "searched": searched 
        }
        return render(request, 'accounts/response/managertable.html', context)

class logoffView(View):
    def get(self, request):
        if not isauth(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        destroysession(request)
        context = {
           "session" : request.session,
            "texts" : texts 
        }
        return render(request, 'accounts/logged.html', context)


class loggedView(View):
    def get(self, request):
        if not isauth(request.session):
            return HttpResponseRedirect(reverse('login_page'))
        texts = initializeTextDB(df,language)
        context = {
           "session" : request.session,
            "texts" : texts 
        }
        return render(request, 'accounts/logged.html', context)


class loginView(View):
    def get(self, request):
        try:
            request.session['id']
        except:
            request.session['id'] = ''
            request.session['firstname'] = ''
            request.session['profile'] = ''
        texts = initializeTextDB(df,language)
        context = {
           "session" : request.session,
            "texts" : texts 
        }
        return render(request, 'accounts/login.html', context)
    def post(self, request):
        texts = initializeTextDB(df,language)
        context = {
           "session" : request.session,
            "texts" : texts 
        }

        retorno = processRequest(request)

        ##Reset mail
        if retorno and retorno['key'] == 'sendresetemail':
            name = users.objects.filter(username = retorno['mainusernamereset'])[0]
            retorno['first_name'] = name.first_name
            retorno['subject'] = texts['passresetsubject']
            retorno['emailtext'] = retorno['mainemailreset']

            sendmail('accounts/email/passwordrecover.html',retorno, texts)
            print('Email enviado')
            responsekey = texts['acceptkey']
            return render(request, 'accounts/response/validations.html', context)   
            

        ##Reset de senha
        if retorno and retorno['key'] == 'reset':
            context['key'] = texts['goodkey']
            context['return'] = {"data": f"<li>{texts['invalidmailuser']}</li>"}
            if validateUserMail(retorno['mainusernamereset'],retorno['mainemailreset'],retorno['newpass'],texts) == 1:
                context['key'] = texts['acceptkey']
                context['return'] = {"data":f"<li>{texts['mailsent']} {retorno['mainemailreset']} </li>"}
            return render(request, 'accounts/response/validations.html', context)  
        ##LOGOFF
        if retorno and retorno['key'] == 'logoff':
            destroysession(request)
            context['key'] = texts['acceptkey']
            return render(request, 'accounts/response/validations.html', context) 


        ##Login
        if retorno and retorno['key'] == 'login':
            context['key'] = texts['goodkey']
            if retorno['mainusername'] == '' or retorno['password'] == '': 
                context['return'] = {"data": f"<li>{texts['emptyfield2']}</li>"} 
                return render(request, 'accounts/response/validations.html', context)   
            else:
                validsignin = validateSignIn(retorno,texts, request)
                if validsignin == 1:
                    context['key'] = texts['acceptkey']
                    return render(request, 'accounts/response/validations.html', context)  
                elif validsignin == 2:
                    context['return'] = {"data": f"<li>{texts['passblock']}</li>"} 
                elif validsignin == 3: 
                    context['return'] = {"data": f"<li>{texts['userblock']}</li>"} 
                else:               
                    context['return'] = {"data": f"<li>{texts['userorpassnotfound']}</li>"}     


        return render(request, 'accounts/response/validations.html', context)   

class validationsView(View):
    def post(self,request):
            
            texts = initializeTextDB(df,language)
            responsekey = texts['goodkey']
            retorno = processRequest(request)
            textoretorno = {
                "data": ""
            }
        
            
            if retorno and retorno['key'] == 'username' and retorno['value'] != '':
                textoretorno = functionvalidateUsername(retorno['value'],texts)
                
            if retorno and retorno['key'] == 'email' and retorno['value'] != '':
                textoretorno = functionvalidateEmail(retorno['value'],texts)    
            if retorno and retorno['key'] == 'password' and retorno['value'] != '':
                textoretorno = functionvalidatePassword(retorno['value'],texts)              
            
            if retorno and retorno['key'] == 'signup':
                textoretorno = functionvalidateSignup(retorno,texts)  
                if textoretorno['data'] == '':
                    salt = randomstring(random.randint(5,10))
                    creationdate = timezone.now()
                    newuser = users(
                        username = retorno['mainusername']
                        ,password = validatePassword(retorno['password'], salt, creationdate)
                        ,status = 0
                        ,createdate = creationdate
                        ,salt = salt
                        ,profile_type = 4
                        ,email = retorno['emailtext']
                        ,first_name = retorno['firstname']
                        ,last_name = retorno['lastname']
                        ) 
                    
                    newuser.save()    
                    print('registrado com sucesso!')

                    responsekey = texts['acceptkey']

            if retorno and retorno['key'] == 'sendemail':
                    retorno['subject'] = texts['accountcreationsubject']
                    sendmail('accounts/email/emailregister.html',retorno, texts)
                    #print('Email enviado')
                    responsekey = texts['acceptkey']


            context={
                "key": responsekey,
                "return" : textoretorno,
                "session" : request.session,
                "texts" : texts
            }

            return render(request, 'accounts/response/validations.html', context)

class registerView(View):
    def get(self,request):
        texts = initializeTextDB(df,language)
        context = {
            "session" : request.session,
            "texts" : texts,
        }
        return render(request, 'accounts/register.html', context)
