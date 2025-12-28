import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# boto3를 mock하여 실제 AWS 연결 방지
sys.modules['boto3'] = MagicMock()

# 테스트 대상 모듈 임포트를 위한 경로 설정
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'email_sender'))
import app


class TestEmailSender(unittest.TestCase):
    """이메일 발송 Lambda 함수 테스트"""
    
    def setUp(self):
        """각 테스트 전 실행"""
        self.ses_mock = MagicMock()
        
        # SES 예외 클래스를 실제 예외처럼 동작하도록 설정
        self.ses_mock.exceptions.MessageRejected = type('MessageRejected', (Exception,), {})
        self.ses_mock.exceptions.MailFromDomainNotVerifiedException = type('MailFromDomainNotVerifiedException', (Exception,), {})
        
        app.ses = self.ses_mock
        
        # 환경변수 모킹
        self.env_patcher = patch.dict(os.environ, {
            'SES_CONFIG_SET_NAME': 'test-configuration-set'
        })
        self.env_patcher.start()
        app.CONFIG_SET_NAME = os.environ.get('SES_CONFIG_SET_NAME', 'my-first-configuration-set')
    
    def tearDown(self):
        """각 테스트 후 실행"""
        self.env_patcher.stop()
        
    def _create_event(self, message_body):
        """SQS 이벤트 생성 헬퍼"""
        return {
            'Records': [
                {
                    'body': json.dumps(message_body)
                }
            ]
        }
    
    # ===== 정상 케이스 =====
    
    def test_successful_email_send(self):
        """정상적인 이메일 발송"""
        # Given
        self.ses_mock.send_email.return_value = {
            'MessageId': 'test-message-id-123'
        }
        
        message = {
            'email_id': 'test-001',
            'from': 'verified-sender@example.com',
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': '<html>Test Body</html>'
        }
        event = self._create_event(message)
        
        # When
        result = app.lambda_handler(event, None)
        
        # Then
        self.assertEqual(result['statusCode'], 200)
        self.ses_mock.send_email.assert_called_once()
        
        # SES 호출 파라미터 확인
        call_args = self.ses_mock.send_email.call_args[1]
        self.assertEqual(call_args['Source'], 'verified-sender@example.com')
        self.assertEqual(call_args['Destination']['ToAddresses'][0], 'recipient@example.com')
        self.assertEqual(call_args['Message']['Subject']['Data'], 'Test Subject')
        self.assertEqual(call_args['Message']['Body']['Html']['Data'], '<html>Test Body</html>')
        self.assertEqual(call_args['ConfigurationSetName'], 'test-configuration-set')
        self.assertEqual(call_args['Tags'][0]['Name'], 'email_id')
        self.assertEqual(call_args['Tags'][0]['Value'], 'test-001')
    
    def test_email_with_korean_subject(self):
        """한글 제목 이메일 발송"""
        # Given
        self.ses_mock.send_email.return_value = {
            'MessageId': 'test-message-id-456'
        }
        
        message = {
            'email_id': 'test-002',
            'from': 'verified-sender@example.com',
            'to': 'recipient@example.com',
            'subject': '안녕하세요 테스트 메일입니다',
            'body': '<html><body>테스트 내용</body></html>'
        }
        event = self._create_event(message)
        
        # When
        result = app.lambda_handler(event, None)
        
        # Then
        self.assertEqual(result['statusCode'], 200)
        self.ses_mock.send_email.assert_called_once()
        
        call_args = self.ses_mock.send_email.call_args[1]
        self.assertEqual(call_args['Message']['Subject']['Data'], '안녕하세요 테스트 메일입니다')
        self.assertEqual(call_args['Message']['Subject']['Charset'], 'UTF-8')
        self.assertEqual(call_args['Message']['Body']['Html']['Charset'], 'UTF-8')
    
    # ===== SES 예외 처리 케이스 =====
    
    def test_message_rejected_exception(self):
        """SES MessageRejected 예외 처리 - 재시도하지 않음"""
        # Given
        self.ses_mock.send_email.side_effect = self.ses_mock.exceptions.MessageRejected('Email address is not verified')
        
        message = {
            'email_id': 'test-003',
            'from': 'verified-sender@example.com',
            'to': 'unverified@example.com',
            'subject': 'Test Subject',
            'body': '<html>Test Body</html>'
        }
        event = self._create_event(message)
        
        # When & Then
        with self.assertLogs(level='ERROR') as log:
            result = app.lambda_handler(event, None)
        
        # MessageRejected는 재시도하지 않고 정상 처리
        self.assertEqual(result['statusCode'], 200)
        self.assertTrue(any('Message rejected' in msg for msg in log.output))
    
    def test_domain_not_verified_exception(self):
        """SES MailFromDomainNotVerifiedException 예외 처리 - 재시도하지 않음"""
        # Given
        self.ses_mock.send_email.side_effect = self.ses_mock.exceptions.MailFromDomainNotVerifiedException('Domain not verified')
        
        message = {
            'email_id': 'test-004',
            'from': 'verified-sender@example.com',
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': '<html>Test Body</html>'
        }
        event = self._create_event(message)
        
        # When & Then
        with self.assertLogs(level='ERROR') as log:
            result = app.lambda_handler(event, None)
        
        # Domain not verified는 재시도하지 않고 정상 처리
        self.assertEqual(result['statusCode'], 200)
        self.assertTrue(any('Domain not verified' in msg for msg in log.output))
    
    def test_generic_exception_raises(self):
        """일반 예외는 재시도를 위해 raise"""
        # Given
        self.ses_mock.send_email.side_effect = Exception('Network timeout error')
        
        message = {
            'email_id': 'test-005',
            'from': 'verified-sender@example.com',
            'to': 'recipient@example.com',
            'subject': 'Test Subject',
            'body': '<html>Test Body</html>'
        }
        event = self._create_event(message)
        
        # When & Then
        with self.assertLogs(level='ERROR') as log:
            # 일반 예외는 재시도를 위해 raise되어야 함
            with self.assertRaises(Exception) as context:
                app.lambda_handler(event, None)
            
            self.assertEqual(str(context.exception), 'Network timeout error')
            self.assertTrue(any('Error sending email' in msg for msg in log.output))
    
    # ===== 배치 처리 케이스 =====
    
    def test_multiple_messages_processing(self):
        """여러 메시지 배치 처리 - 모두 성공"""
        # Given
        self.ses_mock.send_email.return_value = {
            'MessageId': 'test-message-id'
        }
        
        event = {
            'Records': [
                {'body': json.dumps({
                    'email_id': 'test-006',
                    'from': 'verified-sender@example.com',
                    'to': 'recipient1@example.com',
                    'subject': 'Test 1',
                    'body': '<html>Body 1</html>'
                })},
                {'body': json.dumps({
                    'email_id': 'test-007',
                    'from': 'verified-sender@example.com',
                    'to': 'recipient2@example.com',
                    'subject': 'Test 2',
                    'body': '<html>Body 2</html>'
                })},
                {'body': json.dumps({
                    'email_id': 'test-008',
                    'from': 'verified-sender@example.com',
                    'to': 'recipient3@example.com',
                    'subject': 'Test 3',
                    'body': '<html>Body 3</html>'
                })}
            ]
        }
        
        # When
        result = app.lambda_handler(event, None)
        
        # Then
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(self.ses_mock.send_email.call_count, 3)
    
    def test_partial_failure_in_batch(self):
        """배치 중 일부 메시지 실패 - 첫 번째는 성공, 두 번째는 실패"""
        # Given
        self.ses_mock.send_email.side_effect = [
            {'MessageId': 'test-006-success'},  # 첫 번째 성공
            Exception('Connection timeout')      # 두 번째 실패 (재시도 필요)
        ]
        
        event = {
            'Records': [
                {'body': json.dumps({
                    'email_id': 'test-006',
                    'from': 'verified-sender@example.com',
                    'to': 'recipient1@example.com',
                    'subject': 'Test 1',
                    'body': '<html>Body 1</html>'
                })},
                {'body': json.dumps({
                    'email_id': 'test-007',
                    'from': 'verified-sender@example.com',
                    'to': 'recipient2@example.com',
                    'subject': 'Test 2',
                    'body': '<html>Body 2</html>'
                })}
            ]
        }
        
        # When & Then
        # 두 번째 메시지 실패로 예외 발생 (SQS가 배치 전체를 재시도)
        with self.assertRaises(Exception):
            app.lambda_handler(event, None)
        
        # 첫 번째는 호출되었음
        self.assertEqual(self.ses_mock.send_email.call_count, 2)
    
    def test_batch_with_rejected_and_success(self):
        """배치 중 MessageRejected와 성공 혼합 - 정상 완료"""
        # Given
        self.ses_mock.send_email.side_effect = [
            self.ses_mock.exceptions.MessageRejected('Invalid email'),  # 첫 번째 거부
            {'MessageId': 'test-007-success'}  # 두 번째 성공
        ]
        
        event = {
            'Records': [
                {'body': json.dumps({
                    'email_id': 'test-006',
                    'from': 'verified-sender@example.com',
                    'to': 'invalid@example.com',
                    'subject': 'Test 1',
                    'body': '<html>Body 1</html>'
                })},
                {'body': json.dumps({
                    'email_id': 'test-007',
                    'from': 'verified-sender@example.com',
                    'to': 'valid@example.com',
                    'subject': 'Test 2',
                    'body': '<html>Body 2</html>'
                })}
            ]
        }
        
        # When & Then
        with self.assertLogs(level='ERROR') as log:
            result = app.lambda_handler(event, None)
        
        # MessageRejected는 정상 처리되므로 statusCode 200
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(self.ses_mock.send_email.call_count, 2)
        self.assertTrue(any('Message rejected' in msg for msg in log.output))


if __name__ == '__main__':
    unittest.main()
