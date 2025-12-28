# Tests

이메일 서비스의 단위 테스트 모음입니다.

## 테스트 구조

```
tests/
├── test_email_sender.py    # 이메일 발송 Lambda 테스트
├── run_tests.py             # 테스트 실행 스크립트
├── requirements.txt         # 테스트 의존성
└── README.md
```

## 실행 방법

### 모든 테스트 실행

```bash
python tests/run_tests.py
```

또는

```bash
python -m unittest discover tests
```

### 특정 테스트 파일만 실행

```bash
python -m unittest tests.test_email_sender
```

### 특정 테스트 케이스만 실행

```bash
python -m unittest tests.test_email_sender.TestEmailSender.test_successful_email_send
```

### Verbose 모드

```bash
python -m unittest discover tests -v
```

## 테스트 커버리지

### test_email_sender.py

#### ✅ 정상 케이스
- `test_successful_email_send`: 정상적인 이메일 발송
- `test_email_with_korean_subject`: 한글 제목/내용 이메일 발송

#### 🚨 SES 예외 처리 케이스
- `test_message_rejected_exception`: MessageRejected 예외 (재시도 없음)
- `test_domain_not_verified_exception`: MailFromDomainNotVerifiedException 예외 (재시도 없음)
- `test_generic_exception_raises`: 일반 예외 (재시도 필요)

#### 📦 배치 처리 케이스
- `test_multiple_messages_processing`: 여러 메시지 배치 처리 (모두 성공)
- `test_partial_failure_in_batch`: 배치 중 일부 실패
- `test_batch_with_rejected_and_success`: MessageRejected와 성공 혼합

## 예상 출력

```
test_batch_with_rejected_and_success ... ok
test_domain_not_verified_exception ... ok
test_email_with_korean_subject ... ok
test_generic_exception_raises ... ok
test_message_rejected_exception ... ok
test_multiple_messages_processing ... ok
test_partial_failure_in_batch ... ok
test_successful_email_send ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.009s

OK
```

## 의존성 설치

```bash
pip install -r requirements-dev.txt
```

## 주의사항

- 테스트는 실제 AWS 리소스를 사용하지 않고 Mock을 사용합니다
- 실제 SES API 호출이 발생하지 않습니다
- 단위 테스트만 포함되어 있으며, 통합 테스트는 별도로 구성해야 합니다
