"""LG 냉장고 DB 로더 — 엑셀을 추천 엔진이 쓰기 좋은 형태로 정규화.
엑셀 파일이 없으면 샘플 데이터로 동작합니다.
"""
import os
import re

DATA_FILE = "LG_냉장고_대표상품기준_통합DB.xlsx"
BASE_DIR = os.path.dirname(__file__)

SOFT_FEATURES = {
    "door_cooling": ("도어쿨링+ (문쪽까지 균일 냉기)", ["도어쿨링"]),
    "uv_filter":    ("UV청정탈취필터+ (냄새·세균 케어)", ["UV청정탈취필터", "퓨어 프레시 필터"]),
    "knock_on":     ("노크온 (두드리면 내부가 보임)", ["노크온"]),
    "magic_space":  ("매직스페이스 (자주 쓰는 식품 빠르게)", ["매직스페이스"]),
    "ai":           ("AI 기능 (자동 절전·신선 케어)", ["AI"]),
    "voice":        ("음성인식", ["음성인식"]),
    "fresh_room":   ("신선맞춤실 (맞춤 보관실)", ["신선맞춤실"]),
    "energy_top":   ("1등급 에너지 효율", []),
}


def _to_int(x):
    import math
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return None
    m = re.search(r"-?\d[\d,]*", str(x))
    return int(m.group(0).replace(",", "")) if m else None


def _width(dim):
    if dim is None or str(dim).strip() in ("", "nan"):
        return None
    nums = re.findall(r"[\d,]+", str(dim))
    return int(nums[0].replace(",", "")) if nums else None


def _dimensions(dim):
    """(W, H, D) 파싱 — '912 x 1790 x 715' 또는 '912x1790x715' 형식."""
    if dim is None or str(dim).strip() in ("", "nan", "-"):
        return None, None, None
    nums = [int(n.replace(",", "")) for n in re.findall(r"[\d,]+", str(dim))]
    return (
        nums[0] if len(nums) > 0 else None,
        nums[1] if len(nums) > 1 else None,
        nums[2] if len(nums) > 2 else None,
    )


def _split(val):
    if val is None or str(val).strip() in ("X", "", "nan"):
        return []
    return [t.strip() for t in re.split(r"[,/]", str(val)) if t.strip() and t.strip() != "X"]


def _dedup(lst: list) -> list:
    """순서를 유지하며 중복 제거."""
    seen: set = set()
    out = []
    for v in lst:
        if v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _make_product(code, name, price_min, price_max, install, doors, total_l,
                  fridge_l, freezer_l, energy, width, size_raw, material,
                  colors, feat_tokens, promo, model_codes=None, image_class=None):
    energy_val = _to_int(energy)
    full_blob = " ".join(feat_tokens) + " " + name
    features = set()
    for key, (_, kws) in SOFT_FEATURES.items():
        if key == "energy_top":
            if energy_val == 1:
                features.add(key)
            continue
        if any(kw in full_blob for kw in kws):
            features.add(key)
    mat_list = _dedup(_split(material)) if material else ["-"]
    return {
        "code": code,
        "name": name,
        "price_min": _to_int(price_min),
        "price_max": _to_int(price_max),
        "install": install,
        "doors": doors,
        "total_l": _to_int(total_l),
        "fridge_l": _to_int(fridge_l),
        "freezer_l": _to_int(freezer_l),
        "energy": energy_val,
        "width": _width(width),
        "dim_h": _dimensions(size_raw)[1],
        "dim_d": _dimensions(size_raw)[2],
        "size_raw": str(size_raw).strip() if size_raw else "-",
        "material": str(material).strip() if material else "-",
        "materials": mat_list,
        "colors": _dedup(colors if isinstance(colors, list) else _split(colors)),
        "model_codes": _dedup(model_codes) if model_codes else [code],
        "features": features,
        "is_ai": "ai" in features,
        "promo": promo if isinstance(promo, list) else [],
        "raw_features": feat_tokens,
        "image_class": str(image_class).strip() if image_class else "",
    }


