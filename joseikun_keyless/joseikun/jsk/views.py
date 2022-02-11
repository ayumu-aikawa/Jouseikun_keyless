from lib2to3.pgen2 import token
import smtplib, docx, re, datetime, uuid
import urllib.parse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.core.files import File
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponseBadRequest, FileResponse ,Http404 , HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, resolve_url, render
from django.template.loader import render_to_string
from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse_lazy
from django.views import generic
from jmespath import search
from matplotlib.pyplot import close
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm, MyPasswordChangeForm,
    MyPasswordResetForm, MySetPasswordForm, FileUploadTextForm,
    FileDataUpdateForm, FileTagUpdateForm, FileUploadImageForm,
    UserDeleteForm, TextToTagsForm, FileSearchForm
)
from .models import User , Filemanage
from django.db.models import Q
from email.mime.text import MIMEText
import json
from PIL import Image
from secrets import token_urlsafe

# Google-Cloud関係で必要な物
import io
import os
from google.cloud import vision
from google.oauth2 import service_account
import boto3

#Google-Cloudのクライアント作成
credential_path = './gcp_key/norse-ego-279800-dbca388726fe.json'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
# Instantiates a client
client = vision.ImageAnnotatorClient()

User = get_user_model()
# from django.contrib.auth.models import User これはあまりうまくない

#環境変数
FILE_PATH = ".\\download\\"
LANGUAGE_DICT = {
    'ja': '日本語',
    'en': '英語',
    'es': 'スペイン語',
    'it': 'イタリア語',
    'fr': 'フランス語',
    'pt': 'ポルトガル語',
    'de': 'ドイツ語'}

# Access key ID
ACCESS_KEY_ID = ''
# Secret access key
SECRET_ACCESS_KEY = ''
# Region name
REGION_NAME = 'ap-northeast-1'
S3_FILE_UPLOAD = ''
S3_FILE_DOWNLOAD = ''
S3_FILE_TAGS = ''
S3_FILE_PIC = ''

# メール送信
#メール送信関数
def mail_send(to_email,subject,message):
  # SMTP認証情報
#   account = "jyouseikun@gmail.com"
#   password = "bexgkklkixezgdcr"
  account = ""
  password = ""

  from_email = "情整君。  メール送信システム<" + account + ">"
  
  # MIMEの作成
  msg = MIMEText(message, "html")
  msg["Subject"] = subject
  msg["To"] = to_email
  msg["From"] = from_email
  
  # メール送信処理
  server = smtplib.SMTP("smtp.gmail.com", 587)
  server.starttls()
  server.login(account, password)
  server.send_message(msg)
  server.quit()


class Top(generic.TemplateView):
    template_name = 'jsk/top.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': '情整君。へようこそ', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)

class Login(LoginView):
    """ログイン画面"""
    form_class = LoginForm
    template_name = 'jsk/login.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ログイン', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)



class Logout(LogoutView):
    """ログアウト画面"""
    template_name = 'jsk/top.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': '情整君。へようこそ', 'template_name': template_name}

class UserDataInput(generic.FormView):
    """ユーザー情報の入力

    このビューが呼ばれるのは、以下の2箇所です。
    ・初回の入力欄表示(aタグでの遷移)
    ・確認画面から戻るを押した場合(これはPOSTで飛んできます)

    初回の入力欄表示の際は、空のフォームをuser_create_input.htmlに渡し、
    戻る場合は、POSTで飛んできたフォームデータをそのままuser_create_input.htmlに渡します。

    """
    template_name = 'jsk/user_create_input.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'アカウント登録', 'template_name': template_name}
    form_class = UserCreateForm

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        return render(self.request, 'jsk/user_create_input.html', {'form': form})

class UserDataConfirm(generic.FormView):
    """ユーザー情報の確認

    ユーザー情報入力後、「送信」を押すとこのビューが呼ばれます。(user_create_input.htmlのform action属性がこのビュー)
    データが問題なければuser_create_confirm.html(確認画面)を、入力内容に不備があればuser_create_input.html(入力画面)に
    フォームデータを渡します。

    """
    form_class = UserCreateForm
    # extra_context = {
        # 'search_form': FileSearchForm(),
    # 'title': 'ユーザー情報の確認', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        context = {
            'title': 'アカウント入力画面',
            'form': form,
            'pass1': '●●●●●●●●',
            'pass2': '●●●●●●●●',
        }
        return render(self.request, 'jsk/user_create_confirm.html', context)

    def form_invalid(self, form):
        return render(self.request, 'jsk/user_create_input.html', {'form': form})

class UserCreateDone(generic.CreateView):
    """ユーザー仮登録"""
    template_name = 'jsk/user_create_done.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'アカウント仮登録', 'template_name': template_name}
    form_class = UserCreateForm

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)

    def form_invalid(self, form):
        return render(self.request, 'jsk/user_confirm_error.html', {'name': '南部隼希'})

    def form_valid(self, form):
        """仮登録と本登録用メールの発行."""
        # 仮登録と本登録の切り替えは、is_active属性を使うと簡単です。
        # 退会処理も、is_activeをFalseにするだけにしておくと捗ります。
        user = form.save(commit=False)
        user.is_active = True
        user.save()

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk),
            'user': user,
        }
        # メール送信
        to_mail = self.request.POST['email']
        subject = render_to_string('jsk/mail_template/create/subject.txt', context)
        message = render_to_string('jsk/mail_template/create/message.txt', context)

        # user.email_user(subject, message)
        # メール送信
        mail_send(to_mail, subject, message)
        return redirect('jsk:user_create_done')

