import base64

from django.contrib import admin
from django.utils.html import format_html

from .models import Assure, Etablissement, EmailVerificationCode


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    """Consultation des codes envoyés (création/suppression désactivées)."""

    list_display = ('email', 'code', 'attempts', 'created_at', 'expires_at', 'consumed_at')
    list_filter = ('created_at',)
    search_fields = ('email',)
    readonly_fields = ('email', 'code', 'attempts', 'created_at', 'expires_at', 'consumed_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Assure)
class AssureAdmin(admin.ModelAdmin):
    """Consultation des assurés (les données proviennent de PostgreSQL)."""

    list_display = ('nni', 'inam', 'nom', 'prenom', 'date_naissance', 'age', 'a_photo')
    list_filter = ('sexe',)
    search_fields = ('nni', 'inam', 'nom', 'prenom', 'numero_carte')
    readonly_fields = ('apercu_photo', 'age')
    fieldsets = (
        ("Identification", {'fields': ('nni', 'inam', 'numero_carte', 'numero_feuille')}),
        (
            "État civil",
            {'fields': ('nom', 'prenom', 'nom_ar', 'prenom_ar', 'sexe', 'date_naissance',
                        'age', 'lieu_naissance', 'telephone')},
        ),
        ("Établissement", {'fields': ('centre_hospitalier',)}),
        ("Photo de profil", {'fields': ('apercu_photo', 'photo', 'photo_type', 'photo_nom',
                                        'photo_path')}),
        ("Code scanné / QR", {'fields': ('code_qr',)}),
    )

    @admin.display(description="Âge")
    def age(self, obj):
        return obj.age if obj.age is not None else '-'

    @admin.display(boolean=True, description="Photo")
    def a_photo(self, obj):
        return obj.photo_binaire() is not None

    @admin.display(description="Aperçu de la photo")
    def apercu_photo(self, obj):
        octets = obj.photo_binaire()
        if not octets:
            return "Aucune photo enregistrée pour cet assuré."
        type_mime = obj.photo_type or 'image/jpeg'
        donnees = base64.b64encode(octets).decode('ascii')
        return format_html(
            '<img src="data:{};base64,{}" style="max-height:180px;'
            'border:1px solid #ccd;border-radius:6px;" alt="Photo de l\'assuré">',
            type_mime,
            donnees,
        )


@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    """Établissements de santé proposés dans la liste déroulante du formulaire."""

    list_display = ('nom', 'type_etablissement', 'ville', 'telephone', 'conventionne')
    list_filter = ('type_etablissement', 'conventionne', 'ville')
    list_editable = ('conventionne',)
    search_fields = ('nom', 'ville', 'adresse')
    ordering = ('nom', 'ville')


