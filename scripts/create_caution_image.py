#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Caution 이미지 생성 스크립트
"""

import os
from PIL import Image, ImageDraw, ImageFont
import sys

def create_caution_image():
    """경고 이미지를 생성합니다."""
    # 이미지 크기 설정 (16:9 비율로 480x100에 맞춤)
    width = 480
    height = 100
    
    # 이미지 생성
    img = Image.new('RGB', (width, height), color='#fff3e0')
    draw = ImageDraw.Draw(img)
    
    # 경고 테두리 그리기
    border_color = '#ff9800'
    border_width = 3
    draw.rectangle([border_width//2, border_width//2, 
                   width-border_width//2-1, height-border_width//2-1], 
                   outline=border_color, width=border_width)
    
    # 경고 아이콘과 텍스트
    try:
        # 시스템 폰트 사용
        font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
        font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 16)
    except:
        # 기본 폰트 사용
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # 경고 아이콘
    warning_icon = "⚠️"
    text_color = '#e65100'
    
    # 텍스트 위치 계산
    icon_bbox = draw.textbbox((0, 0), warning_icon, font=font_large)
    icon_width = icon_bbox[2] - icon_bbox[0]
    icon_height = icon_bbox[3] - icon_bbox[1]
    
    text = "CAUTION"
    text_bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    # 전체 텍스트 너비
    total_width = icon_width + 20 + text_width + 20 + icon_width
    
    # 중앙 정렬
    start_x = (width - total_width) // 2
    y = (height - max(icon_height, text_height)) // 2
    
    # 왼쪽 경고 아이콘
    draw.text((start_x, y), warning_icon, fill=text_color, font=font_large)
    
    # CAUTION 텍스트
    text_x = start_x + icon_width + 20
    draw.text((text_x, y), text, fill=text_color, font=font_large)
    
    # 오른쪽 경고 아이콘
    right_icon_x = text_x + text_width + 20
    draw.text((right_icon_x, y), warning_icon, fill=text_color, font=font_large)
    
    return img

def main():
    """메인 함수"""
    try:
        # 현재 스크립트 위치에서 프로젝트 루트 찾기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        
        # 이미지 저장 경로
        image_dir = os.path.join(project_root, 'ui', 'image')
        os.makedirs(image_dir, exist_ok=True)
        
        image_path = os.path.join(image_dir, 'caution_img.png')
        
        # 이미지 생성 및 저장
        img = create_caution_image()
        img.save(image_path, 'PNG')
        
        print(f"Caution 이미지가 생성되었습니다: {image_path}")
        
    except Exception as e:
        print(f"이미지 생성 중 오류 발생: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
