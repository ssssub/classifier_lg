"""
LG 냉장고 추천 백엔드 (SKU 연동 버전)
- 추천은 대표 모델 단위 (로직 동일)
- 결과 카드에서 색상 선택 → 코드/재질/가격 자동 연동
Replit: lg_products_sku.json 과 이 파일을 함께 배포
"""
import json, os

_PATH = os.path.join(os.path.dirname(__file__), "lg_products_sku.json")
with open(_PATH, encoding="utf-8") as f:
    PRODUCTS = json.load(f)

# EDA KMeans 분기점 기반 용량 구간(L)
CAPACITY_BANDS = {"small": (0, 290), "medium": (290, 590), "large": (590, 99999)}

def recommend(answers: dict, limit: int = 5) -> list:
    """answers: install_type / capacity(small|medium|large) /
       energy_grade_max / budget_max / door_count  (전부 optional)"""
    res = []
    for p in PRODUCTS:
        if answers.get("install_type") and p["install_type"] != answers["install_type"]:
            continue
        if answers.get("door_count") and p["door_count"] != answers["door_count"]:
            continue
        if answers.get("energy_grade_max") and p["energy_grade"] and p["energy_grade"] > answers["energy_grade_max"]:
            continue
        if answers.get("budget_max") and p["price_min"] and p["price_min"] > answers["budget_max"]:
            continue
        if answers.get("capacity") and p["capacity_total"]:
            lo, hi = CAPACITY_BANDS[answers["capacity"]]
            if not (lo <= p["capacity_total"] < hi):
                continue
        res.append(p)
    res.sort(key=lambda x: (x["energy_grade"] or 9, x["price_min"] or 9e9))
    return res[:limit]

def get_variant(rep_code: str, color: str) -> dict | None:
    """결과 카드에서 색상 선택 시 호출 → 해당 색상의 코드/재질/가격 반환"""
    for p in PRODUCTS:
        if p["rep_code"] == rep_code:
            for v in p["variants"]:
                if v["color"] == color:
                    return v
    return None

if __name__ == "__main__":
    hits = recommend({"install_type": "프리스탠딩", "capacity": "medium", "energy_grade_max": 2})
    print(f"추천 {len(hits)}개:")
    for h in hits[:3]:
        print(f"  {h['rep_code']} | {h['name']} | {h['capacity_total']:.0f}L | "
              f"{h['energy_grade']}등급 | 색상 {len(h['colors'])}종 {h['colors']}")
    # 색상 연동 테스트
    if hits:
        rep = hits[0]; c = rep["colors"][-1]
        v = get_variant(rep["rep_code"], c)
        print(f"\n[연동] {rep['rep_code']} 에서 '{c}' 선택 → "
              f"코드 {v['code']} / 재질 {v['material']} / {v['price']:,.0f}원")
