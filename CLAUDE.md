# Korean Public Nonferrous Metal Price Dashboard

## 프로젝트 개요
조달청 비축물자 원자재 판매가격(https://www.pps.go.kr/bichuk/bbs/list.do?key=00825)을
시각화하는 대시보드 프로젝트.

## 대상 원자재 (9종)
- 알루미늄(서구산)
- 알루미늄(비서구산)
- 구리(99.99%이상)
- 납(99.99%이상)
- 아연
- 주석(99.85%이상)
- 주석(99.99%이상)
- 니켈(합금용)
- 니켈(도금용)

## 데이터 범위
2012년 1월 6일부터 오늘까지의 일별 가격 데이터.
가격은 부가세 포함/미포함 두 기준 모두 필요.

## 디렉토리 구조
- /.devcontainer — GitHub Codespaces 환경 설정
- /sync.ps1 — git add + commit + push 자동화 스크립트
- /pull.ps1 — git pull 자동화 스크립트

## 작업 규칙
- 모든 코드 주석과 변수명은 영어로, 사용자 응답은 한국어로
- 데이터 저장은 CSV 형식 사용
- 날짜 형식은 YYYY-MM-DD 통일
- 새 스크립트 작성 시 Python 3.14 기준으로 작성 (경로: C:\Users\seren\AppData\Local\Python\bin\python.exe)

## 동기화 워크플로우
작업 시작 전: .\pull.ps1
작업 종료 후: .\sync.ps1

## 환경
- OS: Windows
- Node.js, Git, Python 3.13 설치됨
- GitHub 리포지토리: Korean_Public_Nonferrous_Metal_Price
