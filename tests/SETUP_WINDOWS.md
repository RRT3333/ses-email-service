# Windows 환경 개발 가이드

## Prerequisites

- [Python 3.12](https://www.python.org/downloads/)
- [pyenv-win](https://github.com/pyenv-win/pyenv-win) (선택사항)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Visual Studio Code](https://code.visualstudio.com/)

## 초기 설정

### 1. pyenv-win으로 Python 설치

```powershell
# pyenv-win 설치 (PowerShell 관리자 권한)
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Python 3.12 설치
pyenv install 3.12.0

# 프로젝트에서 Python 3.12 사용
pyenv local 3.12.0

# 확인
python --version
# Python 3.12.0
```

### 2. 가상환경 생성 및 활성화

```powershell
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# PowerShell 실행 정책 에러가 나는 경우
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 의존성 설치

```powershell
# pip 업그레이드
pip install --upgrade pip

# 메인 의존성 설치
pip install -r requirements.txt

# 개발/테스트 의존성 설치 (선택사항)
pip install -r requirements-dev.txt

# AWS SAM CLI 확인
sam --version
```

### 4. 환경 변수 설정

```powershell
# .env 파일 생성
Copy-Item .env.example .env

# .env 파일 편집 (VS Code에서)
code .env
```

**.env 파일 내용:**
```bash
TEST_FROM_EMAIL=your-verified-email@yourdomain.com
TEST_TO_EMAIL=recipient@example.com
SQS_QUEUE_URL=https://sqs.us-west-2.amazonaws.com/123456789012/dev-email-queue
AWS_REGION=us-west-2
```

## VS Code 설정

프로젝트를 VS Code에서 열면 자동으로 가상환경을 인식하고 터미널이 자동으로 활성화됩니다.

### Python 인터프리터 선택

1. `Ctrl+Shift+P` → "Python: Select Interpreter"
2. `.venv\Scripts\python.exe` 선택

### 자동 가상환경 활성화

`.vscode/settings.json`에 이미 설정되어 있습니다:
- 새 터미널을 열면 자동으로 `.venv` 활성화
- 기본 터미널 프로필: "PowerShell (venv)"

**터미널 열기:** `Ctrl+Shift+5` 또는 상단 메뉴 → Terminal → New Terminal

### 권장 확장 프로그램

- Python (Microsoft) - 필수
- Pylance (Microsoft) - 필수
- AWS Toolkit (Amazon Web Services) - 선택사항

## 개발 워크플로우

### 빌드 및 배포

```powershell
# SAM 빌드
sam build

# SAM 배포 (처음)
sam deploy --guided

# SAM 배포 (이후)
sam deploy

# 배포 후 Outputs 확인
# EmailQueueUrl을 .env의 SQS_QUEUE_URL에 복사
```

### 테스트 실행

```powershell
# 단위 테스트
python tests/run_tests.py

# 특정 테스트만
python -m unittest tests.test_email_sender.TestEmailSender.test_successful_email_send

# Verbose 모드
python -m unittest discover tests -v
```

### 이메일 테스트

```powershell
# 정상 발송
python email_test/send_test_message.py --type normal

# 필드 누락 테스트
python email_test/send_test_message.py --type missing-email-id

# Dry-run
python email_test/send_test_message.py --type normal --dry-run
```

### CloudWatch 로그 확인

```powershell
# 실시간 로그 스트리밍
aws logs tail /aws/lambda/dev-email-sender --follow --region us-west-2

# 특정 시간대 로그 조회
aws logs tail /aws/lambda/dev-email-sender --since 1h --region us-west-2
```

## 트러블슈팅

### PowerShell 실행 정책 에러

```powershell
# 현재 사용자 권한으로 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### pyenv 명령어를 찾을 수 없음

환경 변수 PATH에 pyenv 경로 추가:
- `%USERPROFILE%\.pyenv\pyenv-win\bin`
- `%USERPROFILE%\.pyenv\pyenv-win\shims`

### VS Code에서 가상환경이 자동 활성화되지 않음

1. `.vscode/settings.json` 파일이 있는지 확인
2. `Ctrl+Shift+P` → "Python: Select Interpreter" → `.venv\Scripts\python.exe` 선택
3. 기존 터미널 닫기 (`휴지통 아이콘`)
4. 새 터미널 열기 (`Ctrl+Shift+5`)
5. 터미널 프롬프트에 `(.venv)` 표시되는지 확인

**수동으로 활성화:**
```powershell
.\.venv\Scripts\Activate.ps1
```

### SAM build 실패

```powershell
# Python 버전 확인
python --version

# SAM CLI 버전 확인
sam --version

# 가상환경 활성화 확인
Get-Command python
# .venv\Scripts\python.exe 경로가 나와야 함
```

## Git 워크플로우

```powershell
# 변경사항 확인
git status

# 스테이징
git add .

# 커밋
git commit -m "feat: 새로운 기능 추가"

# 푸시
git push origin main
```

## 추가 정보

- AWS SES Sandbox 모드에서는 인증된 이메일 주소로만 발송 가능
- Production 모드 전환은 AWS SES 콘솔에서 요청 필요
- Rate Limit 증가가 필요한 경우 AWS Support 티켓 생성