def _sample_products():
    """엑셀 파일이 없을 때 사용하는 샘플 데이터 (시연용)."""
    return [
        # 빌트인
        _make_product("M301S", "LG 디오스 빌트인 냉장고 M301S", 1_500_000, 1_800_000,
                      "빌트인", "1도어", 310, 310, 0, 1, 540, "540x1770x540", "메탈",
                      ["화이트"], ["도어쿨링", "UV청정탈취필터"], []),
        _make_product("M402S", "LG 디오스 빌트인 냉장고 M402S", 1_800_000, 2_100_000,
                      "빌트인", "2도어", 402, 280, 122, 1, 540, "540x1770x540", "메탈",
                      ["화이트", "실버"], ["도어쿨링"], []),
        # Fit & Max
        _make_product("F402S", "LG 디오스 Fit & Max 냉장고 F402S", 900_000, 1_100_000,
                      "Fit & Max", "2도어", 402, 280, 122, 1, 595, "595x1850x712", "강화유리",
                      ["오브제 베이지"], ["도어쿨링", "매직스페이스"], ["에너지 1등급"]),
        _make_product("F507S", "LG 디오스 Fit & Max 냉장고 F507S", 1_100_000, 1_300_000,
                      "Fit & Max", "2도어", 507, 350, 157, 2, 595, "595x1850x712", "강화유리",
                      ["오브제 그린", "오브제 베이지"], ["도어쿨링", "노크온"], []),
        _make_product("F604S", "LG 디오스 Fit & Max 냉장고 F604S", 1_300_000, 1_500_000,
                      "Fit & Max", "4도어", 604, 422, 182, 1, 910, "910x1850x712", "강화유리",
                      ["오브제 클레이"], ["도어쿨링", "UV청정탈취필터", "신선맞춤실"], ["신선맞춤실"]),
        # 프리스탠딩 — 소용량
        _make_product("B182S", "LG 일반 냉장고 B182", 400_000, 480_000,
                      "프리스탠딩", "2도어", 182, 126, 56, 2, 500, "500x1350x600", "강화유리",
                      ["화이트"], [], []),
        _make_product("B247S", "LG 일반 냉장고 B247", 520_000, 620_000,
                      "프리스탠딩", "2도어", 247, 175, 72, 2, 595, "595x1600x651", "강화유리",
                      ["화이트", "실버"], [], []),
        # 프리스탠딩 — 중용량
        _make_product("S343S", "LG 디오스 냉장고 S343", 700_000, 850_000,
                      "프리스탠딩", "2도어", 343, 245, 98, 1, 595, "595x1740x712", "강화유리",
                      ["오브제 화이트"], ["도어쿨링", "UV청정탈취필터"], ["에너지 1등급"]),
        _make_product("S454S", "LG 디오스 냉장고 S454", 850_000, 1_000_000,
                      "프리스탠딩", "2도어", 454, 321, 133, 1, 595, "595x1850x712", "강화유리",
                      ["오브제 베이지", "오브제 그린"], ["도어쿨링", "노크온"], []),
        _make_product("S527S", "LG 디오스 냉장고 S527", 950_000, 1_150_000,
                      "프리스탠딩", "2도어", 527, 375, 152, 2, 680, "680x1850x760", "강화유리",
                      ["다크 그레이", "화이트"], ["도어쿨링", "매직스페이스"], []),
        # 프리스탠딩 — 대용량 800L+
        _make_product("R870S", "LG 디오스 오브제컬렉션 양문형 냉장고 R870", 2_200_000, 2_600_000,
                      "프리스탠딩", "2도어", 870, 580, 290, 1, 912, "912x1790x715", "강화유리",
                      ["오브제 핑크", "오브제 그린"], ["도어쿨링", "음성인식"], ["양문형"]),
        _make_product("T873S", "LG 디오스 오브제컬렉션 4도어 냉장고 T873", 2_800_000, 3_200_000,
                      "프리스탠딩", "4도어", 873, 560, 313, 1, 912, "912x1790x715", "강화유리",
                      ["오브제 화이트", "오브제 블랙"], ["도어쿨링", "UV청정탈취필터", "노크온", "신선맞춤실"], []),
        _make_product("T921S", "LG 디오스 오브제컬렉션 AI 4도어 냉장고 T921 AI", 3_200_000, 3_800_000,
                      "프리스탠딩", "4도어", 921, 615, 306, 1, 912, "912x1790x715", "강화유리",
                      ["오브제 블루", "오브제 그린"], ["AI", "도어쿨링", "UV청정탈취필터", "노크온", "음성인식", "신선맞춤실"], ["AI"]),
    ]


