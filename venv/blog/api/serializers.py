from rest_framework import serializers

from main.models import Bd, Comments

class BbSerializer(serializers.ModelSerializer):
    '''Первый сериализатор, который будет формировать список рубрик. В состав сведений будем отправлять
        ключ, описание, цену, и дату создания'''
    class Meta:
        model = Bd
        fields = ('id', 'title', 'content', 'price', 'created_at')



class BbDetailSerializer(serializers.ModelSerializer):
    class Meta:
        '''Сведения о выбранном объявлении.'''
        model = Bd
        fields = ('id', 'title', 'content', 'price', 'created_at', 'contacts', 'image')



class CommentSerializer(serializers.ModelSerializer):
    '''Извлечение списка комментариев и добавление новых комментариев'''
    class Meta:
        model = Comments
        fields = ('id', 'author', 'content', 'created_at')


