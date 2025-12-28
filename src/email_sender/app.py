import boto3
import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ses = boto3.client('ses')
CONFIG_SET_NAME = os.environ.get('SES_CONFIG_SET_NAME', 'my-first-configuration-set')

def lambda_handler(event, context):
    for record in event['Records']:
        message = json.loads(record['body'])
        try:
            response = ses.send_email(
                Source=message['from'],
                Destination={
                    'ToAddresses': [message['to']]
                },
                Message={
                    'Subject': {'Data': message['subject'], 'Charset': 'UTF-8'},
                    'Body': {
                        'Html': {'Data': message['body'], 'Charset': 'UTF-8'}
                    }
                },
                ConfigurationSetName=CONFIG_SET_NAME,
                Tags=[
                    {'Name': 'email_id', 'Value': str(message['email_id'])}  # ← 추가
                ]
            )
            
            logger.info(f"Email sent successfully. MessageId: {response['MessageId']}, EmailId: {message.get('email_id')}")
            
            # TODO: DB 상태 업데이트 API 호출 또는 다른 SQS로 결과 전송
            
        except ses.exceptions.MessageRejected as e:
            logger.error(f"Message rejected: {str(e)}")
            # 재시도 무의미 - 정상 리턴하여 메시지 삭제
            
        except ses.exceptions.MailFromDomainNotVerifiedException as e:
            logger.error(f"Domain not verified: {str(e)}")
            # 재시도 무의미
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise  # 재시도 필요한 경우 예외 발생
    
    return {'statusCode': 200}