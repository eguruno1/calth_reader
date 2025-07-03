# PyCalthReader

PyCalthReader는 PyQt5를 사용하여 개발된 의료진단장비용 파이썬 애플리케이션입니다. 
백엔드/프론트엔드 구조적 분리와 디버그 모드를 지원하여 개발과 실제 운영 환경을 구분할 수 있습니다.

## 프로젝트 구조

```
calth_reader/
├── main.py                 # 메인 애플리케이션 진입점
├── requirements.txt        # 패키지 의존성
├── README.md              # 프로젝트 문서
├── config/                # 설정 관리
│   ├── config.py          # 애플리케이션 설정 (디버그 모드 등)
│   └── settings.json      # 설정 파일 (자동 생성)
├── backend/               # 백엔드 서비스
│   ├── backend_manager.py # 백엔드 통합 관리자
│   ├── camera_manager.py  # 카메라 제어 매니저
│   └── uart_manager.py    # UART 통신 매니저
├── views/                 # 프론트엔드 뷰들
│   ├── Utils.py           # 뷰 유틸리티
│   ├── SystemStatus.py    # 시스템 상태 표시
│   ├── VKeyboard.py       # 가상 키보드
│   ├── LoadView.py        # 로딩 화면
│   ├── HomeView.py        # 홈 화면
│   ├── OperatorView.py    # 관리자 화면
│   ├── SelectView.py      # 테스트 선택 화면
│   ├── TestInfoView.py    # 테스트 정보 화면
│   ├── MeasureView.py     # 측정 화면
│   ├── ResultView0.py     # 결과 화면
│   ├── ResultListView.py  # 결과 목록 화면
│   ├── SettingsView.py    # 설정 화면
│   └── InfoView.py        # 정보 화면
├── ui/                    # UI 파일들
│   └── *.ui              # Qt Designer 파일들
├── fonts/                 # 폰트 파일들
├── info/                  # 정보 파일들
└── ...
```

## 주요 기능

### 백엔드/프론트엔드 분리
- **백엔드**: 카메라, UART 등 하드웨어 제어
- **프론트엔드**: PyQt5 기반 사용자 인터페이스
- **통합 관리**: BackendManager를 통한 백엔드 서비스 통합 관리

### 디버그 모드 지원
- **실제 하드웨어 모드**: 실제 카메라와 UART 사용
- **디버그 모드**: 가상 카메라와 가상 UART 사용
- **자동 전환**: 하드웨어 연결 실패시 자동으로 디버그 모드로 전환
- **수동 전환**: Ctrl+D로 디버그 모드 토글 가능

### 시스템 상태 모니터링
- 실시간 시스템 상태 표시
- 카메라/UART 연결 상태 확인
- 디버그/실제 하드웨어 모드 표시

## 단축키

- **Ctrl+Q**: 애플리케이션 종료
- **Ctrl+X**: 시스템 종료 (확인 다이얼로그)
- **Ctrl+D**: 디버그 모드 토글 (재시작 필요)

## 시스템 요구사항

- Python 3.6 이상
- PyQt5
- OpenCV (카메라 제어용)
- pyserial (UART 통신용, 선택사항)
- numpy

### 패키지 설치
```bash
# 기본 패키지 설치
sudo apt-get install python3-pyqt5
pip install -r requirements.txt

# UART 통신용 (선택사항)
pip install pyserial
```

## JETSON Tweak 설정

# 우분투 Tweak 설치
- sudo apt-get install gnome-shell-extensions
- sudo apt-get install gnome-shell-extension-autohidetopbar

# 우분투 자체 키보드 팝업 방지
- gsettings set org.gnome.desktop.a11y.applications screen-keyboard-enabled false

# 우분투 부트 메세지 숨기기
- sudo nano /etc/extlinux/extlinux.conf
; APPEND quiet loglevel=0 vt.global_cursor_default=0 console=tty1 fbcon=map:1

