import json
import random
from django.core.mail import send_mail
from django.template import loader
from django.conf import settings
import hashlib
from datetime import date
from .models import *
from django.contrib.sessions.models import Session

# language = default, and try to get stored session language
def initializeTextDB(df,language, session):
    try: 
        language = session['language']
    except:
        pass
    texts = df.filter(['key',language]) ## pt-br deve variar de acordo com a session.
    keys = texts['key'].to_list()
    content = texts[language].to_list()
    newvar = {}
    for x in range(0,len(texts)):
        newvar[keys[x]] = content[x]
    return newvar

def processRequest(string):
    try:
        value = json.load(string)
        return (json.loads(value))
    except:
        return ''  

def profiletype(value, texts):
    profiletypes = {
        texts['administrator_text'] : 1
        ,texts['manager_text'] : 2
        ,texts['client_text']: 4
    }
    for x in profiletypes:
        if profiletypes[x] == value:
            return x

def statustypes(value,texts):
    statustypes = {
        texts['Active'] : 0
        ,texts['Password_Blocked'] : 1
        ,texts['Inactive'] : 2
    }
    for x in statustypes:
        if statustypes[x] == value:
            return x    

def randomstring(amount):
 
    random_string = ''
    
    for x in range(amount):
        # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))
    
    return random_string    

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip   

def validatePassword(password, salt, creationdate):

    return hashlib.md5((password + salt[1:-1] + date.strftime(creationdate, '%Y-%m-%d')).encode()).hexdigest()    


def sendmail(htmlpath, retorno, texts):
    html_message = loader.render_to_string(htmlpath,context ={
        "retorno" : retorno
        ,"texts":texts
    })
    send_mail(
        retorno['subject'],
        html_message,
        settings.ACCOUNT_CREATION_MAIL,
        [retorno['emailtext']],
        fail_silently=False,
        html_message=html_message
    ) 

def validateUserMail(username, email, newpass, texts):
    try:
        userinstance = users.objects.filter(username=username)
        if userinstance[0].email == email:
            user_log(id_user = userinstance[0], task = 'resetpassword', ip=userinstance[0].ip, session_key = userinstance[0].session_key).save()
            login_log(username = username, auth=2, ip=userinstance[0].ip, session_key=userinstance[0].session_key).save()
            salt=randomstring(random.randint(5,10))
            userinstance.update(
                password = validatePassword(newpass,salt,userinstance[0].createdate)
                ,salt = salt
                ,expire_pwd = now()
                ,status=0
                )

            return 1
    except Exception as Err:
        #print(Err)
        pass
    return 0    


def functionvalidateSignup(data,texts):
    #print(data)
    finaltext = {"data": ""}
    finaltext['data'] += functionvalidateUsername(data['mainusername'], texts)['data']
    finaltext['data'] +=functionvalidatePassword(data['password'], texts)['data'] 
    finaltext['data'] +=functionvalidateEmail(data['emailtext'], texts)['data']
    if data['password'] != data['repassword']:
        finaltext['data'] += f'<li>{texts["passwordmismatch"]}</li>'
    if len(data['firstname']) > 25:
        data['firstname'] = data['firstname'][0:25]  
    if len(data['lastname']) > 50:
        data['lastname'] = data['lastname'][0:50]

    for x in data:
        #print(data[x])
        if data[x] == '':
            finaltext['data'] += f"<li>{texts['emptyfield']}</li>"   
            break     

    if data['terms'] == 'on':
        finaltext['data'] += f"<li>{texts['notermsandconditions']}</li>"            

    #print(finaltext)

    return finaltext

def destroysession(request):  
    user = users.objects.filter(id = request.session['id'])
    user_log(id_user = user[0], task = 'logoff', ip=user[0].ip, session_key = user[0].session_key).save()
    user.update(online = 0, ip = '', session_key = '')

    
    request.session['id'] = ''
    request.session['firstname'] = ''
    request.session['profile'] = ''  

def createSessionObject():
    # 1 - Pegar todas as sessões ativas.
    sessionobject = Session.objects.all()

    # 2 - Para cada sessão ativa, criar uma lista com os seus dados.
    sessionlist = []
    for x in sessionobject:
        data = x.get_decoded()
        data['session_key'] = x.session_key
        sessionlist.append(data)

    return sessionlist


