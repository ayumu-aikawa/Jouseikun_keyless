import io
import os
import boto3
import json
import docx

output_bucket = ''


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    input_bucket=event['Records'][0]['s3']['bucket']['name']
    input_data=event['Records'][0]['s3']['object']['key']
    #拡張子をチェック
    file_name = input_data.rsplit('.', 1)
    if file_name[1] == 'txt':
        content = s3.get_object(Bucket=input_bucket, Key=input_data)['Body'].read()
        input_text = content.decode('utf-8')
    elif file_name[1] == 'docx':
        content = ''
        
        obj_data = s3.get_object(Bucket=input_bucket, Key=input_data)['Body']
        doc = docx.Document(io.BytesIO(obj_data.read()))
        content = ''
        for para in doc.paragraphs:
            content += (para.text + '\n') 
        input_text = content
        
    next_text = ''.join(list(input_text.splitlines()))
    
    translate = boto3.client('translate')
    response = translate.translate_text(
        Text=next_text,
        SourceLanguageCode='auto',
        TargetLanguageCode='ja'
        )
        
    comprehend_text = response.get('TranslatedText')

    comprehend = boto3.client('comprehend', 'ap-northeast-1')
    result = comprehend.detect_key_phrases(Text=comprehend_text, LanguageCode='ja')
    # keyphrase = []
    # for phrase in result['KeyPhrases']:
    #         if len(phrase['Text']) < 20:
    #             keyphrase.append(phrase['Text'])
    # unique_keyphrase = set(keyphrase)
    
    # S3に書き込み
    s3 = boto3.resource('s3')
    output_key = f"{input_data}.json"
    
    obj = s3.Object(output_bucket,output_key)
    obj.put( Body=json.dumps(result, ensure_ascii=False) )
    

    return {
        'statusCode': 200,
    }