class UserCreateComplete(generic.TemplateView):
    """メール内URLアクセス後のユーザー本登録"""
    template_name = 'jsk/user_create_complete.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'アカウント本登録', 'template_name': template_name}
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24*365)  # デフォルトでは1年以内

    def get(self, request, **kwargs):
        """tokenが正しければ本登録."""
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                # if not user.is_active:
                #     # 問題なければ本登録とする
                #     user.is_active = True
                if user.is_regist == False:
                    # 問題なければ本登録とする
                    user.is_regist = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()

class OnlyYouMixin(UserPassesTestMixin):
    # 条件を満たさない場合に403画面に移動させるかどうかのフラグです。
    #   ログインしているユーザーでないと見れないページである場合に使用する
    # Falseなら、ログイン画面に移動させます。 
    raise_exception = False
    # extra_context = {
        # 'search_form': FileSearchForm(),
    # 'title': 'LOGIN', 'template_name': template_name}

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        user = self.request.user
        return user.pk == self.kwargs['pk'] or user.is_superuser


class UserDetail(OnlyYouMixin, generic.DetailView):
    model = User
    template_name = 'jsk/user_detail.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ユーザー基本情報', 'template_name': template_name}


class UserUpdate(OnlyYouMixin, generic.UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'jsk/user_update_input.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'アカウント編集', 'template_name': template_name}

    def get_success_url(self):
        return resolve_url('jsk:user_detail', pk=self.kwargs['pk'])

class UserDelete(OnlyYouMixin, generic.TemplateView):
    template_name = 'jsk/user_delete_confirm.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'アカウント削除', 'template_name': template_name}

    def post(self, request, *args, **kwargs):
        # user = User.objects.get(email=self.request.user.email)
        user = User.objects.get(id=self.request.user.id)
        if user.username == self.request.POST.get('username'):
            user.is_active = False
            user.save()
            # 関連しているファイルも削除する
            # ファイルデータの取得
            file_data = Filemanage.objects.filter(user_id=user.id)
            # S3のファイルを削除
            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)
            for file in file_data:
                file_key = file.file_name + '.' + file.file_extension
                s3.delete_object(Bucket=S3_FILE_DOWNLOAD, Key=file_key)
                s3.delete_object(Bucket=S3_FILE_TAGS,Key=file_key + '.json')
            # DBのファイルデータを削除（物理）
            file_data.delete()
            # auth_logout(self.request)
            return redirect('jsk:logout')
        else:
            messages.error(self.request, '※ニックネームが違います。')

            return redirect('jsk:user_delete', self.request.user.id)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = UserDeleteForm(self.request.POST or None)
        context["form"] = form
        return context

class PasswordChange(PasswordChangeView):
    """パスワード変更ビュー"""
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('jsk:password_change_done')
    template_name = 'jsk/password_change.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'パスワードリセット', 'template_name': template_name}


class PasswordChangeDone(PasswordChangeDoneView):
    """パスワード変更しました"""
    template_name = 'jsk/password_change_done.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'パスワードリセット完了', 'template_name': template_name}


class PasswordReset(PasswordResetView):
    """パスワード変更用URLの送付画面"""
    subject_template_name = 'jsk/mail_template/password_reset/subject.txt'
    email_template_name = 'jsk/mail_template/password_reset/message.txt'
    template_name = 'jsk/password_reset_form.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'パスワード再発行', 'template_name': template_name}
    form_class = MyPasswordResetForm
    success_url = reverse_lazy('jsk:password_reset_done')

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        # 入力されたメアドを取得し、存在チェックをする
        user_email = form.cleaned_data.get('email')
        exist_user = User.objects.filter(email=user_email).exists()
        # あった場合
        if exist_user:
            # データの取得
            email_user = User.objects.get(email=user_email)
            # トークンを取得しDBへ保存
            email_user.token2 = self.token_generator.make_token(email_user)
            email_user.save()

            # current_site = get_current_site(self.request)
            # domain = current_site.domain
            # context = {
            #     'protocol': self.request.scheme,
            #     'domain': domain,
            #     'token': dumps(email_user.pk),
            #     'user': email_user,
            # }
            # メール送信
            # to_mail = self.request.POST['email']
            # subject = render_to_string('jsk/mail_template/create/subject.txt', context)
            # message = render_to_string('jsk/mail_template/create/message.txt', context)
            # mail_send(to_mail, subject, message)
            return super().form_valid(form)
        else:
            return super().form_invalid(form)


class PasswordResetDone(PasswordResetDoneView):
    """パスワード変更用URLを送りました画面"""
    template_name = 'jsk/password_reset_done.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'パスワード再発行・再発行用のメールの送信が完了しました', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)


