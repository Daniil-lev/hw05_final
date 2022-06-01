from django.forms import ModelForm

from .models import Comment, Follow, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        labels = {'text': 'Текст поста', 'group': 'Группа'}
        help_texts = {'group': 'Выберите группу', 'text': 'Введите ссообщение'}
        fields = ('text', 'group', 'image')


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        labels = {'text': 'Добавить комментарий'}
        help_texts = {'text': 'Текст комментария'}
        fields = ('text',)


class FollowForm(ModelForm):
    class Meta:
        model = Follow
        labels = {'user': 'Подписка на:', 'author': 'Автор записи'}
        fields = ('user',)
