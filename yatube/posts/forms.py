from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'Текст замечательного поста'
        )
        self.fields['group'].empty_label = (
            'Может в группу его?'
        )

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': ('Текст поста'),
            'group': ('Группа'),
            'image': ('Изображение'),
        }
        help_texts = {
            'text': ('Введите текст поста'),
            'group': ('Выберите группу'),
            'image': ('Выберите изображение'),
        }


class CommentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['text'].widget.attrs['placeholder'] = (
            'В комментах не гадить, а то закроем бассеин'
        )

    class Meta:
        model = Comment
        fields = ('text', )