# 우분투 로고 변경하기
  1. sudo apt install liblz4-tool
  2. git clone https://github.com/VladimirSazonov/jw-boot-logo-for-Jetson-Nano
  3. cd jw-boot-logo-for-Jetson-Nano
  4. git clone https://github.com/nothings/stb
  5. g++ -o jw_boot_image main.cpp
  6. ./jw_boot_image [path_to_your_logo]
  7. "bmp.blob"이라는 출력 파일이 있는지 확인합니다.
  8. "bmp.blob"을 [path_to_your_bsp]/Linux_for_Tegra/bootloader/에 복사합니다.
  9. cd [path_to_your_bsp]/Linux_for_Tegra/
  10. sudo ./flash.sh -k BMP --image bootloader/bmp.blob jetson-nano-qspi-sd mmcblk0p1
   ; 플래싱 완료 후 재부팅

# 두번째 로고 변경하기
  1. /usr/share/backgrounds/NVIDIA_Login_Logo.png 교체

# 부팅시 자동실행

##시스템 서비스로 설정하기 (systemd 사용)
  1. 서비스 파일 작성:
   ; /etc/systemd/system/ 디렉토리에 새로운 서비스 파일을 작성합니다.
   ; sudo nano /etc/systemd/system/myscript.service
  
  2. 서비스 파일 내용:
   [Unit]
   Description=My Python Script
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/your_script.py
   WorkingDirectory=/path/to
   User=your_username
   Restart=always

   [Install]
   WantedBy=multi-user.target

  3. 서비스 활성화:
   ; 서비스 파일을 저장한 후, 다음 명령어로 활성화합니다.
   ; sudo systemctl enable myscript.service
   ; sudo systemctl start myscript.service

# 참고 링크
https://forums.developer.nvidia.com/t/jetson-nano-developer-kit-ubuntu-splash-screen/107984
https://forums.developer.nvidia.com/t/hello-how-can-i-change-the-nvidia-boot-logo-to-my-own/83583/15




## 실행 방법

### 1. 종속성 설치
```bash
pip install -r requirements.txt
```

### 2. 애플리케이션 실행
```bash
python main.py
```

### 3. 구조 테스트 (PyQt5 없이)
```bash
python test_structure.py
```

## 개발자 가이드

### 디버그 모드 설정
디버그 모드는 다음과 같이 설정할 수 있습니다:

1. **자동 설정**: 하드웨어 연결 실패시 자동으로 디버그 모드 활성화
2. **수동 설정**: `config/settings.json` 파일에서 `debug_mode` 값 변경
3. **단축키**: 애플리케이션 실행 중 Ctrl+D로 토글 (재시작 필요)

### 백엔드 서비스 추가
새로운 백엔드 서비스를 추가하려면:

1. `backend/` 폴더에 새 매니저 클래스 생성
2. `backend/backend_manager.py`에 새 서비스 추가
3. 디버그 모드 지원 구현

### 프론트엔드 뷰 추가
새로운 뷰를 추가하려면:

1. `views/` 폴더에 새 뷰 클래스 생성
2. `ui/` 폴더에 해당 UI 파일 추가
3. `main.py`에 뷰 등록 및 연결

### 설정 옵션 추가
새로운 설정을 추가하려면:

1. `config/config.py`의 `Config` 클래스에 새 속성 추가
2. `load_config()` 및 `save_config()` 메서드 업데이트

## 트러블슈팅

### 카메라 연결 문제
- 디버그 모드에서는 가상 카메라가 사용됩니다
- 실제 카메라 연결 실패시 자동으로 디버그 모드로 전환됩니다
- 카메라 권한 확인: `ls -la /dev/video*`

### UART 연결 문제
- 디버그 모드에서는 가상 UART가 사용됩니다
- 권한 문제: `sudo usermod -a -G dialout $USER` 후 재로그인
- 포트 확인: `ls -la /dev/ttyTHS*` 또는 `/dev/ttyUSB*`

### 설정 파일 문제
- 설정 파일 위치: `config/settings.json`
- 파일 삭제 후 재시작하면 기본값으로 재생성됩니다

## 구조적 특징

### 장점
1. **모듈화**: 백엔드와 프론트엔드가 명확히 분리
2. **테스트 용이성**: 디버그 모드로 하드웨어 없이 개발 가능
3. **확장성**: 새로운 백엔드 서비스나 뷰 추가가 쉬움
4. **안정성**: 하드웨어 실패시 자동 복구 메커니즘

### 개선 사항
- 카메라와 UART 모듈이 실제 연결되지 않아도 정상 동작
- 디버그 모드와 실제 하드웨어 모드의 매끄러운 전환
- 시스템 상태 실시간 모니터링
- 통합된 백엔드 서비스 관리
