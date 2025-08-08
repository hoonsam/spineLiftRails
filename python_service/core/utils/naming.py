import re
import logging

logger = logging.getLogger(__name__)

def clean_name(original_name: str, for_file_system: bool = False) -> str:
    """
    원본 문자열(레이어 이름, 파일 이름 등)에서 Spine 또는 파일 시스템에
    문제를 일으킬 수 있는 문자를 정리하고, 이름을 정규화합니다.

    Args:
        original_name (str): 정리할 원본 이름입니다.
        for_file_system (bool): 파일 시스템용으로 이름을 정리할지 여부입니다.
                                True이면 좀 더 엄격한 규칙(예: 점(.)도 밑줄로 변경)을
                                적용할 수 있습니다. Spine 슬롯/어태치먼트 이름은
                                점을 포함할 수 있습니다.

    Returns:
        str: 정리된 이름입니다. 비어있거나 정리 후 빈 문자열이 되면 "layer" 또는
             "unnamed_file"을 반환합니다.
    """
    if not original_name:
        default_name = "unnamed_file" if for_file_system else "layer"
        logger.debug(f"입력 이름이 비어있어 기본 이름 '{default_name}' 반환")
        return default_name

    # 1. 전각문자를 반각문자로 변환 (일본어/한국어 등의 전각 영숫자를 ASCII로 변환)
    #    전각 알파벳 (Ａ-Ｚ, ａ-ｚ) 및 전각 숫자 (０-９) 처리
    cleaned = original_name
    
    # 전각 대문자 A-Z (U+FF21-U+FF3A) -> 반각 A-Z (U+0041-U+005A)
    for i in range(26):
        fullwidth_char = chr(0xFF21 + i)  # Ａ, Ｂ, Ｃ, ...
        halfwidth_char = chr(0x0041 + i)  # A, B, C, ...
        cleaned = cleaned.replace(fullwidth_char, halfwidth_char)
    
    # 전각 소문자 a-z (U+FF41-U+FF5A) -> 반각 a-z (U+0061-U+007A)
    for i in range(26):
        fullwidth_char = chr(0xFF41 + i)  # ａ, ｂ, ｃ, ...
        halfwidth_char = chr(0x0061 + i)  # a, b, c, ...
        cleaned = cleaned.replace(fullwidth_char, halfwidth_char)
    
    # 전각 숫자 0-9 (U+FF10-U+FF19) -> 반각 0-9 (U+0030-U+0039)
    for i in range(10):
        fullwidth_char = chr(0xFF10 + i)  # ０, １, ２, ...
        halfwidth_char = chr(0x0030 + i)  # 0, 1, 2, ...
        cleaned = cleaned.replace(fullwidth_char, halfwidth_char)
    
    # 자주 사용되는 전각 기호들도 반각으로 변환
    fullwidth_symbols = {
        '　': ' ',   # 전각 공백 -> 반각 공백
        '！': '!',   # 전각 느낌표
        '？': '?',   # 전각 물음표
        '（': '(',   # 전각 괄호
        '）': ')',
        '［': '[',   # 전각 대괄호
        '］': ']',
        '｛': '{',   # 전각 중괄호
        '｝': '}',
        '：': ':',   # 전각 콜론
        '；': ';',   # 전각 세미콜론
        '，': ',',   # 전각 쉼표
        '．': '.',   # 전각 점
        '＿': '_',   # 전각 언더스코어
        '－': '-',   # 전각 하이픈
        '＋': '+',   # 전각 플러스
        '＝': '=',   # 전각 등호
    }
    
    for fullwidth, halfwidth in fullwidth_symbols.items():
        cleaned = cleaned.replace(fullwidth, halfwidth)
    
    if cleaned != original_name:
        logger.debug(f"전각문자 변환: '{original_name}' -> '{cleaned}'")

    # 2. 일반적인 태그 패턴 제거 (예: [bone], [slot], [skin])
    #    태그 내용은 대소문자 구분 없이 영숫자, 밑줄, 공백 포함 가능
    cleaned = re.sub(r'\s*\[\s*[a-zA-Z0-9_\s]+?\s*\]', '', cleaned).strip()
    if cleaned != original_name:
        logger.debug(f"태그 제거: '{original_name}' -> '{cleaned}'")


    # 3. Spine/파일 시스템에서 문제를 일으킬 수 있는 특수 문자들을 밑줄로 대체
    #    - Spine에서 허용되지 않는 일반적인 문자: :, ", /, \, |, ?, *
    #    - 파일 시스템에서 일반적으로 문제되는 문자 포함 (위와 대부분 겹침)
    #    - 공백 문자(whitespace)는 단일 밑줄로
    #    - 점(.)의 처리:
    #        - for_file_system=True: 모든 점을 밑줄로 변경 (확장자도 포함될 수 있으므로 주의)
    #        - for_file_system=False (Spine용): 점 유지 (Spine은 이름에 점 허용)
    
    if for_file_system:
        # 파일 시스템용: 점(.) 포함 모든 특수문자 및 공백을 밑줄로
        cleaned = re.sub(r'[<>:"/\\|?*\s.]+', '_', cleaned)
        logger.debug(f"파일 시스템용 정리 (특수문자,공백,점->'_'): '{original_name}' -> '{cleaned}'")
    else:
        # Spine용: 점(.)은 유지, 다른 특수문자 및 공백은 밑줄로
        cleaned = re.sub(r'[<>:"/\\|?*\s]+', '_', cleaned)
        logger.debug(f"Spine용 정리 (특수문자,공백->'_', 점 유지): '{original_name}' -> '{cleaned}'")

    # 4. 연속된 밑줄(underscore)을 하나로 합침
    cleaned = re.sub(r'_+', '_', cleaned)

    # 5. 이름 앞뒤의 밑줄 제거
    cleaned = cleaned.strip('_')

    # 6. 정리 후 이름이 비어있으면 기본값 사용
    if not cleaned:
        default_name = "unnamed_file" if for_file_system else "layer"
        logger.warning(f"정리 후 이름이 비어있어 기본 이름 '{default_name}' 사용 (원본: '{original_name}')")
        return default_name
    
    if cleaned != original_name: # 최종적으로 변경된 경우만 로깅 (단, 위에서 단계별 로깅을 했으므로 여기선 info 레벨로)
        logger.info(f"이름 정리 최종: 원본='{original_name}', 정리본='{cleaned}', 파일시스템용={for_file_system}")

    return cleaned