class PasswordResetConfirm(generic.FormView):
    """新パスワード入力画面"""
    form_class = MySetPasswordForm
    success_url = reverse_lazy('jsk:password_reset_complete')
    template_name = 'jsk/password_reset_confirm.html'
    extra_context = {
        'search_form': FileSearchForm(),
        
        'title': 'パスワード再入力',
        'template_name': template_name,
        }

    def get(self, request, *args, **kwargs):
        # トークンがDBに存在しない場合トップ画面へ遷移する
        if not User.objects.filter(token2=kwargs['token']).exists():
            return redirect('jsk:error_view')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # print(request.POST.get('username'))
        # print(kwargs['token'])
        # トークンの値からユーザーデータを取得
        try:
            token_data = User.objects.get(token2=kwargs['token'])
        except:
            return render(request, 'jsk/user_password_error.html', self.extra_context)
        # 入力された値を取得
        form = MySetPasswordForm(request.POST)
        # パスワードの再発行をしたいアカウントデータをformに送る
        form.set_user_id(token_data)
        if form.is_valid():
        # 入力されたニックネームとユーザーのニックネームが合致するかどうか
        # if token_data.username == request.POST.get('username'):
            # 新パスワードを取得
            password = request.POST.get('password1')
            # ここでなぜかもう一度ユーザーデータを取得
            token_user = User.objects.get(token2=kwargs['token'])
            # 新パスワードを登録
            token_user.set_password(password)
            # トークンの値を空にする
            token_user.token2 = None
            # DB更新
            token_user.save()
            # 新パスワード登録完了画面へ遷移
            return redirect('jsk:password_reset_complete')
        else:
            return self.form_invalid(form)

class PasswordResetComplete(PasswordResetCompleteView):
    """新パスワード設定しました画面"""
    template_name = 'jsk/password_reset_complete.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'パスワード再発行が完了しました', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.id:
            # ログインボタンを押下した後、top画面へ遷移するところを
            # ファイル検索画面へ遷移させました
            return redirect('jsk:file_search')
        return super().get(request, *args, **kwargs)



class FileUploadImage(LoginRequiredMixin, generic.FormView):
    '''ファイルのアップロードをしてストレージに保存・DBに登録'''
    form_class = FileUploadImageForm
    template_name = 'jsk/file_upload_image.html'
    extra_context = {
        'search_form': FileSearchForm(),
        
        'title': '画像ファイルの選択',
        'template_name': template_name}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['after_code'] = list(LANGUAGE_DICT.keys())
        context['after_name'] = list(LANGUAGE_DICT.values())
        context['before_code'] = ['auto'] + context['after_code'].copy()
        context['before_name'] = ['自動'] + context['after_name'].copy()
        return context

    # ファイルに問題がなかったら、ファイル保存用の関数を作成して実行
    def form_valid(self, form):
        # ここにファイルの保存関数を作成する
        img_file = self.request.FILES['file']
        # S3にファイルを保存する処理を作成する
        img_file_name = img_file.name.rsplit('.', 1)
        file_name = [img_file_name[0], 'txt']
        random_name = str(uuid.uuid4())
        new_path = FILE_PATH + random_name
        # 画像保存
        f_img = open(new_path + ".png",'wb+')
        for chunk in img_file.chunks():
            f_img.write(chunk)
        f_img.close()

        #Google-Cloud-Visionに投げる
        
        # The name of the image file to annotate
        # file_name = os.path.abspath('')
        image_name = new_path + ".png"

        # Loads the image into memory
        with io.open(image_name, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Performs label detection on the image file
        response =  client.document_text_detection(
                image=image,
                image_context={'language_hints': ['ja']}
            )

        # レスポンスからテキストデータを抽出
        output_text = ''
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        output_text += ''.join([
                            symbol.text for symbol in word.symbols
                        ])
                    output_text += '\n'

        get_rekognition_text = output_text

        # txtファイルを一度作成して、必要な文字列を書き込む
        with open('./text_template/{}.txt'.format(random_name), 'w', encoding='utf-8') as txt:
            txt.write('{}'.format(get_rekognition_text))

        # 読み込みモードでひらき、s3へ保存
        if 'translate' in self.request.POST.keys():
            # 翻訳する場合は、ここで処理
            # 翻訳前言語の取得
            before_lang = self.request.POST['before_langage']
            # 翻訳後言語の取得
            after_lang = self.request.POST['after_langage']
            input_key = f'{before_lang}_{after_lang}_' + random_name
            input_key = input_key + '.' + file_name[1]

            new_path = FILE_PATH + input_key

            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)

            response = s3.upload_file('./text_template/{}.txt'.format(random_name), S3_FILE_UPLOAD, input_key)

            # 作成したファイルを削除
            os.remove('./text_template/{}.txt'.format(random_name))

        else:
            # 翻訳しないそのままの文書ファイルをoutputにアップロード
            file_data = self.request.FILES['file']
            #input_key = 'none_none_' + random_name
            new_path = FILE_PATH + random_name

            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)

            response = s3.upload_file('./text_template/{}.txt'.format(random_name), S3_FILE_DOWNLOAD, random_name + '.' + file_name[1])

            #ファイル削除
            os.remove('./text_template/{}.txt'.format(random_name))

        '''new_path = FILE_PATH + random_name
        s3_file = FILE_PATH + input_key

        with open('./text_template/{}.txt'.format(random_name), 'r', encoding='utf-8') as txt:
            file_data = File(txt, 'test.txt')

            f = open(s3_file,'wb+')
            for chunk in file_data.chunks():
                f.write(chunk.encode())
            f.close()

        # s3へ保存
        s3 = boto3.client('s3',
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY,
            region_name=REGION_NAME)

        s3_response = s3.upload_file(s3_file, S3_FILE_UPLOAD, input_key)

        # 作成したtxtファイルを削除
        print('ファイル削除')
        os.remove(new_path+'.png')
        os.remove('./text_template/{}.txt'.format(random_name))
        os.remove(s3_file)'''


        #画像アップロード後削除
        response = s3.upload_file(image_name, S3_FILE_PIC, random_name)
        os.remove(image_name)

        # 複数個保存防止のため、個数+1を最後につける
        file_name_filter = Filemanage.objects.filter(user_id=self.request.user.id, file_name=file_name[0])

        if file_name_filter.exists():
            count_file_name = file_name[0]
            file_name_num = 1
            while(True):
                file_name_num += 1
                count_file_name =  file_name[0] + '({})'.format(str(file_name_num))
                if Filemanage.objects.filter(user_id=self.request.user.id, file_name=count_file_name).exists() == False:
                    file_name[0] = count_file_name
                    break

        # create = '成功したら絶対にエラーを吐くので処理作成時に上書きしてください'
        # ここにDBへファイルの関連データを保存する
        create = Filemanage.objects.create(
            user_id = self.request.user.id,
            file_name = file_name[0],
            file_extension = file_name[1],
            s3_file_name = random_name,
            tag_name = '',
            update_dt = datetime.datetime.now(),
            last_viewed_dt = datetime.datetime.now(),
            pic_flag = True)

        user_data = User.objects.get(id=self.request.user.id)
        while True:
            token_url = token_urlsafe(16)
            if not User.objects.filter(token=token_url).exists():
                break
        user_data.token = token_url
        user_data.save()

        # return render(self.request, 'jsk/file_upload_done.html', context)
        return redirect('jsk:file_upload_done', user_pk=self.request.user.id, pk=create.id, token=token_url)


