# PyCalthReader

PyCalthReader는 PyQt5를 사용하여 개발된 의료진단장비용 파이썬 애플리케이션입니다. 
**MVC(Model-View-Controller) 패턴**을 적용하여 구조적으로 분리되었으며, 디버그 모드를 지원하여 개발과 실제 운영 환경을 구분할 수 있습니다.

## 프로젝트 구조 (MVC 패턴)

```
calth_reader/
├── main.py                 # 메인 애플리케이션 진입점
├── requirements.txt        # 패키지 의존성
├── README.md              # 프로젝트 문서
├── config/                # 설정 관리
│   ├── config.py          # 애플리케이션 설정
│   └── settings.json      # 설정 파일 (자동 생성)
├── models/                # MVC - Model 레이어
│   ├── __init__.py        # 모델 패키지
│   ├── application_model.py # 애플리케이션 상태 모델
│   ├── camera_model.py    # 카메라 데이터 모델
│   └── uart_model.py      # UART 통신 모델
├── views/                 # MVC - View 레이어
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
├── controllers/           # MVC - Controller 레이어
│   ├── __init__.py        # 컨트롤러 패키지
│   ├── application_controller.py # 메인 애플리케이션 컨트롤러
│   └── measurement_controller.py # 측정 프로세스 컨트롤러
├── services/              # 서비스 레이어 (하드웨어 인터페이스)
│   ├── __init__.py        # 서비스 패키지
│   ├── camera_service.py  # 카메라 하드웨어 제어
│   └── uart_service.py    # UART 하드웨어 제어
├── ui/                    # UI 파일들
│   └── *.ui              # Qt Designer 파일들
├── fonts/                 # 폰트 파일들
├── info/                  # 정보 파일들
└── ...
```

## MVC 패턴 적용

### Model (모델)
- **데이터와 비즈니스 로직 담당**
- `models/application_model.py`: 애플리케이션 전체 상태 관리
- `models/camera_model.py`: 카메라 프레임 및 설정 데이터
- `models/uart_model.py`: UART 통신 및 LED 제어 데이터
- **옵저버 패턴 적용**: 데이터 변경시 자동으로 컨트롤러에 알림

### View (뷰)
- **사용자 인터페이스 담당**
- PyQt5 기반 UI 컴포넌트들
- 사용자 입력을 컨트롤러로 전달
- 컨트롤러로부터 받은 데이터를 화면에 표시

### Controller (컨트롤러)
- **Model과 View 사이의 중재자**
- `controllers/application_controller.py`: 전체 애플리케이션 흐름 제어
- `controllers/measurement_controller.py`: 측정 프로세스 제어
- 사용자 입력 처리 및 비즈니스 로직 실행

### Service (서비스)
- **하드웨어 및 외부 시스템 인터페이스**
- `services/camera_service.py`: 실제/가상 카메라 제어
- `services/uart_service.py`: 실제/가상 UART 통신
- 디버그 모드와 실제 하드웨어 모드 지원

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

# 자동 실행관련 재정의
 1. 기존 서비스 파일 확인 
 ```bash
  $ cat ~/PyCalth.service
  # 서비스 활성화
  sudo systemctl enable PyCalth.service
  sudo systemctl restart PyCalth.service
  # 상태 확인
  systemctl status PyCalth.service
  # 로그 확인
  journalctl -u PyCalth.service -n 100 --no-pager
 ```

 2. 기존 서비스 파일 내용
  [Unit]
  Description=Main Python Script
  After=network.target

  [Service]
  Environment=XDG_RUNTIME_DIR=/run/user/1000
  Environment=PYTHONUNBUFFERED=1
  Environment=XAUTHORITY=/home/calth/.Xauthority
  Environment=DISPLAY=:0
  ExecStart=/home/calth/calth_reader/py369/bin/python3 /home/calth/calth_reader/main.py
  WorkingDirectory=/home/calth/calth_reader
  StandardOutput=inherit
  StandardError=inherit
  Restart=on-failure
  RestartSec=10
  User=calth
  Group=calth

  [Install]
  WantedBy=multi-user.target

 3. 서비스파일 상태 확인
