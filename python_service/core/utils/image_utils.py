"""
Image Processing Utilities
이미지 자르기, 패딩 추가 등과 같은 일반적인 이미지 처리 함수를 제공합니다.
"""
import logging
from typing import Optional, Tuple
from PIL import Image # type: ignore

logger = logging.getLogger(__name__)

def trim_transparent_borders(image: Image.Image) -> Image.Image:
    """이미지 가장자리의 완전 투명한 영역을 제거합니다 (트림).

    Args:
        image (Image.Image): PIL Image 객체 (RGBA 모드여야 함).

    Returns:
        Image.Image: 트림된 PIL Image 객체. 트림할 영역이 없거나 RGBA 모드가 아니면 원본 이미지 반환.
    """
    if image.mode != 'RGBA':
        logger.debug(f"이미지 트림 건너뜀: RGBA 모드 아님 (현재: {image.mode}).")
        return image
    
    bbox: Optional[Tuple[int, int, int, int]] = image.getbbox()
    if bbox:
        trimmed_image = image.crop(bbox)
        if image.size != trimmed_image.size:
            logger.debug(f"이미지 트림됨: 원본 {image.size}, 새크기 {trimmed_image.size}, bbox {bbox}")
        else:
            logger.debug(f"이미지 트림 시도했으나 변경 없음 (bbox: {bbox}).")
        return trimmed_image
    
    logger.debug("이미지 트림 건너뜀: 내용 없음 (getbbox is None).")
    return image

def add_padding_to_image(image: Image.Image, padding: int) -> Image.Image:
    """이미지 모든 가장자리에 지정된 크기의 투명 패딩을 추가합니다.

    Args:
        image (Image.Image): 패딩을 추가할 PIL Image 객체.
        padding (int): 추가할 패딩 크기 (픽셀).

    Returns:
        Image.Image: 패딩이 추가된 PIL Image 객체. 패딩 값이 0 이하면 원본 이미지 반환.
    """
    if padding <= 0:
        return image
    
    new_width: int = image.width + padding * 2
    new_height: int = image.height + padding * 2
    
    # 새 이미지를 생성할 때 원본 이미지의 모드를 유지하려고 시도
    # 단, 투명 패딩을 위해서는 RGBA가 강제될 수 있음
    mode_to_use = image.mode
    if mode_to_use not in ['RGBA', 'LA']: # 알파 채널이 없는 모드면 RGBA로 강제
        logger.debug(f"패딩 추가 시 이미지 모드 {mode_to_use} -> RGBA로 변경 (투명도 지원 위해)")
        mode_to_use = 'RGBA'
        # 원본 이미지를 RGBA로 변환하여 paste할 때 색상 왜곡 방지
        image_to_paste = image.convert('RGBA')
    else:
        image_to_paste = image

    padded_image: Image.Image = Image.new(mode_to_use, (new_width, new_height), (0,0,0,0)) # 투명 배경
    padded_image.paste(image_to_paste, (padding, padding))
    logger.debug(f"이미지 ({image.size}, mode={image.mode})에 {padding}px 패딩 추가. 새 크기: {padded_image.size}, 새 모드: {padded_image.mode}")
    return padded_image 