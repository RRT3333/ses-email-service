import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    for record in event['Records']:
        sns_message = json.loads(record['Sns']['Message'])
        
        # Configuration Set은 eventType 사용
        event_type = sns_message.get('eventType')
        mail = sns_message['mail']
        message_id = mail['messageId']
        
        # 태그에서 email_id 추출
        tags = mail.get('tags', {})
        email_id = tags.get('email_id', [None])[0]
        
        if event_type == 'Bounce':
            bounce = sns_message['bounce']
            bounce_type = bounce['bounceType']
            
            for recipient in bounce['bouncedRecipients']:
                email = recipient['emailAddress']
                logger.info(f"Bounce - Type: {bounce_type}, Email: {email}, EmailId: {email_id}")
                
                # TODO: DB 업데이트
                
        elif event_type == 'Complaint':
            complaint = sns_message['complaint']
            
            for recipient in complaint['complainedRecipients']:
                email = recipient['emailAddress']
                logger.warning(f"Complaint - Email: {email}, EmailId: {email_id}")
                
                # TODO: 수신거부 처리
                
        elif event_type == 'Delivery':
            delivery = sns_message['delivery']
            logger.info(f"Delivered - Recipients: {delivery['recipients']}, EmailId: {email_id}")
            
            # TODO: 상태를 'delivered'로 업데이트
            
        elif event_type == 'Reject':
            logger.error(f"Rejected - MessageId: {message_id}, EmailId: {email_id}")
            
    return {'statusCode': 200}
