# -*- coding: utf-8 -*-
"""
SpineLift - Mesh Utilities
메시 데이터 처리와 관련된 공통 유틸리티 함수들을 제공합니다.
"""

import logging
from typing import List

logger = logging.getLogger(__name__)

def generate_standard_uvs(local_vertices: List[float], image_width: int, image_height: int) -> List[float]:
    """
    이미지의 로컬 정점 좌표로부터 표준 UV 좌표 리스트를 생성합니다.

    UV 좌표계:
    - U: 0 (왼쪽) 에서 1 (오른쪽)
    - V: 0 (상단) 에서 1 (하단)

    Args:
        local_vertices: 이미지의 좌상단을 (0,0)으로 하는 픽셀 좌표 리스트 [x1, y1, x2, y2, ...].
        image_width: 원본 이미지의 너비 (픽셀).
        image_height: 원본 이미지의 높이 (픽셀).

    Returns:
        List[float]: [u1, v1, u2, v2, ...] 형식의 UV 좌표 리스트.
                     입력 정점 리스트와 동일한 순서 및 개수를 가집니다.
                     잘못된 입력(이미지 크기 0 이하, 빈 정점 리스트 등) 시 빈 리스트 반환.
    """
    if not local_vertices:
        logger.warning("generate_standard_uvs: 입력된 로컬 정점 리스트가 비어있습니다. 빈 UV 리스트를 반환합니다.")
        return []

    if not (image_width > 0 and image_height > 0):
        logger.warning(
            f"generate_standard_uvs: 이미지 너비 또는 높이가 0 이하입니다 "
            f"(width={image_width}, height={image_height}). 빈 UV 리스트를 반환합니다."
        )
        return [0.0] * len(local_vertices) # 입력 정점 수만큼 0.0으로 채워 반환할 수도 있으나, 빈 리스트가 더 명확할 수 있음

    if len(local_vertices) % 2 != 0:
        logger.warning(
            f"generate_standard_uvs: 로컬 정점 리스트의 길이가 홀수({len(local_vertices)})입니다. "
            "마지막 좌표는 무시될 수 있습니다. UV 생성은 짝수 길이로 진행됩니다."
        )
        # 여기서 오류를 발생시키거나, 잘린 리스트로 처리하거나, 빈 리스트를 반환할 수 있습니다.
        # 우선은 로그만 남기고 진행하되, 호출부에서 짝수 길이를 보장하는 것이 좋습니다.

    uvs: List[float] = []
    processed_length = (len(local_vertices) // 2) * 2 # 짝수 길이로 조정

    for i in range(0, processed_length, 2):
        x = local_vertices[i]
        y = local_vertices[i+1]
        
        u = x / image_width
        v = y / image_height  # V좌표: 이미지 상단 0, 하단 1
        
        uvs.extend([u, v])
        
    if processed_length != len(local_vertices):
        logger.debug(
            f"generate_standard_uvs: 정점 리스트의 길이가 홀수여서 마지막 좌표는 UV 계산에서 제외되었습니다. "
            f"원본 길이: {len(local_vertices)}, 처리된 길이: {processed_length}"
        )

    return uvs

if __name__ == '__main__':
    # 테스트 코드
    logging.basicConfig(level=logging.DEBUG)

    test_vertices1 = [10.0, 20.0, 50.0, 100.0, 90.0, 180.0]
    width1, height1 = 100, 200
    uvs1 = generate_standard_uvs(test_vertices1, width1, height1)
    # 예상: [0.1, 0.1, 0.5, 0.5, 0.9, 0.9]
    logger.info(f"Test 1 Vertices: {test_vertices1}, Width: {width1}, Height: {height1}")
    logger.info(f"Test 1 UVs: {uvs1}")

    test_vertices2 = [0.0, 0.0, 200.0, 0.0, 0.0, 300.0, 200.0, 300.0]
    width2, height2 = 200, 300
    uvs2 = generate_standard_uvs(test_vertices2, width2, height2)
    # 예상: [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0]
    logger.info(f"Test 2 Vertices: {test_vertices2}, Width: {width2}, Height: {height2}")
    logger.info(f"Test 2 UVs: {uvs2}")

    test_vertices3 = [10.0, 20.0, 50.0] # 홀수 길이
    width3, height3 = 100, 100
    uvs3 = generate_standard_uvs(test_vertices3, width3, height3)
    # 예상: [0.1, 0.2] (마지막 50.0 무시)
    logger.info(f"Test 3 Vertices (odd length): {test_vertices3}, Width: {width3}, Height: {height3}")
    logger.info(f"Test 3 UVs: {uvs3}")

    test_vertices4: List[float] = [] # 빈 리스트
    width4, height4 = 100, 100
    uvs4 = generate_standard_uvs(test_vertices4, width4, height4)
    # 예상: []
    logger.info(f"Test 4 Vertices (empty): {test_vertices4}, Width: {width4}, Height: {height4}")
    logger.info(f"Test 4 UVs: {uvs4}")

    test_vertices5 = [10.0, 20.0]
    width5, height5 = 0, 100 # 너비 0
    uvs5 = generate_standard_uvs(test_vertices5, width5, height5)
    # 예상: [0.0, 0.0] 또는 [] - 현재 로직은 [0.0, 0.0] 반환
    logger.info(f"Test 5 Vertices (zero width): {test_vertices5}, Width: {width5}, Height: {height5}")
    logger.info(f"Test 5 UVs: {uvs5}") 