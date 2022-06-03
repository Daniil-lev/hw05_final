from django.forms import ModelForm

from .models import Comment, Post


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
