# PyCalthReader

PyCalthReader는 PyQt5를 사용하여 개발된 파이썬 애플리케이션입니다. 
이 애플리케이션은 Calth AI 진단 장치를 위한 사용자 인터페이스를 제공하며, 다양한 의료 진단 정보를 표시하고 관리합니다.

## 주요 기능

- 로딩 화면: 애플리케이션 시작 시 진행 상황을 표시
- 홈 화면: 메인 인터페이스 제공
- 테스트 선택 화면: 다양한 진단 테스트 옵션 제공
- 테스트 정보 화면: 선택된 테스트에 대한 상세 정보 표시
- 애플리케이션 정보 화면: 버전, 제작자 등 앱 정보 제공

## 시스템 요구사항

- Python 3.6 이상
- PyQt5
; 설치 : sudo apt-get install python3-pyqt5

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

프로젝트 디렉토리에서 다음 명령어를 실행합니다:

1. 애플리케이션 실행:
   ```
   python main.py
   ```

## 디렉토리 구조

PyCalth_Qt5/

│

├── main.py                          # 메인 애플리케이션 실행 코드

│

├── views/

│    ├── LoadView.py                  # 로딩 화면 뷰

│    ├── HomeView.py                  # 홈 화면 뷰

│    │    ├── OperatorView.py            # 운영자 설정 화면 뷰

│    │    │    ├── [x] CamSetView.py        # 카메라 설정 화면 뷰

│   │   │   ├── [x] SettingsView.py      # 설정 화면 뷰

│   │   │   ├── [x] NetworkView.py       # 네트워크 설정 화면 뷰

│   │   │   └── [x] UpdateView.py        # 업데이트 화면 뷰

│   │   │

│   │   ├── SettingsView.py          # 설정 화면 뷰

│   │   ├── ResultListView.py        # 결과 목록 화면 뷰

│   │   └── InfoView.py              # 애플리케이션 정보 화면 뷰

│   │  

│   ├── SelectView.py                # 테스트 선택 화면 뷰

│   ├── MeasureView.py               # 측정 진행 화면 뷰

│   ├── ResultView.py                # 결과 화면 뷰

│   │

│   ├── VKeyboard.py                 # 가상 키보드 정의한 파일

│   └── Utils.py                     # 날짜/시간 표시 기능등 기타 기능을 정의한 파일

│

├── ui/

│   ├── LoadViewWindow.ui            # 로딩 화면 UI 파일

│   ├── HomeViewWindow.ui            # 홈 화면 UI 파일

│   │   ├── InfoViewWindow.ui          # 애플리케이션 정보 화면 UI 파일

│   │   ├── OperatorViewWindow.ui      # 운영자 정보 화면 UI 파일

│   │   ├── SettingsViewWindow.ui      # 설정 화면 UI 파일

│   │   └── ResultListViewWindow.ui    # 결과 목록 화면 UI 파일

│   │

│   ├── SelectViewWindow.ui          # 테스트 선택 화면 UI 파일

│   ├── TestInfoViewWindow.ui        # 테스트 정보 화면 UI 파일

│   ├── MeasureViewWindow.ui         # 측정 진행 화면 UI 파일

│   ├── ResultViewWindow.ui          # 결과 화면 UI 파일

│   │

│   └── images/                      # 애플리케이션에서 사용되는 이미지 파일들

│

├── fonts/                           # 애플리케이션에서 사용되는 폰트 파일들

│

├── info/

│   ├── info.json                    # 애플리케이션 정보 파일

│   │

│   └── current.json                 # 현재 진단 관련 정보 파일

│

├── history.txt                      # 히스토리

│

└── README.md                        # 프로젝트 설명 및 문서


## UI 파일 구조

- `main.py`: 메인 애플리케이션 코드
- `LoadViewWindow.ui`: 로딩 화면 UI 파일
- `HomeViewWindow.ui`: 홈 화면 UI 파일
-    `OperatorViewWindow.ui`: 운영자 설정 화면 UI 파일
-        `CamSetViewWindow.ui`: 카메라 설정 화면 UI 파일 - 미구현
-        `SettingsViewWindow.ui`: 설정 화면 UI 파일 - 미구현
-        `NetworkViewWindow.ui`: 네트워크 설정 화면 UI 파일 - 미구현
-        `UpdateViewWindow.ui`: 업데이트 화면 UI 파일 - 미구현
-    `ResultListViewWindow.ui`: 결과 목록 화면 UI 파일
-    `InfoViewWindow.ui`: 애플리케이션 정보 화면 UI 파일
- `SelectViewWindow.ui`: 테스트 선택 화면 UI 파일
- `TestInfoViewWindow.ui`: 테스트 정보 화면 UI 파일
- `MeasureViewWindow.ui`: 측정 진행 화면 UI 파일    
- `ResultViewWindow.ui`: 결과 화면 UI 파일

- `info/info.json`: 애플리케이션 정보 파일
- `image/`: 애플리케이션에서 사용되는 이미지 파일들


## json 파일

`info/info.json` 파일은 애플리케이션의 기본 정보를 포함함:
```
{
    "name": "Calth Reader",
    "sn": "C2024090001",
    "version": "1.00.000",
    "description": "Calth AI 진단 장치",
    "author": "Calth.co",
    "last_updated": "2023-09-10"
}
```

`info/current.json` 파일은 현재 진단 관련 정보를 포함함:
```
{
    "test_type0": "Qualitative",
    "test_type1": "Influenza A & B",
    "operator": "CALTH0320",
    "patient_id": "2024090001",
    "datentime": "2024-09-01 12:00:00",
    "control": "Positive",
    "resultb": "POS",
    "resulta": "POS"
}
```


## 단축키

- `Ctrl + Q`: 애플리케이션 종료


## 연락처

문의사항이나 제안사항이 있으시면 [tech@bench-soft.com]으로 연락 주시기 바랍니다.
