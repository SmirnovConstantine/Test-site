from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import UpdateView, CreateView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.views.generic.base import TemplateView
from django.core.signing import BadSignature
from django.views.generic.edit import DeleteView
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import  Paginator
from django.db.models import Q
from django.shortcuts import redirect


from .models import AdvUser, SubRubric, Bd, Comments
from .forms import ChangeUserInfoForm, RegisterUserForm, SearchForm, BdForm, AIFormSet, UserCommentForm, GuestCommentForm
from .utilities import signer

def index(request):
    bbs = Bd.objects.filter(is_active=True)[:10]
    context = {'bbs': bbs}
    return render(request, 'layout/index.html', context)


def other_page(request, page):

    '''Реализация контроллера-функции other page
    Здесь мы получаем имя выводимой страницы из параметра page, добавлем к нему путь и ищем
    полный путь к шаблону и загружаем его. Если загрузка выполнилась, формируем на основе этого шаблона
    страницу, иначе get_template() возбудит исключение, TemplateDoesNOtExist, Мы его перехватываем и возбуждаем
    новое исключение Http404, которое приведет к отправке страницы с собщение об ошибке 404(страница не существует)'''

    try:
        template = get_template('main/' + page + '.html')
    except TemplateDoesNotExist:
        raise Http404
    return HttpResponse(template.render(request=request))


class BBLoginView(LoginView):
    '''Реализация входа на сайт.'''
    template_name = 'main/login.html'


class BBLogoutView(LoginRequiredMixin, LoginView):
    template_name = 'main/logout.html'


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):

    '''В процессе работы контроллера извелекается запись текущего пользователя.'''

    model = AdvUser
    template_name = 'main/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('main:profile')
    success_message = 'Личные данные пользователя изменеы'

    def dispatch(self, request, *args, **kwargs):

        '''Для чего сначала мы получаем уникальный ключ из метода dispatch() который выполняется
    всегда первым и наследуется всеми контроллер-классами. В переопределенном методе мы
    звлекаем ключ и сохраняем его в атрибуте user_id.'''

        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):

        '''Здесь происходит звлечение записи.'''

        if  not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BBPasswordChangeView(SuccessMessageMixin, LoginRequiredMixin, PasswordChangeView):

    '''Контролер изменения пароля.'''

    template_name = 'main/password_change.html'
    success_url = reverse_lazy('main:profile')
    success_message = 'Пароль успешно изменен'


class RegisterUserView(CreateView):
    '''Реистрирует пользлвателя и инициирует отправку письма об активации'''
    model = AdvUser
    template_name = 'main/register.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('main:register_done')

class RegisterDoneView(TemplateView):
    '''Сообщение об успешной активации'''
    template_name = 'main/register_done.html'


def user_activate(request, sign):

    '''Функция-контроллер, для активации пользователя. Подписанный индентификатор который приходт
    в составе интернет-адреса, мы получаем с прамтром signю. Дфлее мы извлекаем из него пользователя
    ,и ищем пользлователя с этим именем. Далее выполняем проверку, активирован ли пользователь'''

    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'main/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template('main/user_is_activated.html')
    else:
        template = 'main/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


class DeleteUserView(LoginRequiredMixin, DeleteView):

    '''Удаление пользователя'''

    model = AdvUser
    template_name = 'main/delete_user.html'
    success_url = reverse_lazy('main:index')

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.add_message(request, messages.SUCCESS, 'Пользователь удален')
        return super().post(request, *args, **kwargs)


    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)

def by_rubric(request, pk):
    '''Извлекаем выбранную поситителем рубрику. Затем извелекаем объявления, относящиеся к этой рубрике
        и помеченные для вывода. После чего выполняем фильтрацию уже отобранных записей, по ведденому слову'''

    rubric = get_object_or_404(SubRubric, pk=pk)
    bbs = Bd.objects.filter(is_active=True, rubric=pk)
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        q = Q(title__icontains=keyword)|Q(content__icontains=keyword)
        bbs = bbs.filter(q)
    else:
        keyword = ''
    form = SearchForm(initial={'keyword': keyword})
    paginator = Paginator(bbs, 2)
    if 'page' in request.GET:
        page_num = request.GET['page']
    else:
        page_num = 1
    page = paginator.get_page(page_num)
    context = {'rubric': rubric, 'page': page, 'bbs': page.object_list, 'form':form}
    return render(request, 'main/by_rubric.html', context)


def detail(request, rubric_pk, pk):
    '''Вывод объявлений'''
    bb = Bd.objects.get(pk=pk)
    ais = bb.additionalimage_set.all()
    comments = Comments.objects.filter(bb=pk, is_active=True)
    initial = {'bb': bb.pk}
    if request.user.is_authenticated:
        initial['author'] = request.user.username
        form_class = UserCommentForm
    else:
        form_class = GuestCommentForm
    form = form_class(initial=initial)
    if request.method == 'POST':
        c_form = form_class(request.POST)
        if c_form.is_valid():
            c_form.save()
            messages.add_message(request, messages.SUCCESS, 'Комментарий добавлен')
        else:
            form = c_form
            messages.add_message(request, messages.WARNING, 'Комментарий не добавлен')
    context = {'bb': bb, 'ais': ais, 'comments': comments, 'form': form}
    return render(request, 'main/detail.html', context)



'''Ниже написан контроллер, который выводит страницу поьзовательского профиля. Т.к
страница профиля должна быть доступна только зареганым пользователям, успешн выполнившим вход на сайт, 
мы пометили котроллер-функцию декоратором @login_required'''
@login_required
def profile(request):
    bbs = Bd.objects.filter(author=request.user.pk)
    context = {'bbs': bbs}
    return render(request, 'main/profile.html', context)


def profile_bb_detail(request, pk):
    '''Вывод объявлений для зарегестрированных пользователей'''
    bb = get_object_or_404(Bd, pk=pk)
    ais = bb.additionalimage_set.all()
    bbs = Bd.objects.filter(pk=pk)
    context = {'bb': bb,  'ais':ais, 'bbs':bbs}
    return render(request, 'main/profile_bb_detail.html', context)

@login_required
def profile_bb_add(request):
    '''Добавление формы'''
    if request.method == 'POST':
        form = BdForm(request.POST, request.FILES)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if form.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS, 'Объявление добавлено')
            return redirect('main:profile')
    else:
        form = BdForm(initial={'author': request.user.pk})
        formset = AIFormSet()
    context = {'form': form, 'formset': formset}
    return render(request, 'main/profile_bb_add.html', context)




@login_required
def profile_bb_change(request, pk):
    '''Изменение объявления'''
    bb = get_object_or_404(Bd, pk=pk)
    if request.method == 'POST':
        form = BdForm(request.POST, request.FILES, instance=bb)
        if form.is_valid():
            bb = form.save()
            formset = AIFormSet(request.POST, request.FILES, instance=bb)
            if formset.is_valid():
                formset.save()
                messages.add_message(request, messages.SUCCESS, 'Объявление изменено')
                return redirect('main:profile')
    else:
        form = BdForm(instance=bb)
        formset = AIFormSet(instance=bb)
        context = {'form': form, 'formset': formset}
        return render(request, 'main/profile_bb_change.html', context)



@login_required
def profile_bb_delete(request, pk):
    '''Удаление объявления'''
    bb = get_object_or_404(Bd, pk=pk)
    if request.method == 'POST':
        bb.delete()
        messages.add_message(request, messages.SUCCESS, 'Объявление удалено')
        return redirect('main:profile')
    else:
        context = {'bb': bb}
        return render(request, 'main/profile_bb_delete.html', context)