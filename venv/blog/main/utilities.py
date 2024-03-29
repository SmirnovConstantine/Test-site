from django.template.loader import render_to_string
from django.core.signing import Signer
from blog.settings import ALLOWED_HOSTS
from datetime import datetime
from os.path import splitext


'''Создаем функцию для отправки электронных писем об активацит'''

signer = Signer()

def send_activation_notification(user):
    if ALLOWED_HOSTS:
        host = 'http://' + ALLOWED_HOSTS[0]
    else:
        host = 'http://127.0.0.1:8000'
    context = {'user': user, 'host': host,
               'sign': signer.sign(user.username)}
    subject = render_to_string('email/activation_letter_subject.txt', context)
    body_text = render_to_string('email/activation_letter_body.txt', context)
    user.email_user(subject, body_text)


def get_timestamp_path(istance, filename):

    ''' Генерирует имена для сохраняемых в модели выгруженных файлов'''

    return '%s%s' % (datetime.now().timestamp(), splitext(filename)[1])