class FileUploadText(LoginRequiredMixin, generic.FormView):
    '''ファイルのアップロードをしてストレージに保存・DBに登録'''
    form_class = FileUploadTextForm
    template_name = 'jsk/file_upload_text.html'
    extra_context = {
        'search_form': FileSearchForm(),
        
        'title': '文書ファイルの選択',
        'template_name': template_name}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['after_code'] = list(LANGUAGE_DICT.keys())
        context['after_name'] = list(LANGUAGE_DICT.values())
        context['before_code'] = ['auto'] + context['after_code'].copy()
        context['before_name'] = ['自動'] + context['after_name'].copy()
        return context

    # ファイルに問題がなかったら、ファイル保存用の関数を作成して実行
    def form_valid(self, form):
        random_name = str(uuid.uuid4())
        file_name = self.request.FILES['file'].name.rsplit('.', 1)
        # ここにファイルの保存関数を作成する
        # S3にファイルを保存する処理を作成する
        if 'translate' in self.request.POST.keys():
            # 翻訳する場合は、ここで処理
            # 翻訳前言語の取得
            before_lang = self.request.POST['before_langage']
            # 翻訳後言語の取得
            after_lang = self.request.POST['after_langage']
            # ファイルの取得
            file_data = self.request.FILES['file']

            input_key = f'{before_lang}_{after_lang}_' + random_name
            input_key = input_key + '.' + file_name[1]

            new_path = FILE_PATH + input_key
    
            if self.request.method == 'POST':
                f = open(new_path,'wb+')
            for chunk in file_data.chunks():
                f.write(chunk)
            f.close()


            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)

            response = s3.upload_file(new_path, S3_FILE_UPLOAD, input_key)

            # 作成したファイルを削除
            os.remove(new_path)


        else:
            # 翻訳しないそのままの文書ファイルをoutputにアップロード
            file_data = self.request.FILES['file']
            #input_key = 'none_none_' + random_name
            new_path = FILE_PATH + random_name
    
            if self.request.method == 'POST':
                f = open(new_path,'wb+')
            for chunk in file_data.chunks():
                f.write(chunk)
            f.close()


            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)
            #new_path = FILE_PATH + input_key
    
            if self.request.method == 'POST':
                f = open(new_path,'wb+')
            for chunk in file_data.chunks():
                f.write(chunk)
            f.close()


            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)

            response = s3.upload_file(new_path, S3_FILE_DOWNLOAD, random_name + '.' + file_name[1])


            # 作成したファイルを削除
            os.remove(FILE_PATH + random_name)

        # 複数個保存防止のため、個数+1を最後につける
        file_name_filter = Filemanage.objects.filter(user_id=self.request.user.id, file_name=file_name[0])

        if file_name_filter.exists():
            count_file_name = file_name[0]
            file_name_num = 1
            while(True):
                file_name_num += 1
                count_file_name =  file_name[0] + '({})'.format(str(file_name_num))
                if Filemanage.objects.filter(user_id=self.request.user.id, file_name=count_file_name).exists() == False:
                    file_name[0] = count_file_name
                    break

        # ここにDBへファイルの関連データを保存する
        create = Filemanage.objects.create(
            user_id = self.request.user.id,
            file_name = file_name[0],
            file_extension = file_name[1],
            s3_file_name = random_name,
            tag_name = '',
            update_dt = datetime.datetime.now(),
            last_viewed_dt = datetime.datetime.now(),
            pic_flag = False)

        user_data = User.objects.get(id=self.request.user.id)
        while True:
            token_url = token_urlsafe(16)
            if not User.objects.filter(token=token_url).exists():
                break
        user_data.token = token_url
        user_data.save()

        # return render(self.request, 'jsk/file_upload_done.html', context)
        return redirect('jsk:file_upload_done', user_pk=self.request.user.id, pk=create.id, token=token_url)


