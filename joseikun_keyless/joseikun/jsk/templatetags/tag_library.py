'''
# Templateから独自関数を呼び出して利用する方法
# おまじない [ register = template.Library() ] を記載する
# 関数名を [ @register.filter(name=”関数名”) ] として記載する
# 関数は普通に [ def 関数名 ] で書き始める
# return は1つだけ ※ Template内でリストをこね回せないので
'''
'''
独自関数の呼出しの手順
# 独自関数を使うTemplateに {% load 呼出し名 %}を配置
# 値を返す位置に {{ 引数| 関数名:第2引数 }} を記載
'''


from django import template
register = template.Library()

@register.filter(name="change_Tags")
def change_Tags(tag_name):
    return tag_name.split(';')