```bash
  systemctl status PyCalth.service
```
  ############## 상태 출력 예시 ##############
  ● PyCalth.service - Calth Reader Main Script
     Loaded: loaded (/etc/systemd/system/PyCalth.service; enabled; vendor preset: enabled)
     Active: activating (auto-restart) (Result: exit-code) since Wed 2025-12-31 10:45:38 KST; 651ms ago
    Process: 8151 ExecStart=/home/calth/calth_reader/py369/bin/python3 /home/calth/calth_reader/main.py (code=exite
   Main PID: 8151 (code=exited, status=203/EXEC)
  ######################################### 

 4. 파이썬 설치 위치 확인
```bash 
  which python3
  /usr/bin/python3
```

 5. 서비스파일 수정
  $ sudo nano /etc/systemd/system/PyCalth.service

  ExecStart=/home/calth/calth_reader/py369/bin/python3 /home/calth/calth_reader/main.py 를

  ExecStart=/usr/bin/python3 /home/calth/calth_reader/main.py
  
  ############## 서비스파일 내용 ##############
  [Unit]
  Description=Calth Reader Application
  After=network.target graphical.target

  [Service]
  Type=simple
  User=calth
  Group=calth
  WorkingDirectory=/home/calth/calth_reader

  ExecStart=/usr/bin/python3 /home/calth/calth_reader/main.py

  Environment=PYTHONUNBUFFERED=1
  Environment=DISPLAY=:0
  Environment=XAUTHORITY=/home/calth/.Xauthority

  Restart=always
  RestartSec=5

  [Install]
  WantedBy=graphical.target
  #########################################

 6. systemd 재적용
```bash
  sudo systemctl daemon-reexec
  sudo systemctl daemon-reload
  sudo systemctl restart PyCalth.service
  sudo systemctl stop PyCalth.service
```

 7. 상태확인
```bash 
  systemctl status PyCalth.service 
```

 8. 프로그램 실행후 ssh 접속후 콘솔단 로그 확인
```bash  
  journalctl -u PyCalth.service -f 
```



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
- 카메라 포맷 확인을 위해 설치.
```bash
sudo apt update
sudo apt install -y v4l-utils
v4l2-ctl --list-formats-ext -d /dev/video0
v4l2-ctl -d /dev/video0 --all
```

# Argus 데몬 확인
```bash
ps aux | grep nvargus-daemon
```

# 카메라 단독 테스트
```bash
gst-launch-1.0 nvarguscamerasrc ! nvvidconv ! autovideosink
```

# CSI 카메라 연결 확인
```bash
ls /dev/video*
```

### UART 연결 문제
- 디버그 모드에서는 가상 UART가 사용됩니다
- 권한 문제: `sudo usermod -a -G dialout $USER` 후 재로그인
- 포트 확인: `ls -la /dev/ttyTHS*` 또는 `/dev/ttyUSB*`
- LED 연동
```bash
ls -l /dev/ttyTHS1
# 예상 출력 : crw-rw---- 1 root dialout ... /dev/ttyTHS1
calth@calth-00003:~/calth_reader$ ls -la /dev/ttyTHS*
crw--w---- 1 root tty     238, 1 12월 31 15:50 /dev/ttyTHS1  <= 이걸로 사용해야됩니다.
crw-rw---- 1 root dialout 238, 2 12월 31 15:49 /dev/ttyTHS2  
# 사용자 그룹 추가
sudo usermod -a -G dialout $USER
```



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


### QR 관련 패키지 설치
```bash
# 시스템 라이브러리 설치
sudo apt-get update
sudo apt-get install libzbar0
# Python 라이브러리 설치
pip install pyzbar
# 또는
# pip3 install pyzbar
# Jetson 환경에서 pip 미설치 및 설치 오류시 아래 수행.
# 기존 깨진 pip 관련 패키지 정리
sudo apt-get remove -y python3-pip python-pip python-pip-whl
sudo apt-get autoremove -y
sudo apt-get clean
# 필수 Python 패키지 수동 설치
sudo apt-get update
sudo apt-get install -y \
    python3-distutils \
    python3-setuptools \
    python3-wheel \
    curl
# python3-distutils 가 없으면 get-pip.py 실패합니다
# get-pip.py로 pip3 강제 설치
curl -sS https://bootstrap.pypa.io/pip/3.6/get-pip.py -o get-pip.py
sudo python3 get-pip.py
# 설치확인
pip3 --version
# pyzbar 설치
pip3 install pyzbar
# zbar 연동 확인 테스트
python3 - << 'EOF'
from pyzbar import pyzbar
print("pyzbar OK")
EOF
# DataMatrix (ECC200) 설치.
sudo apt update
sudo apt install -y libdmtx0a libdmtx-dev
# 정상 설치 확인
ldconfig -p | grep dmtx
# libdmtx.so  또는  libdmtx.so.0 확인
pip3 install pylibdmtx
```

### Jetson 카메라 외부 원격 확인(VLC 이용)
1. 우분투 스트리밍 설정
host=[확인하고자 하는 로컬PC IP]
```bash
# RTP
gst-launch-1.0 -v nvarguscamerasrc ! \
'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
nvvidconv ! \
'video/x-raw,format=I420' ! \
x264enc tune=zerolatency speed-preset=ultrafast bitrate=2000 key-int-max=30 ! \
rtph264pay config-interval=1 pt=96 ! \
udpsink host=192.168.0.250 port=5000 sync=false

# MPEG-TS
gst-launch-1.0 nvarguscamerasrc ! \
'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1' ! \
nvvidconv ! \
'video/x-raw,format=I420' ! \
x264enc tune=zerolatency speed-preset=ultrafast bitrate=2000 ! \
mpegtsmux ! \
udpsink host=192.168.0.250 port=5000 sync=false
```

2. 예 : Mac -> sdp 파일 생성(터미널 사용)
```bash
cat <<EOF > jetson.sdp
v=0
o=- 0 0 IN IP4 192.168.0.250
s=JetsonCam
c=IN IP4 192.168.0.250
t=0 0
m=video 5000 RTP/AVP 96
a=rtpmap:96 H264/90000
a=fmtp:96 packetization-mode=1
EOF
```

3. 카메라 영상 확인.
 - vlc 실행 -> 파일 오픈 -> .sdp 파일 선택
 - 터미널 : jetson.sdp 파일이 위치한 곳에서
```bash
open -a VLC jetson.sdp
# OR MPEG-TS 면 sdp 필요없음.
open -a VLC udp://@:5000
# OR (VLC 캐시 문제 방지)
open -a VLC --args --network-caching=0 udp://@:5000
```