def validateSignIn(retorno,texts, request):
    ip = get_client_ip(request)
    sessionkey = (request.session.session_key)
    #conn = dbConnect()
    #cursor = conn.cursor()  
    #select = f"select * from `login` where userid = '{username}'"
    #cursor.execute(select)
    #row = cursor.fetchall()
    #conn.close()

    newlogin = login_log(username = retorno['mainusername'], auth=0, ip=ip, session_key=sessionkey)

    try:
        usermodel = users.objects.filter(username = retorno['mainusername'])
        userobject = usermodel[0]
        if userobject.status != 0:
            if userobject.status == 1:
                return 2
            else:
                return 3    
        
        #Deletar todos os ids que compartilham a mesma conta no login.
        sessionlist = createSessionObject()
        for each in sessionlist:
            if each['id'] != '' and int(each['id']) == int(userobject.id) and each['session_key'] != request.session.session_key:
                Session.objects.filter(pk= each['session_key'])[0].delete()

 
        salt = userobject.salt
        creationdate = userobject.createdate
        if userobject.password == validatePassword(retorno['password'], salt, creationdate):
            request.session['id'] = userobject.id
            request.session['firstname'] = userobject.first_name
            request.session['profile'] = userobject.profile_type
            sessionkey = (request.session.session_key)
            
            newlogin.auth = 1
            newlogin.save()

            
            
            user_log(id_user = userobject, task = 'login', ip=ip, session_key = sessionkey).save()


            
            usermodel.update(online = 1, ip=ip, session_key=sessionkey, last_login = now())
            
            
            return 1
    except Exception as error:
        print(error)
        pass

        return 0    

    newlogin.save()

    ## Bloqueio de senha.
    login_attempts = login_log.objects.filter(username = retorno['mainusername']).order_by('-id')[:4]
    #print(login_attempts)
    count = 0
    for x in login_attempts:
        if x.auth == 0:
            count +=1

    if count == 4:
        usermodel = users.objects.filter(username = retorno['mainusername']).update(status = 1)       
        return 2        
            
    return 0


def functionvalidatePassword(password,texts):
    data = []
    key = '0'

    

    data = validateCharacters(password,texts)

    #print(data)


                                        
    return {
        "data": data

    }

def functionvalidateEmail(email,texts):
    
    data = []
    key = '0'

    if emailCharacters(email) == 0:
        data.append(f'<li>{texts["mailinvalidchar"]}</li>') 

    if '@' in email:
        domain = email.split('@')
        domain = domain[1]
        if '.' in domain:
            domains = domain.split('.')
            if len(domains[0]) < 1:
                data.append(f'<li>{texts["domaininvalidbody"]}</li>')  
            if len(domains[1]) < 1:
                data.append(f'<li>{texts["domaininvalidsegment"]}</li>')      
        else:    
            data.append(f'<li>{texts["domainnotdot"]}</li>')  

    else:
        data.append(f'<li>{texts["domainnotat"]}</li>') 

    if email.count('@') > 1:
       data.append(f'<li>{texts["domaindoubleat"]}</li>')     

    if ' ' in email:    
        data.append(f'<li>{texts["emailempty"]}</li>') 



    return {
        "data": '\n'.join(data)
    }       


def functionvalidateUsername(username,texts):
    data = []
    key = ''

    Upper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] ## 2 point
    lower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] ## 4 potins
    numbers = ['0','1','2','3','4','5','6','7','8','9'] ## 8 points

    if 'xn--a' in username:
        return{
                "data":f"<li>{texts['rspinvalido']}</li>"
            }

    try:
        users.objects.get(username=username)
        return{
                "data":f"<li>{texts['Bankuser']}</li>"
            } 
    except: 
        pass   
               
    

    for x in username:
        if x in Upper:
            continue
        elif x in lower:
            continue
        elif x in numbers:
            continue
        else:
            return{
                "data":f"<li>{texts['rspinvalido']}</li>"
            }



    if (len(username) < 4):
            return {
                "data":f"<li>{texts['rspusernamelow']} {len(username)}</li>"
            }
    
    
    return {
        "data":''.join(data)
    }              

def validateCharacters(password, texts):
    data = []
    special = '~!@#$%^*-_=+[{]}/;:,.?' ## 1 point
    Upper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] ## 2 point
    lower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] ## 4 potins
    numbers = ['0','1','2','3','4','5','6','7','8','9'] ## 8 points

    score = 0
    for x in special:
        if x in password:
            score += 1
            break
    for x in Upper:
        if x in password:
            score += 2
            break     
    for x in lower:
        if x in password:
            score += 4
            break             
    for x in numbers:
        if x in password:
            score += 8
            break    
    
    if not score&1:
        data.append(f"<li>{texts['passwordspecial']}</li>")  
    
    if not score&2:
        data.append(f"<li>{texts['passwordupper']}</li>")   
    
    if not score&4:
        data.append(f"<li>{texts['passwordlower']}</li>")  
    
    if not score&8:
        data.append(f"<li>{texts['passwordnumber']}</li>")   


    for x in password:
        if password.count(x) > 3:
            data.append(f"<li>{texts['passwordsequence']}</li>")
            break

    if (len(password) < 8):
        data.append(f"<li>{texts['passwordcharlimit']} {len(password)}</li>")     

    return '\n'.join(data)     


def emailCharacters(email):
    special = "~@!$%^&*_=+}{'?-."
    Upper = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'] ## 2 point
    lower = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z'] ## 4 potins
    numbers = ['0','1','2','3','4','5','6','7','8','9'] ## 8 points

    if 'xn--a' in email:
        return 0


    for x in email:
        if x in special:
            continue
        elif x in Upper:
            continue
        elif x in lower:
            continue
        elif x in numbers:
            continue
        else:
            return(0)
    return (1)     


def isauth(session):
    try:
        if  session['id'] != '':
            return 1
    except:
        pass
    return 0

def isadmin(session):
    if not isauth(session):
        return 0
    getuser = users.objects.filter(id=session['id'])[0]
    if getuser.profile_type == 1:
        return 1
    return 0

def issameuser(session, id):
    if not isauth(session):
        return 0
    getuser = users.objects.filter(id=session['id'])[0]
    if getuser.id == id:
        return 1
    return 0