class FileUploadDone(OnlyYouMixin, generic.TemplateView):
    template_name = 'jsk/file_upload_done.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ファイルアップロード完了', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        # 現在のユーザーのデータを取得
        token_user = User.objects.get(id=kwargs['user_pk'])
        # 取得したtokenであっているかチェック
        if token_user.token == kwargs['token']:
            token_user.token = None
            token_user.save()
        else:
            return redirect('jsk:error_view')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file'] = Filemanage.objects.get(id=kwargs['pk'])
        context['user_pk'] = kwargs['user_pk']
        return context

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser


class FileTextUpdate(OnlyYouMixin, generic.UpdateView):
    '''DBに保存されているファイルのデータを編集'''
    model = Filemanage
    form_class = FileDataUpdateForm
    template_name = 'jsk/file_update_text.html'
    # success_url = reverse_lazy('jsk:file_search')
    extra_context = {
        'search_form': FileSearchForm(),
        'title': '文書ファイルの編集', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        # 拡張子を表示させる（基本 .docx だと思うけど…）
        self.extra_context['file_extension'] = Filemanage.objects.get(pk=kwargs['pk']).file_extension
        return super().get(request, *args, **kwargs)

    def get_success_url(self) -> str:
        return reverse_lazy('jsk:file_update_done', user_pk=self.request.user.id, pk=self.kwargs['pk'])

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser

    def form_valid(self, form):
        # 更新日時を追加
        self.object.last_viewed_dt = datetime.datetime.now()
        self.object.save()
        return super().form_valid(form)


class FileUpdateDone(OnlyYouMixin, generic.TemplateView):
    template_name = 'jsk/file_update_done.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'タグ編集完了', 'template_name': template_name}

    def get(self, request, *args, **kwargs):
        # 現在のユーザーのデータを取得
        token_user = User.objects.get(id=kwargs['user_pk'])
        # 取得したtokenであっているかチェック
        if token_user.token == kwargs['token']:
            token_user.token = None
            token_user.save()
        else:
            return redirect('jsk:error_view')
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['file'] = Filemanage.objects.get(id=kwargs['pk'])
        context['user_pk'] = kwargs['user_pk']
        return context

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser


class FileSearch(LoginRequiredMixin, generic.ListView):
    """ファイルの検索画面"""
    template_name = 'jsk/file_search.html'
    model = Filemanage
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ファイル検索結果・一覧',
        'template_name': template_name,
        'user_id': None
        }
    # テンプレートで扱うモデルのオブジェクト名
    context_object_name = 'file_list'
    # 一度に表示する件数
    paginate_by =   5

    def get(self, request, *args, **kwargs):
        if not self.request.GET == {}:
            if not 'search_name' in self.request.GET or not 'search' in self.request.GET:
                return redirect('jsk:error_view')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        # 検索語
        q_word = self.request.GET.get('search_name')
        q_method = self.request.GET.get('search')
        user_num = self.request.user.id
        # 検索方法
        sort_column = '-last_viewed_dt'
        object_list = Filemanage.objects.filter(user_id=user_num).order_by(sort_column)
        if q_word:
            q_word_list = re.split('[ 　]',q_word)
            # ファイル検索
            if q_method == 'file':
                for q in q_word_list:
                    object_list = object_list.filter(file_name__icontains=q)
            # タグ検索
            elif q_method == 'tag':
                # q_word += ';'
                for q in q_word_list:
                    object_list = object_list.filter(tag_name__icontains=q)

        # 表示する用のタグリストを用意
        for object in object_list:
            object.tag_name = object.tag_name.split(';')
            # データが空の場合は要素を消す
            if object.tag_name == ['']:
                object.tag_name = []

        # 検索結果の件数
        data_count = object_list.count()
        if data_count == 0:
            disp_result = 'ファイルが見つかりませんでした'
        else:
            disp_result = f'{data_count}件のヒット'
        self.extra_context['count_result'] = disp_result

        return object_list

    def post(self, request, *args, **kwargs):
        # 入力内容の保持をしている
        form_value = [
            self.request.POST.get('search_name', None),
        ]
        request.session['form_value'] = form_value
        # 検索時にページネーションに関連したエラーを防ぐ
        self.request.GET = self.request.GET.copy()
        self.request.GET.clear()
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        initial_dict = dict(search_name='', search='file')
        if not self.request.GET == {}:
            print('aaaaaaaaaaaaaaaaaaaaaaaaa')
            if not self.request.GET['search_name']:
                context['search'] = {
                    'is': False,
                }
                context['search_form'] = FileSearchForm(self.request.GET or None, initial=initial_dict)
            else:
                context['search'] = {
                    'is': True,
                    'name': self.request.GET['search_name'],
                    'method': 'タグ検索' if self.request.GET['search']=='tag' else 'ファイル検索',
                }
                context['search_form'] = FileSearchForm(self.request.GET or None, initial=initial_dict)

                if 'page' in self.request.GET.keys():
                    if self.request.GET['search_name'] == 'None':
                        context['search_form'] = FileSearchForm(initial=initial_dict)
            
        else:
            context['search'] = {
                'is': False,
            }
            context['search_form'] = FileSearchForm(self.request.GET or None, initial=initial_dict)

        return context


