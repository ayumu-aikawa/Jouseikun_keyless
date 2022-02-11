from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm, UserCreationForm, PasswordChangeForm,
    PasswordResetForm, SetPasswordForm
)
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model

from jsk.models import Filemanage

import smtplib
from email.mime.text import MIMEText
from django.template.loader import render_to_string


User = get_user_model()


class LoginForm(AuthenticationForm):
    """ログインフォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'
        #     field.widget.attrs['placeholder'] = field.label  # placeholderにフィールドのラベルを入れる


class UserCreateForm(UserCreationForm):
    """ユーザー登録用フォーム"""

    class Meta:
        model = User
        fields = ('email', 'username')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data['email']
        User.objects.filter(email=email, is_active=False).delete()
        return email

class UserUpdateForm(forms.ModelForm):
    """ユーザー情報更新フォーム"""

    class Meta:
        model = User
        fields = ('email', 'username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

class UserDeleteForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class MyPasswordChangeForm(PasswordChangeForm):
    """パスワード変更フォーム"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

class MyPasswordResetForm(PasswordResetForm):
    """パスワード忘れたときのフォーム"""
    email = forms.EmailField(
        label="メールアドレス",
        max_length=254,
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # for field in self.fields.values():
        #     field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        email = self.cleaned_data["email"]
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('メールアドレスが存在しません！！！')
        return email

    def send_mail(self, subject_template_name, email_template_name, context, from_email, user_email,html_email_template_name=None):
        # SMTP認証情報
        account = ""
        #   password = "meatsaucepasta0ic"
        password = ""

        from_email = "情整君。  メール送信システム<" + account + ">"
        subject = render_to_string(subject_template_name, context)
        message = render_to_string(email_template_name, context)
        # MIMEの作成
        msg = MIMEText(message, "html")
        msg["Subject"] = subject
        msg["To"] = user_email
        msg["From"] = from_email
        
        # メール送信処理
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(account, password)
        server.send_message(msg)
        server.quit()
    

class MySetPasswordForm(UserCreationForm):
    user_data = None

    """パスワード再設定用フォーム(パスワード忘れて再設定)"""
    class Meta:
        model = User
        fields = ('username', )

    # パスワードの再発行をしたいアカウントデータを保持する
    def set_user_id(self, user_data):
        self.user_data = user_data

    # 入力されたusernameとアカウントのusernameが違う場合
    # エラーメッセージを表示させる
    def clean_username(self):
        username = self.cleaned_data['username']
        if self.user_data.username != username:
            raise forms.ValidationError("ニックネームが違います。")
        return username

VALID_EXTENSIONS = ['txt', 'docx']

class FileUploadImageForm(forms.Form):
    file = forms.FileField(
        label='ファイル',
        required=True,
        widget=forms.FileInput(attrs={'accept':'image/*'}))

    def clean_file(self):
        file = self.cleaned_data['file']
        print(self.cleaned_data)
        file_type = file.content_type.split('/')
        if file_type[0] != 'image':
            raise forms.ValidationError('そのファイル形式には対応していません。')
        return file

    def save(self, random_name):
        upload_file = self.cleaned_data['file']
        # 拡張子の指定
        # extension = upload_file.name.split('.')[1]
        # save_name = random_name + '.' + extension
        save_name = random_name + '.png'
        file_name = default_storage.save(save_name, upload_file)
        return default_storage.url(file_name)

class FileUploadTextForm(forms.Form):
    file = forms.FileField(
        label='ファイル',
        required=True,
        widget=forms.FileInput(attrs={'accept':'.txt,.docx'}))

    def clean_file(self):
        file = self.cleaned_data['file']
        # print('aaaaaaaaaaaaaaaaaaaaaaaaa', file.name.rsplit('.', 1))
        file_name = file.name.rsplit('.', 1)
        if len(file_name) == 2:
            if not file_name[1] in VALID_EXTENSIONS:
                raise forms.ValidationError('そのファイル形式には対応していません。')
        else:
            raise forms.ValidationError('そのファイル形式には対応していません。')
        return file

class FileDataUpdateForm(forms.ModelForm):
    class Meta:
        model = Filemanage
        fields = ('file_name',)
        # fields = ('file_name', 'tag_name',)
    file_name = forms.CharField(label='ファイル名', required=True)
    # tag_name = forms.CharField(label='タグ', required=False)

class FileTagUpdateForm(forms.Form):
    user_id = None
    file_id = None

    file_name = forms.CharField(label='ファイル名', required=True)
    tag_name = forms.CharField(label='タグの入力', required=False)

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fields['file_name'].widget.attrs["class"] = "file_name_field"
        self.fields['tag_name'].widget.attrs["class"] = "tag_name_field"

    # バリデーションチェックするために編集中のファイルのIDを取得
    def set_file_id(self, file_id):
        self.file_id = file_id

    # バリデーションチェックするために編集中のアカウントのIDを取得
    def set_user_id(self, user_id):
        self.user_id = user_id

    def clean_file_name(self):
        data = self.cleaned_data["file_name"]
        file_list = Filemanage.objects.filter(user_id=self.user_id, file_name=data)
        # ファイル名の存在チェック
        if file_list.exists():
            # すでに存在しているファイル名の個数が1個の場合
            if file_list.count() == 1:
                # そのデータを取得
                file_data = Filemanage.objects.get(user_id=self.user_id, file_name=data)
                # そのデータと現在編集中のファイルIDが同じ場合
                if file_data.id == self.file_id:
                    return data
            # ファイル名が存在している
            # 複数個の場合している
            # 1個だけ存在していて、idが同じではない場合
            raise forms.ValidationError('そのファイル名はすでに使われています。※大文字小文字は判定しません')
        
        return data

class TextToTagsForm(forms.Form):
    tag_name = forms.CharField(label='タグの入力', required=False)
    
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)

    def clean_tag_name(self):
        data = self.cleaned_data["tag_name"]
        data_list = data.split(',')
        if len(data_list) > 12:
            raise forms.ValidationError('タグの数は12個までです')
        return data

# 検索方法の際の値の保持がわからんすぎたから、form使いたい
# その場合、検索に使う画面すべてに下記のformの記述が必要・・・？
class FileSearchForm(forms.Form):
    search_name = forms.CharField(label='検索', required=False, initial='')
    search = forms.MultipleChoiceField(
          label='検索方法',
          required=False,
          disabled=False,
          initial=['file'],
          choices=[
              ('file', 'ファイル名'),
              ('tag', 'タグ'),
          ],
          widget=forms.RadioSelect(attrs={
               'id': 'search_radio','class': 'form-check-input'}))