if __name__ == '__main__':
    # 로깅 설정 (테스트용)
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 테스트 케이스
    names_to_test = [
        "Layer 1", "Layer [bone] 2", "  layer with spaces  ",
        "name:with:colons", "file/with/slashes", "star*char",
        "a_b_c", "___d___", ".leadingdot", "trailingdot.", "middle.dot.name",
        "", None, "[slot]", "_[skin]_", "   ", "very_long_name_with_many_underscores_and_spaces",
        "image.001.png", "image.ver2.jpg (Copy)", "레이어 [태그] 이름.확장자",
        # 전각문자 테스트 케이스 추가
        "water_Ｂ", "hair_Ｆ１", "ＡＢＣ１２３", "ａｂｃ", "Ｈａｉｒ＿Ｂ２",
        "レイヤー（水着）", "全角　文字", "Ａ－Ｂ＋Ｃ＝Ｄ", "ＸＹＺ０９８"
    ]

    print("--- Spine 이름 정리 테스트 (for_file_system=False) ---")
    for name_input in names_to_test:
        if name_input is None: # 실제 사용 시에는 타입 힌트로 None 방지
            print(f"입력: {name_input} -> 에러 또는 기본값 처리 필요 (여기선 스킵)")
            continue
        print(f"입력: \"{name_input}\" -> 정리: \"{clean_name(name_input, for_file_system=False)}\"")

    print("\n--- 파일 시스템 이름 정리 테스트 (for_file_system=True) ---")
    for name_input in names_to_test:
        if name_input is None:
            print(f"입력: {name_input} -> 에러 또는 기본값 처리 필요 (여기선 스킵)")
            continue
        print(f"입력: \"{name_input}\" -> 정리: \"{clean_name(name_input, for_file_system=True)}\"")

    # 특정 케이스 추가 테스트
    print("\n--- 추가 테스트 ---")
    test_name = "skirt_R5"
    print(f"Spine: \"{test_name}\" -> \"{clean_name(test_name, False)}\"")
    print(f"File:  \"{test_name}\" -> \"{clean_name(test_name, True)}\"")
    test_name_with_tag = "skirt [details] R5.png"
    print(f"Spine: \"{test_name_with_tag}\" -> \"{clean_name(test_name_with_tag, False)}\"")
    print(f"File:  \"{test_name_with_tag}\" -> \"{clean_name(test_name_with_tag, True)}\"") 