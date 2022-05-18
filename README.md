# Accounts

# Install requirements to get all necessary packages

### settings.py not included. To work you will need to install 'accounts' app

### email settings

EMAIL_HOST = 

EMAIL_HOST_USER = 

EMAIL_HOST_PASSWORD = 

EMAIL_PORT = 

EMAIL_USE_TLS = 

ACCOUNT_CREATION_MAIL = 

### Fill upward data to pre-config email mailing.

### Add to your urls.py: 
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include("accounts.urls"))
]

### configure static/accounts/textdb.xlsx to set your language worddb using excel.

### On views.py change your default language ( Will be a data stored in session )

### Change the paginatorDefault (Will be modified but will always start with the default one)

# Urls

* accounts/register -> Register new account
* account/login -> Login
* accounts/manage -> Manage accounts
* accounts/manage/id -> Manage each account
* accounts/changepassword/id -> Change account password
* accounts/sessions -> Manage sessions
* accounts/logoff -> Logout actual session

# First register will be an admin account.