@login_required(login_url="/top/")
def FileDownload(request):
    #ファイルのダウンロード関数
    #後でクラスベースに変更してくださいお願いします！
    try:
        param = request.GET['param']
        file_data = Filemanage.objects.get(id = param,user_id = request.user.id)

        output_key = file_data.s3_file_name + '.' + file_data.file_extension
        s3 = boto3.client('s3',
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY,
            region_name=REGION_NAME)

        #s3.download_file(S3_FILE_DOWNLOAD, output_key, FILE_PATH+output_key)

        # return FileResponse(open(FILE_PATH + output_key, 'rb'), as_attachment=True, filename=file_data.file_name +'.' +file_data.file_extension)
        att_name = file_data.file_name +'.' +file_data.file_extension
        att_name = urllib.parse.quote(att_name)
        att_name = "attachment; filename*=UTF-8\'\'" + att_name
        url = s3.generate_presigned_url(
            'get_object', 
            Params = { 
                        'Bucket': S3_FILE_DOWNLOAD, 
                        'Key': output_key,
                        'ResponseContentDisposition': att_name,
                    }, 
            ExpiresIn = 600, )
        return HttpResponseRedirect(url)
        #response["Content-Disposition"]="filename=nanbu.docx"
        #return response

    except:
        return False

def FileDownloadPic(request):
    #ファイルのダウンロード関数
    #後でクラスベースに変更してくださいお願いします！
    try:
        param = request.GET['param']
        file_data = Filemanage.objects.get(id = param,user_id = request.user.id)

        output_key = file_data.s3_file_name
        s3 = boto3.client('s3',
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY,
            region_name=REGION_NAME)

        #s3.download_file(S3_FILE_DOWNLOAD, output_key, FILE_PATH+output_key)

        # return FileResponse(open(FILE_PATH + output_key, 'rb'), as_attachment=True, filename=file_data.file_name +'.' +file_data.file_extension)
        att_name = file_data.file_name +'.png'
        att_name = urllib.parse.quote(att_name)
        att_name = "attachment; filename*=UTF-8\'\'" + att_name
        url = s3.generate_presigned_url(
            'get_object', 
            Params = { 
                        'Bucket': S3_FILE_PIC, 
                        'Key': output_key,
                        'ResponseContentDisposition': att_name,
                    }, 
            ExpiresIn = 600, )
        return HttpResponseRedirect(url)
        #response["Content-Disposition"]="filename=nanbu.docx"
        #return response

    except:
        return False


class FileDetail(OnlyYouMixin, generic.TemplateView):
    """ファイルの詳細画面"""
    template_name = 'jsk/file_detail.html'
    # model = Filemanage
    # context_object_name = 'file'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ファイル詳細', 'template_name': template_name}

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser

    # パラメータの作成
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 詳細表示するファイルのデータの取得
        file_data = Filemanage.objects.get(pk=self.kwargs['pk'])
        # tag_name を配列化
        tag_list = self.get_tag_list(file_data.tag_name)
        if tag_list == ['']:
            tag_list = []
        context['tag_list'] = tag_list
        context['file'] = {
            'pk':file_data.id,
            'file_name': file_data.file_name,
            'file_extension': file_data.file_extension,
            'tag_name': file_data.tag_name,
            'update_dt': file_data.update_dt,
            'last_viewed_dt': file_data.last_viewed_dt,
            'pic_flag':file_data.pic_flag,
        }

        return context

    # タグを文字列から配列に変える
    def get_tag_list(self, tag_data):
        return tag_data.split(';')

