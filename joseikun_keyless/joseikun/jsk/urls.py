from django.urls import path
from . import views

app_name = 'jsk'

urlpatterns = [
    path('', views.Top.as_view(), name='top'),
    # ログイン/ログアウト
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    # アカウント仮登録～本登録完了
    path('user_create_input/', views.UserDataInput.as_view(), name='user_create_input'),
    path('user_create_confirm/', views.UserDataConfirm.as_view(), name='user_create_confirm'),
    path('user_create/done', views.UserCreateDone.as_view(), name='user_create_done'),
    path('user_create/complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    # アカウントの詳細表示・更新・削除
    path('user_detail/<int:pk>/', views.UserDetail.as_view(), name='user_detail'),
    path('user_update/<int:pk>/', views.UserUpdate.as_view(), name='user_update'),
    # ここに編集確認画面を入れる
    path('user_delete/<int:pk>/', views.UserDelete.as_view(), name='user_delete'),
    # パスワードの再設定
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    # パスワードの再発行
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    # path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    # ファイルのアップロード
    path('file_upload_text/', views.FileUploadText.as_view(), name='file_upload_text'),
    path('file_upload_image/', views.FileUploadImage.as_view(), name='file_upload_image'),
    # 完了画面は render() で対応しました。
    path('file_upload_done/<int:user_pk>/<int:pk>/<str:token>', views.FileUploadDone.as_view(), name='file_upload_done'),
    path('file_update_done/<int:user_pk>/<int:pk>/<str:token>', views.FileUpdateDone.as_view(), name='file_update_done'),
    # ファイルの一覧表示
    # path('file_search/<int:pk>/', views.FileSearch.as_view(), name='file_search'),
    path('file_search/', views.FileSearch.as_view(), name='file_search'),
    path('file_download/',views.FileDownload,name='file_download'),
    path('file_download_pic/',views.FileDownloadPic,name='file_download_pic'),
    path('file_detail/<int:user_pk>/<int:pk>/', views.FileDetail.as_view(), name='file_detail'),
    # ファイルの編集
    path('file_update_text/<int:user_pk>/<int:pk>', views.FileTextUpdate.as_view(), name='file_update_text'),
    # タグの編集
    path('file_update_tags/<int:user_pk>/<int:pk>/', views.FileTagUpdate.as_view(), name='file_update_tags'),
    path('text_to_tags/<int:user_pk>/<int:pk>/', views.TextToTags.as_view(), name='text_to_tags'),
    # ファイルの削除
    path('file_delete/', views.FileDelete.as_view(), name='file_delete'),
    # なにかいかがわしいことをした場合
    path('invalid_action_error/', views.ErrorView.as_view(), name='error_view'),
    #開発用ページ
    #path('develop/fileupload/',views.DevelopFileUpload,name='develop_fileupload'),
    #path('develop/fileupload_result/',views.DevelopFileUploadResult,name='develop_fileupload_result'),
    #path('develop/fileselect/',views.DevelopFileSelect,name='develop_fileselect'),
    #path('develop/fileselect_result/',views.DevelopFileSelectResult,name='develop_fileselect_result'),
    #path('develop/fileselect_result2/',views.DevelopFileSelectResult2,name='develop_fileselect_result2'),
    #path('develop/filedownload/',views.DevelopFileDownload,name='develop_filedownload'),
    #path('develop/filedownload_result/',views.DevelopFileDownloadResult,name='develop_filedownload_result'),
    #path('develop/develop_scheme/',views.DevelopScheme,name='develop_scheme'),
    #path('develop/develop_schemedownload/',views.DevelopSchemeDownload,name='develop_schemedownload'),
]