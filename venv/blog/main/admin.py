from django.contrib import admin
import datetime

from .models import AdvUser, SuperRubric, SubRubric, Bd, AdditionalImage, Comments
from .utilities import send_activation_notification
from .forms import SubRubricForm

def send_activation_notifications(modeladmin, request, queryset):
    for rec in queryset:
        if not rec.is_activated:
            send_activation_notification(rec)
        modeladmin.message_user(request, 'Письма с оповощениями отправлены')
    send_activation_notifications.short_description = 'Отправка писем с оповещением об активации'

class NonactivatedFilter(admin.SimpleListFilter):
    title = 'Прошли активацию?'
    parameter_name = 'activate'

    def lookups(self, request, model_admin):
        return (
            ('activated', 'Прошли'),
            ('threedays', 'Не прошли более 3 дней'),
            ('week', 'Не прошли более недели'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'activated':
            return queryset.filter(is_activate=True, is_activated=True)
        elif val == 'threedays':
            d = datetime.date.today() - datetime.timedelta(days=3)
            return queryset.filter(is_activate=False, is_activated=False, date_joined__date__lt=d)
        elif val == 'week':
            d = datetime.date.today() - datetime.timedelta(weeks=1)
            return queryset.filter(is_activate=False, is_activated=False, date_joined__date__lt=d)


class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_activated', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (NonactivatedFilter,)
    fields = (  ('username', 'email'),('first_name', 'last_name'),
                ('send_messages', 'is_active' ,'is_activated'),
                ('is_staff', 'is_superuser'),
                'groups', 'user_permissions',
                ('last_login', 'date_joined'))
    readonly_fields = ('last_login', 'date_joined')
    actions = (send_activation_notifications,)

admin.site.register(AdvUser, AdvUserAdmin)



class SubRubricInline(admin.TabularInline):
    model = SubRubric

class SuperRubricAdmin(admin.ModelAdmin):
    exclude = ('super_rubric', )
    inlines = (SubRubricInline, )

admin.site.register(SuperRubric, SuperRubricAdmin)


class SubRubricAdmin(admin.ModelAdmin):
    form = SubRubricForm

admin.site.register(SubRubric, SubRubricAdmin)



class AdditionalImageInline(admin.TabularInline):
    model = AdditionalImage

class BdAdmin(admin.ModelAdmin):
    list_display = ('rubric', 'title', 'content', 'author', 'created_at')
    fields = (('rubric', 'author'), 'title', 'content', 'price', 'contacts', 'image', 'is_active')
    inlines = (AdditionalImageInline,)

admin.site.register(Bd, BdAdmin)


admin.site.register(Comments)