class TextToTags(OnlyYouMixin, generic.FormView):
    #タグの生成
    template_name = 'jsk/text_to_tags.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'タグの生成', 'template_name': template_name}
    form_class = TextToTagsForm

    def get_success_url(self):
        return resolve_url('jsk:fie_update_done', user_pk=self.user.id, pk=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # この辺に文書ファイルからタグとなる文字列を取得する処理を書く
        file_data = Filemanage.objects.get(id=self.kwargs['pk'], user_id=self.request.user.id)

        output_key = file_data.s3_file_name + '.' + file_data.file_extension + '.json'
        s3 = boto3.client('s3',
            aws_access_key_id=ACCESS_KEY_ID,
            aws_secret_access_key=SECRET_ACCESS_KEY,
            region_name=REGION_NAME)
        s3.download_file(S3_FILE_TAGS, output_key, FILE_PATH+output_key)

        #comprehendが生成したjsonをダウンロード
        with open(FILE_PATH+output_key, 'r', encoding='utf-8') as open_file:
            result = json.load(open_file)
            close()

        #タグが12個未満及び重複しなければリスト追加
        #keyphrase = []
        unique_keyphrase = []
        for phrase in result['KeyPhrases']:
                if len(phrase['Text']) < 20:
                    if (phrase['Text'] in unique_keyphrase) == False:
                        unique_keyphrase.append(phrase['Text'])
        #unique_keyphrase = set(keyphrase)

        # ここに取得したタグのデータを入れる
        # get_tags_list = ['これは', '文書', 'ファイル', 'から', '取得した', 'タグで', 'ある']
        get_tags_list = list(unique_keyphrase)
        if len(get_tags_list) > 12:
            get_tags_list = get_tags_list[0:11]
        # templateで使う変数
        context['get_tags_list'] = get_tags_list

        #ダウンロードしたjsonファイルを削除
        os.remove(FILE_PATH+output_key)


        # 現在のタグのデータを取得
        file_data = Filemanage.objects.filter(id=self.kwargs['pk'])
        if file_data.exists():
            file_id = Filemanage.objects.get(id=self.kwargs['pk'])
            my_tags_list = file_id.tag_name.split(';')
            if my_tags_list == ['']:
                my_tags_list = []
            context['my_tags_list'] = my_tags_list
        else:
            # アクセスしたURLのIDが存在しないなら検索画面へ遷移
            # ほとんどの場合はエラー画面に行くはずだからここの処理は行われないはず
            redirect('jsk:file_search', user_pk=self.kwargs['user_pk'], pk=self.kwargs['pk'])
        return context

    def form_valid(self, form):
        file_data = Filemanage.objects.get(id=self.kwargs['pk'])
        tag_list = self.request.POST['tag_name'].split(',')
        tag_name = ';'.join(tag_list)
        file_data.tag_name = tag_name
        file_data.last_viewed_dt = timezone.localtime()
        file_data.save()

        user_data = User.objects.get(id=self.request.user.id)
        while True:
            token_url = token_urlsafe(16)
            if not User.objects.filter(token=token_url).exists():
                break
        user_data.token = token_url
        user_data.save()

        # return render(self.request, 'jsk/file_update_done.html', context)
        return redirect('jsk:file_update_done', user_pk=self.request.user.id, pk=file_data.id, token=token_url)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser


class FileTagUpdate(OnlyYouMixin, generic.FormView):
    """ファイルの編集画面"""
    template_name = 'jsk/file_update_tags.html'
    model = Filemanage
    form_class = FileTagUpdateForm
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ファイルの編集', 'template_name': template_name}

    def get_context_data(self, **kwargs):
        # 親クラスを先に処理
        context = super().get_context_data(**kwargs)
        # ファイルのIDを取得
        file_id = self.kwargs['pk']
        # ファイルのデータを取得
        file_data = Filemanage.objects.get(id=file_id)
        if 'tag_name' in self.request.POST.keys():
            file_tags = self.request.POST['tag_name'].split(',')
        else:
            # タグデータを取得
            tag_name = file_data.tag_name
            # タグが0個なのか判定
            if tag_name == ';':
                # 空の配列を用意
                file_tags = []
            else:
                # 文字列から配列へ変更
                file_tags = file_data.tag_name.split(';')
                # 最後に謎の空白の値ができるからそれを削除
                if file_tags[-1] == '':
                    del file_tags[-1]
        # 配列をパラメータとして保存
        context["tag_list"] = file_tags

        # ファイル名の存在チェックしたあと、入力の値を保持する
        if 'file_name' in self.request.POST.keys():
            file_name = [self.request.POST['file_name']]
        else:
            file_name = [file_data.file_name]

        context["file_name"] = file_name
        return context

    # def get_success_url(self):

    def form_valid(self, form):
        file_data = Filemanage.objects.get(id=self.kwargs['pk'])
        tag_list = self.request.POST['tag_name'].split(',')
        tag_name = ';'.join(tag_list)
        file_data.tag_name = tag_name
        file_data.file_name = self.request.POST['file_name']
        file_data.last_viewed_dt = datetime.datetime.now()
        file_data.save()

        user_data = User.objects.get(id=self.request.user.id)
        while True:
            token_url = token_urlsafe(16)
            if not User.objects.filter(token=token_url).exists():
                break
        user_data.token = token_url
        user_data.save()

        # return render(self.request, 'jsk/file_update_done.html', context)
        return redirect('jsk:file_update_done', user_pk=self.request.user.id, pk=self.kwargs['pk'], token=token_url)

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        form.set_file_id(kwargs['pk'])
        form.set_user_id(kwargs['user_pk'])
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def test_func(self):
      # 今ログインしてるユーザーのpkと、そのユーザー情報画面のpkが同じか、又はスーパーユーザーなら許可
        # 返すときに使う
        is_pk = False
        user = self.request.user
        # URLのファイルIDを取得
        get_file_pk = self.kwargs['pk']
        # そのIDが存在するか確認
        pk_exist = Filemanage.objects.filter(id=get_file_pk).exists()
        if pk_exist:
            # あった場合はそのデータを取得
            file_data = Filemanage.objects.get(id=get_file_pk)
            # 取得したデータとログイン中のユーザーが同じか確認
            if file_data.user_id == user.pk:
                is_pk = True
                # print(self.kwargs['pk'])
        else:
            # そのIDが存在しない場合Falseを返す
            return False
        return (user.pk == self.kwargs['user_pk'] and is_pk) or user.is_superuser

class FileDelete(generic.DeleteView):
    template_name = ''
    extra_context = {
        'search_form': FileSearchForm(),
        'title': 'ファイル削除', 'template_name': template_name}

    # ファイル削除画面に入った瞬間に削除してファイル検索画面へリダイレクトする
    # もし後に削除画面を導入する際に楽にするため
    # 削除画面導入の時はこの関数をコメントアウト
    def get(self, request, *args, **kwargs):
        try:
            param = self.request.GET['param']
            file_data = Filemanage.objects.get(id = param,user_id = self.request.user.id)
            del_name = file_data.s3_file_name + '.' + file_data.file_extension
            print(del_name)
            file_data.delete()
            # os.remove(FILE_PATH + del_name)
            s3 = boto3.client('s3',
                aws_access_key_id=ACCESS_KEY_ID,
                aws_secret_access_key=SECRET_ACCESS_KEY,
                region_name=REGION_NAME)
            status = s3.delete_object(Bucket=S3_FILE_DOWNLOAD, Key=del_name)
            status2 = s3.delete_object(Bucket=S3_FILE_TAGS,Key=del_name + '.json')
            status3 = s3.delete_object(Bucket=S3_FILE_PIC,Key=file_data.s3_file_name)

            return redirect('jsk:file_search')
        except:
            return Http404

class ErrorView(generic.TemplateView):
    template_name = 'jsk/error_page.html'
    extra_context = {
        'search_form': FileSearchForm(),
        'title': '無効なアクション',
        'template_name': template_name}

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

# 開発用画面 開発終了後削除?
'''
@login_required(login_url="/login/")
def DevelopFileUpload(request):

    test1 = request.user.id

    params = {
        'test1': test1,
        'title':'なんでもいい',
        'template_name':'jsk/develop_fileupload.html',
    }

    return render(request , 'jsk/develop_fileupload.html',params)

@login_required(login_url="/login/")
def DevelopFileUploadResult(request):
    status = 1

    user_id = request.POST.get("user_id")
    filename = request.POST.get("filename")
    file_name = filename.rsplit('.',1)
    if 1 == len(file_name):
        file_name.append('')
    if 4 < len(file_name[1]):
        status *= 5
    s3_file_name = request.POST.get("s3_file_name")
    tag_name = request.POST.get("tag_name")
    tag_check = tag_name.split(';')
    if len(tag_check) > 12:
        status *= 2
    for tag in tag_check:
        if len(tag) >20:
            status *= 3
            break
    update_dt = request.POST.get("update_dt")
    last_viewed_dt = request.POST.get("last_viewed_dt")

    status_disp = ''
    if (status % 2) == 0:
        status_disp += 'タグが12個を超えています。<br>'
    elif (status % 3) == 0:
        status_disp += '文字が20文字を越えています。<br>'
    elif (status % 5) == 0:
        status_disp += '拡張子が4文字を越えています。<br>'
    else :
        Filemanage.objects.create(user_id = user_id,file_name = file_name[0],file_extension = file_name[1],s3_file_name = s3_file_name,tag_name = tag_name,update_dt = update_dt,last_viewed_dt = last_viewed_dt)
        status_disp += '完了。<br>登録されたデータはデータベース等から確認してください。'

    params = {
        'status': status_disp,
        'title':'なくてもいい',
        'template_name':'jsk/develop_result.html',
    }

    return render(request , 'jsk/develop_result.html',params)

@login_required(login_url="/login/")
def DevelopFileSelect(request):


    params = {
        'title':'ファイル送信テスト',
        'template_name':'jsk/develop_fileselect.html',
        }

    return render(request , 'jsk/develop_fileselect.html',params)

@login_required(login_url="/login/")
def DevelopFileSelectResult(request):
    status = 'シェルに出力中'

    filetest = request.FILES['filetest']
    file_name = filetest.name.rsplit('.',1)
    #拡張子がある場合
    if 2 == len(file_name):
        #テキストファイルの場合
        if file_name[1] == 'txt':
            test_text = filetest.read()
            status = test_text.decode('utf-8')
        #文書ファイルの場合
        elif file_name[1] in ['docx']:
            doc = docx.Document(filetest)
            status = ''
            for para in doc.paragraphs:
                status += (str(para.text) + '\n')
        #一致しない場合１
        else:
            status = 'そのファイル形式には対応していません。'
    #一致しない場合２
    else:
        status = 'そのファイル形式には対応していません。'


    params = {
        'status':status,
        'title':'文書ファイル送信テスト結果',
        'template_name':'jsk/develop_result.html',
        }

    return render(request , 'jsk/develop_result.html',params)

@login_required(login_url="/login/")
def DevelopFileSelectResult2(request):
    status = 'シェルに出力中'

    filetest = request.FILES['filetest']
    file_name = filetest.name.rsplit('.',1)
    #拡張子がある場合
    if 2 == len(file_name):
        
        content_type = filetest.content_type.split('/')
        if content_type[0] == 'image':
            im = Image.open(filetest)
            im.show()
        #一致しない場合１
        else:
            status = 'そのファイル形式には対応していません。'
    #一致しない場合２
    else:
        status = 'そのファイル形式には対応していません。'


    params = {
        'status':status,
        'title':'画像ファイル送信テスト結果',
        'template_name':'jsk/develop_result.html',
        }

    return render(request , 'jsk/develop_result.html',params)

@login_required(login_url="/login/")
def DevelopFileDownload(request):
    
    params = {
        'title':'ファイル送受信テスト',
        'template_name':'jsk/develop_filedownload.html',
        }

    return render(request , 'jsk/develop_filedownload.html',params)

@login_required(login_url="/login/")
def DevelopFileDownloadResult(request):

    try:
        filetest = request.FILES['filetest']
        new_path = FILE_PATH + filetest.name

        if request.method == 'POST':
            f = open(new_path,'wb+')
        for chunk in filetest.chunks():
            f.write(chunk)
        f.close()
        
        return FileResponse(open(new_path, 'rb') ,as_attachment=False, filename=('送信成功' + filetest.name))
    except:
        raise Http404

@login_required(login_url="/top/")
def DevelopScheme(request):

    params = {
        'scheme': 'ms-word',
        'title':'スキームテスト',
        'template_name':'jsk/develop_scheme.html',
    }

    return render(request , 'jsk/develop_scheme.html',params)

@login_required(login_url="/top/")
def DevelopSchemeDownload(request):
    
    return FileResponse(open('.\jsk\static\南部.docx', 'rb') ,as_attachment=False,)
'''