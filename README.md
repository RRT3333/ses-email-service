# 📧 SES Email Service

[![AWS](https://img.shields.io/badge/AWS-%23232F3E?logo=amazonwebservices&logoColor=white)](https://aws.amazon.com/)
[![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?logo=awslambda&logoColor=white)](https://aws.amazon.com/lambda/)
[![Amazon SQS](https://img.shields.io/badge/Amazon_SQS-FF4F8B?logo=amazonsqs&logoColor=white)](https://aws.amazon.com/sqs/)
[![Amazon SES](https://img.shields.io/badge/Amazon_SES-DD344C?logo=amazonsimpleemailservice&logoColor=white)](https://aws.amazon.com/ses/)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![AWS SAM](https://img.shields.io/badge/AWS_SAM-FF9900?logo=amazonwebservices&logoColor=white)](https://aws.amazon.com/serverless/sam/)

> 서버리스 기반 비동기 이메일 발송 시스템

## 배경
Cold-Email 대량발송 및 추적 솔루션을 제작하던 중 AWS SES API를 웹서버 에서 직접 호출하는 방식으로 구현하였더니 다음과 같은 문제점이 발생하였음.

<img width="1970" height="973" alt="image" src="https://github.com/user-attachments/assets/73bee12a-2b34-4826-bfaa-6b49e3188d12" />

- **SES Rate Limit**: 초당 14개 발송 한도로 인한 Throttling 에러
- **동기 처리 지연**: 대량 발송 시 사용자 응답 대기 시간 증가
- **실패 처리 부재**: 발송 실패 시 재시도 로직 없음
- **상태 추적 불가**: Bounce, Complaint 등 이메일 상태 파악 어려움

이를 해결하기 위해 SQS + Lambda 기반의 비동기 이메일 발송 시스템을 구축함.

## Architecture
```mermaid
graph TD
    subgraph "WAS"
        A[Web Server]
    end

    subgraph "Message Queue"
        B[SQS<br/>email-outbound-queue]
        C[SQS<br/>email-outbound-dlq]
    end

    subgraph "Processing"
        D[Lambda<br/>email-sender]
        E[Lambda<br/>bounce-handler]
    end

    subgraph "Email Service"
        F[SES<br/>Configuration Set]
    end

    subgraph "Notifications"
        G[SNS<br/>ses-bounce-notifications]
    end

    subgraph "Monitoring"
        H[CloudWatch Logs]
        I[CloudWatch Alarm]
    end

    subgraph "Recipients"
        J[수신자 메일서버]
    end

    %% 정상 발송 흐름
    A -->|1. 메시지 등록| B
    B -->|2. 트리거| D
    D -->|3. 이메일 발송| F
    F -->|4. 전송| J

    %% 실패 처리
    B -->|3회 실패| C
    C -->|알람| I

    %% 이벤트 처리
    F -->|Bounce/Complaint/Delivery| G
    G -->|트리거| E
    E -->|상태 업데이트| A

    %% 로깅
    D -->|로그| H
    E -->|로그| H

    %% 스타일
    style A fill:#3498db,color:#fff
    style B fill:#f39c12,color:#fff
    style C fill:#e74c3c,color:#fff
    style D fill:#9b59b6,color:#fff
    style E fill:#9b59b6,color:#fff
    style F fill:#1abc9c,color:#fff
    style G fill:#e91e63,color:#fff
    style H fill:#607d8b,color:#fff
    style I fill:#ff5722,color:#fff
    style J fill:#4caf50,color:#fff
```

## Project Structure

```
ses-email-service/
├── src/
│   ├── email_sender/
│   │   └── app.py          # 이메일 발송 Lambda
│   └── bounce_handler/
│       └── app.py          # Bounce/Complaint 처리 Lambda
├── template.yaml           # SAM 템플릿
├── samconfig.toml          # SAM 배포 설정
└── README.md
```

## 주요 흐름

### 이메일 발송
1. 웹서버 에서 이메일 발송 요청을 SQS에 등록
2. Lambda(email-sender)가 SQS 메시지를 받아 SES로 발송
3. 실패 시 최대 3회 재시도 후 DLQ로 이동

### 이벤트 처리
1. SES에서 Bounce/Complaint/Delivery 이벤트 발생
2. SNS를 통해 Lambda(bounce-handler)로 전달
3. 이메일 상태 업데이트 및 필요 시 블랙리스트 처리

## Tech Stack
|구성요소|	기술|	용도|
|------|-----|------|
|Queue	|Amazon SQS	|메시지 대기열 및 DLQ|
|Compute	|AWS Lambda	|이메일 발송 및 이벤트 처리|
|Email	|Amazon SES	|이메일 발송|
|Notification|	Amazon SNS	|SES 이벤트 전달|
|Monitoring|	CloudWatch|	로그 및 알람|
|IaC	|AWS SAM	|인프라 코드 관리|


## Configuration
| 항목 | 값 | 설명 |
|------|-----|------|
| Lambda 동시성 | 10 | SES Rate Limit 내 안정적 처리 |
| SQS 배치 크기 | 1 | 실패 시 개별 재시도 |
| 최대 재시도 | 3회 | DLQ 이동 전 재시도 횟수 |
| Visibility Timeout | 60초 | Lambda timeout × 6 |

## Setup

### Windows 환경 개발자

자세한 설정 가이드는 [SETUP_WINDOWS.md](SETUP_WINDOWS.md)를 참고하세요.

**빠른 시작:**
```powershell
# 1. Python 3.12 설치 (pyenv-win)
pyenv install 3.12.0
pyenv local 3.12.0

# 2. 가상환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 개발/테스트용

# 4. 환경 변수 설정
Copy-Item .env.example .env
code .env  # 이메일 주소 설정
```

## Deployment

### Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html) configured
- [SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) installed
- SES domain verified
- Python 3.12

### Deploy

```bash
sam build
sam deploy --guided
```

## Test

### 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경 변수 파일 생성
cp .env.example .env

# 3. .env 파일 편집
# - TEST_FROM_EMAIL: SES 인증된 발신자 이메일
# - TEST_TO_EMAIL: 수신자 이메일
# - SQS_QUEUE_URL: sam deploy 후 확인
```

### 테스트 메시지 전송

```bash
# 정상 발송
python email_test/send_test_message.py --type normal

# 필수 필드 누락 (즉시 삭제, DLQ 안감)
python email_test/send_test_message.py --type missing-email-id
python email_test/send_test_message.py --type missing-from

# 미인증 이메일 (MessageRejected, DLQ 안감)
python email_test/send_test_message.py --type unverified-email

# Dry-run 모드
python email_test/send_test_message.py --type normal --dry-run
```

### SQS Message Format

```json
{
    "email_id": "unique-email-id",
    "from": "sender@yourdomain.com",
    "to": "recipient@example.com",
    "subject": "Email Subject",
    "body": "<html>Email content</html>"
}
```

## Monitoring

| 로그 | 위치 |
|------|------|
| 발송 로그 | `/aws/lambda/{env}-email-sender` |
| 이벤트 처리 로그 | `/aws/lambda/{env}-bounce-handler` |

**CloudWatch Alarm**: DLQ 메시지 ≥ 1 시 알림

## Notes

- SES Sandbox 모드: 인증된 이메일로만 발송 가능
- Production 전환: AWS SES 콘솔에서 요청 필요
- Rate Limit 증가: AWS Support 티켓 생성

