"""LG 냉장고 DB 로더 — 원본 엑셀을 추천 엔진이 쓰기 좋은 형태로 정규화."""
import re
import pandas as pd

DATA_FILE = "LG_냉장고_대표상품기준_통합DB.xlsx"

# 추가기능(Q4)에서 +1점으로 평가할 소프트 기능들.
# key = 내부 식별자, value = (표시 라벨, 매칭 키워드 리스트)
SOFT_FEATURES = {
    "door_cooling": ("도어쿨링+ (문쪽까지 균일 냉기)", ["도어쿨링"]),
    "uv_filter":    ("UV청정탈취필터+ (냄새·세균 케어)", ["UV청정탈취필터", "퓨어 프레시 필터"]),
    "knock_on":     ("노크온 (두드리면 내부가 보임)", ["노크온"]),
    "magic_space":  ("매직스페이스 (자주 쓰는 식품 빠르게)", ["매직스페이스"]),
    "ai":           ("AI 기능 (자동 절전·신선 케어)", ["AI"]),
    "voice":        ("음성인식", ["음성인식"]),
    "fresh_room":   ("신선맞춤실 (맞춤 보관실)", ["신선맞춤실"]),
    "energy_top":   ("1등급 에너지 효율", []),  # 에너지 등급으로 별도 판정
}


def _to_int(x):
    if pd.isna(x):
        return None
    m = re.search(r"-?\d[\d,]*", str(x))
    return int(m.group(0).replace(",", "")) if m else None


def _width(dim):
    """제품 크기 'W x H x D' 에서 폭(W, mm)만 추출."""
    if pd.isna(dim):
        return None
    nums = re.findall(r"[\d,]+", str(dim))
    return int(nums[0].replace(",", "")) if nums else None


def _split(val):
    """콤마/슬래시로 구분된 셀을 토큰 리스트로."""
    if pd.isna(val) or str(val).strip() in ("X", ""):
        return []
    return [t.strip() for t in re.split(r"[,/]", str(val)) if t.strip() and t.strip() != "X"]


def load_products(path=DATA_FILE):
    df = pd.read_excel(path)
    products = []
    for _, r in df.iterrows():
        name = str(r["제품명"]).strip()
        feat_tokens = _split(r["주요 기능"])
        # 제품명에도 기능 단서가 있음 (AI / 매직스페이스 / 노크온 등)
        name_blob = name
        full_blob = " ".join(feat_tokens) + " " + name_blob

        energy = _to_int(r["에너지 등급"])  # '1등급' -> 1

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
            if pd.notna(v) and str(v).strip() not in ("X", ""):
                promo.append(str(v).strip())

        products.append({
            "code": str(r["대표 제품 코드"]).strip().strip("'"),
            "name": name,
            "price_min": _to_int(r["최저가"]),
            "price_max": _to_int(r["최고가"]),
            "install": str(r["설치 타입"]).strip(),       # 빌트인 / Fit & Max / 프리스탠딩
            "doors": str(r["도어 개수"]).strip(),           # 1~4도어
            "total_l": _to_int(r["총 용량"]),
            "fridge_l": _to_int(r["냉장 용량"]),
            "freezer_l": _to_int(r["냉동 용량"]),
            "energy": energy,
            "width": _width(r["제품 크기 (WxHxD)"]),
            "size_raw": str(r["제품 크기 (WxHxD)"]).strip(),
            "material": str(r["도어 재질"]).strip(),
            "colors": _split(r["색상"]),
            "features": features,
            "is_ai": "ai" in features,
            "promo": promo,
            "raw_features": feat_tokens,
        })
    return products


if __name__ == "__main__":
    ps = load_products()
    print(f"{len(ps)} products loaded")
    for p in ps[:3]:
        print(p["code"], p["name"], p["install"], p["total_l"], p["doors"],
              f"{p['price_min']:,}~{p['price_max']:,}", sorted(p["features"]))
