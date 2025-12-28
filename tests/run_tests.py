#!/usr/bin/env python3
"""
테스트 실행 스크립트

Usage:
    python tests/run_tests.py                    # 모든 테스트 실행
    python tests/run_tests.py -v                 # Verbose 모드
    python tests/run_tests.py test_email_sender  # 특정 테스트만 실행
"""

import sys
import unittest
import os

# 프로젝트 루트를 Python path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_tests(test_pattern='test_*.py', verbosity=2):
    """테스트 실행"""
    # 테스트 디렉토리
    test_dir = os.path.join(project_root, 'tests')
    
    # 테스트 로더 생성
    loader = unittest.TestLoader()
    
    # 테스트 스위트 생성
    suite = loader.discover(test_dir, pattern=test_pattern)
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # 결과 출력
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("="*70)
    
    # 실패 시 종료 코드 1 반환
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    # 커맨드라인 인자 처리
    verbosity = 2
    test_pattern = 'test_*.py'
    
    if len(sys.argv) > 1:
        if '-v' in sys.argv or '--verbose' in sys.argv:
            verbosity = 2
        if any(arg.startswith('test_') for arg in sys.argv):
            test_pattern = [arg for arg in sys.argv if arg.startswith('test_')][0] + '.py'
    
    # 테스트 실행
    exit_code = run_tests(test_pattern, verbosity)
    sys.exit(exit_code)
