from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings

from users.api import UserDetails, UserRegister
from portfolios.api import PortfolioList, PortfolioDetails

from users.views import MainView, LoginView, LogoutView
from portfolios.views import Portfolios, PortfolioView, DeletePortfolio

urlpatterns = [
                  path('admin/', admin.site.urls),

                  path('', MainView.as_view()),
                  path('login/', LoginView.as_view()),
                  path('logout/', LogoutView.as_view()),
                  path('portfolios/', Portfolios.as_view()),
                  path('portfolios/<int:pk>/', PortfolioView.as_view()),
                  path('portfolios/add/', Portfolios.as_view()),
                  path('portfolios/<int:pk>/delete/', DeletePortfolio.as_view()),

                  url(r'^api/v1/o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
                  path('api/v1/register/', UserRegister.as_view()),
                  path('api/v1/users/<int:pk>/', UserDetails.as_view()),

                  path('api/v1/portfolios/', PortfolioList.as_view()),
                  path('api/v1/portfolios/<int:pk>/', PortfolioDetails.as_view()),
              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
