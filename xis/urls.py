from django.conf.urls import url, include
from . import views

app_name = "xis"  # This is the app namespace not the app name.

urlpatterns = [

    url(r'^clone-acct/$',  # clones a www.xerocraft.org account to XIS
        views.clone_acct,
        name="clone-acct"),

]
