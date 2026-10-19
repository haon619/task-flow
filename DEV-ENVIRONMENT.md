# DEV-ENVIRONMENT

확인일: 2026-10-19. 아래 출력은 이 컴퓨터에서 실행한 결과를 그대로 옮긴 것이다.

## 운영체제 · 셸
| 항목 | 값 |
|---|---|
| 운영체제 | Microsoft Windows 11 Pro, 버전 10.0.22631, 64비트 |
| 셸 | PowerShell 7.6.7 (Git Bash도 사용할 수 있음) |

## 도구별 버전 (`--version` 결과 그대로)
| 도구 | 명령 | 결과 |
|---|---|---|
| git | `git --version` | `git version 2.56.0.windows.2` |
| node | `node --version` | 실행 안 됨: `'node' 용어는 cmdlet, 함수, 스크립트 파일 또는 실행 프로그램의 이름으로 인식되지 않습니다.` |
| npm | `npm --version` | 실행 안 됨: `'npm' 용어는 cmdlet, 함수, 스크립트 파일 또는 실행 프로그램의 이름으로 인식되지 않습니다.` |
| uv | `uv --version` | `uv 0.13.1 (62faed335 2026-10-13 x86_64-pc-windows-msvc)` |
| python | `python --version` | 출력 `Python`, 종료 코드 9009. PATH의 `python`은 윈도우 스토어 연결 파일(`C:\Users\EZ\AppData\Local\Microsoft\WindowsApps\python.exe`)이라 실제 Python이 아니다. |
| python (uv 관리) | `python3.12 --version` | `Python 3.12.15` |

참고: SQLite는 따로 설치하지 않고 Python 내장 모듈을 쓴다.

## 새로 설치한 것 (M0, 2026-10-19)
- Node.js LTS v24.22.0, npm 11.19.1: winget이 충돌(0xC0000005)해서 nodejs.org 공식 MSI(서명 확인)를 사용자가 직접 설치했다. 설치 직후 열린 터미널에는 PATH가 반영되지 않을 수 있어 새 터미널이 필요하다.

## 아직 없는 것
없음.
