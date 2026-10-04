from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='accueil_fds'),
    path('login/', views.login_view, name='login'),  # Ajoutez cette ligne pour la page de connexion
    # API utilisée par fds/static/fds/script.js
    path('api/register/', views.register_view, name='register'),
    path('api/login/', views.login_api_view, name='login_api'),
    path('api/logout/', views.logout_api_view, name='logout_api'),
    # Vérification par code e-mail (optionnelle, non requise pour s'inscrire)
    path('api/otp/send/', views.otp_send_view, name='otp_send'),
    path('api/otp/verify/', views.otp_verify_view, name='otp_verify'),
    # Établissements de santé conventionnés (liste déroulante du formulaire)
    path('api/etablissements/', views.etablissements_view, name='etablissements'),
    # Assuré : recherche par NNI / INAM puis Feuille de soins PDF
    path('api/assures/verifier/', views.verifier_assure_view, name='verifier_assure'),
    path('api/assures/<str:nni>/photo/', views.assure_photo_view, name='assure_photo'),
    path(
        'api/assures/<str:nni>/feuille-de-soins/',
        views.feuille_de_soins_pdf_view,
        name='feuille_de_soins_pdf',
    ),
]