def load_products(path=None):
    if path is None:
        path = os.path.join(BASE_DIR, DATA_FILE)
    elif not os.path.isabs(path):
        local_path = os.path.join(BASE_DIR, path)
        if os.path.exists(local_path):
            path = local_path

    if not os.path.exists(path):
        return _sample_products(), True  # (products, is_sample)

    try:
        import pandas as pd
        df = pd.read_excel(path)
        products = []
        for _, r in df.iterrows():
            name = str(r["제품명"]).strip()
            feat_tokens = _split(r.get("주요 기능", ""))
            name_blob = name
            full_blob = " ".join(feat_tokens) + " " + name_blob
            energy = _to_int(r.get("에너지 등급"))
            features = set()
            for key, (_, kws) in SOFT_FEATURES.items():
                if key == "energy_top":
                    if energy == 1:
                        features.add(key)
                    continue
                if any(kw in full_blob for kw in kws):
                    features.add(key)
            promo = []
            for col in ["홍보 태그 1", "홍보 태그 2", "홍보 태그 3", "홍보 태그 4", "홍보 태그 5", "홍보 태그 6"]:
                v = r.get(col)
                if v is not None and pd.notna(v) and str(v).strip() not in ("X", ""):
                    promo.append(str(v).strip())
            raw_colors   = _dedup(_split(r.get("색상", "")))
            raw_mats     = _dedup(_split(r.get("도어 재질", "-"))) or ["-"]
            raw_mcodes   = _dedup(_split(r.get("포함 제품 코드", "")))
            rep_code     = str(r["대표 제품 코드"]).strip().strip("'")
            if not raw_mcodes:
                raw_mcodes = [rep_code]
            products.append({
                "code": rep_code,
                "name": name,
                "price_min": _to_int(r.get("최저가")),
                "price_max": _to_int(r.get("최고가")),
                "install": str(r["설치 타입"]).strip(),
                "doors": str(r["도어 개수"]).strip(),
                "total_l": _to_int(r.get("총 용량")),
                "fridge_l": _to_int(r.get("냉장 용량")),
                "freezer_l": _to_int(r.get("냉동 용량")),
                "energy": energy,
                "width": _width(r.get("제품 크기 (WxHxD)")),
                "dim_h": _dimensions(r.get("제품 크기 (WxHxD)"))[1],
                "dim_d": _dimensions(r.get("제품 크기 (WxHxD)"))[2],
                "size_raw": str(r.get("제품 크기 (WxHxD)", "-")).strip(),
                "material": str(r.get("도어 재질", "-")).strip(),
                "materials": raw_mats,
                "colors": raw_colors,
                "model_codes": raw_mcodes,
                "features": features,
                "is_ai": "ai" in features,
                "promo": promo,
                "raw_features": feat_tokens,
                "image_class": (
                    str(r.get("이미지 분류명", "")).strip()
                    if r.get("이미지 분류명") is not None and pd.notna(r.get("이미지 분류명"))
                    else ""
                ),
            })
        return products, False
    except Exception as e:
        print(f"엑셀 로딩 오류: {e}")
        return _sample_products(), True


if __name__ == "__main__":
    ps, is_sample = load_products()
    print(f"{'[샘플]' if is_sample else '[실제]'} {len(ps)}개 제품 로드됨")
    for p in ps[:3]:
        print(p["code"], p["name"], p["install"], p["total_l"], sorted(p["features"]))
