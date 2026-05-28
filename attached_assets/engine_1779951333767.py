"""상담 엔진 — 설계된 트리(베스트샵 매니저 스크립트)를 그대로 따라가는 추천 로직.

흐름: Q1 설치형태 → Q2 가구원수+요리습관(→용량) → [800L+면 Q2-1 도어방식]
      → Q3 설치공간(폭) → Q4 추가기능(소프트 점수) → 결과
매니저처럼, 후보가 1개로 좁혀지면 남은 질문은 건너뜀.
"""
from data_loader import SOFT_FEATURES

# ── 용량 티어 (총 용량 L 기준) ──
def tier_index(total_l):
    if total_l is None:
        return None
    if total_l < 200:  return 1   # 100L대
    if total_l < 300:  return 2   # 200L대
    if total_l < 400:  return 3   # 300L대
    if total_l < 500:  return 4   # 400L대
    if total_l < 600:  return 5   # 500L대
    if total_l < 800:  return 6   # 600~700L대
    return 7                       # 800L+

TIER_LABEL = {1: "100L대", 2: "200L대", 3: "300L대", 4: "400L대",
              5: "500L대", 6: "600~700L대", 7: "800L+ 대용량"}

# (가구원, 요리습관) → 목표 티어
LIFESTYLE_TIER = {
    ("solo", "none"): 1, ("solo", "sometimes"): 2, ("solo", "often"): 3, ("solo", "love"): 3,
    ("two", "none"): 4,  ("two", "sometimes"): 4,  ("two", "often"): 5,  ("two", "love"): 6,
    ("family", "none"): 7, ("family", "sometimes"): 7, ("family", "often"): 7, ("family", "love"): 7,
}

HOUSEHOLD_OPTS = [("solo", "혼자 살아요"), ("two", "둘이 살아요"), ("family", "3~4인 이상 가족이에요")]
COOKING_OPTS = [
    ("none", "거의 안 해요 (배달·간편식 위주)"),
    ("sometimes", "가끔 해요"),
    ("often", "자주 해요"),
    ("love", "요리를 즐겨요 (식재료를 많이 둬요)"),
]
INSTALL_OPTS = [
    ("빌트인", "빌트인 — 가구장에 완전히 통합", "주방 가구와 한 몸처럼 보이게"),
    ("Fit & Max", "Fit & Max — 가구장에 딱 맞게", "기존 가구 사이에 빈틈 없이"),
    ("프리스탠딩", "프리스탠딩 — 자유롭게 어디든", "원하는 자리에 자유롭게 설치"),
]


def _by_install(products, install):
    return [p for p in products if p["install"] == install]


def _target_in_install(products, install, target_tier):
    """해당 설치타입에서 목표 티어 후보. 없으면 가장 가까운 티어로 폴백."""
    pool = _by_install(products, install)
    exact = [p for p in pool if tier_index(p["total_l"]) == target_tier]
    if exact:
        return exact, target_tier
    # 폴백: 가장 가까운 티어
    tiers = sorted({tier_index(p["total_l"]) for p in pool if tier_index(p["total_l"])})
    if not tiers:
        return pool, target_tier
    nearest = min(tiers, key=lambda t: abs(t - target_tier))
    return [p for p in pool if tier_index(p["total_l"]) == nearest], nearest


def filter_candidates(products, ans):
    """현재까지의 답변으로 하드 필터된 후보 + 적용된 목표티어 반환."""
    c = list(products)
    applied_tier = None

    if ans.get("install"):
        c = _by_install(c, ans["install"])

    # 빌트인은 용량 질문을 건너뛰므로 라이프스타일 필터 미적용
    if ans.get("install") != "빌트인" and ans.get("household") and ans.get("cooking"):
        tt = LIFESTYLE_TIER[(ans["household"], ans["cooking"])]
        c, applied_tier = _target_in_install(c, ans["install"], tt)

    # Q2-1: 800L+ 도어 방식
    if ans.get("door_style"):
        ds = ans["door_style"]
        if ds == "양문형":
            c = [p for p in c if p["doors"] == "2도어"]
        elif ds == "4도어_no_ai":
            c = [p for p in c if p["doors"] == "4도어" and not p["is_ai"]]
        elif ds == "4도어_ai":
            c = [p for p in c if p["doors"] == "4도어" and p["is_ai"]]

    # Q3: 설치 공간(폭)
    if ans.get("space") == "slim":
        slim = [p for p in c if p["width"] and p["width"] <= 600]
        if slim:
            c = slim
    return c, applied_tier


def needs_door_style(candidates, ans):
    """800L+ 대용량으로 좁혀졌고, 도어 방식이 후보를 실제로 나눌 때만 Q2-1."""
    if ans.get("install") != "프리스탠딩":
        return False
    big = [p for p in candidates if tier_index(p["total_l"]) == 7]
    if len(big) < 2:
        return False
    styles = set()
    for p in big:
        if p["doors"] == "2도어":
            styles.add("양문형")
        elif p["doors"] == "4도어":
            styles.add("4도어_ai" if p["is_ai"] else "4도어_no_ai")
    return len(styles) >= 2


def needs_space(candidates):
    """폭이 후보를 실제로 가를 때만 Q3을 물음."""
    widths = [p["width"] for p in candidates if p["width"]]
    return any(w <= 600 for w in widths) and any(w > 600 for w in widths)


def available_soft_features(candidates):
    """후보 중 최소 1개가 가진 추가기능만 (있지도 않은 기능은 안 물어봄)."""
    present = set()
    for p in candidates:
        present |= p["features"]
    return [(k, SOFT_FEATURES[k][0]) for k in SOFT_FEATURES if k in present]


def score_and_rank(candidates, ans):
    """추가기능 선택분으로 +1점씩. 동점이면 에너지효율↑·가격↓로 정렬."""
    wanted = set(ans.get("wanted_features", []))
    ranked = []
    for p in candidates:
        hit = wanted & p["features"]
        score = len(hit)
        ranked.append((score, p, hit))
    ranked.sort(key=lambda t: (
        -t[0],
        t[1]["energy"] if t[1]["energy"] else 9,
        t[1]["price_min"] if t[1]["price_min"] else 10**9,
    ))
    return ranked


# ── 다음에 물어볼 질문 결정 (트리 순서 + 좁혀지면 건너뛰기) ──
def next_question(products, ans):
    if "install" not in ans:
        return "install"
    cand, _ = filter_candidates(products, ans)
    if len(cand) <= 1:
        return "result"

    if ans.get("install") != "빌트인":
        if "household" not in ans:
            return "household"
        if "cooking" not in ans:
            return "cooking"
        cand, _ = filter_candidates(products, ans)
        if len(cand) <= 1:
            return "result"
        if "door_style" not in ans and needs_door_style(cand, ans):
            return "door_style"

    if "space" not in ans and needs_space(cand):
        return "space"
    if "wanted_features" not in ans and available_soft_features(cand):
        return "features"
    return "result"


def reasons_for(product, ans, applied_tier):
    """추천 근거 문장들 (매니저 설명용)."""
    out = []
    inst = {"빌트인": "빌트인 설치", "Fit & Max": "Fit & Max(가구장 맞춤) 설치",
            "프리스탠딩": "프리스탠딩 설치"}.get(product["install"], product["install"])
    out.append(f"원하신 {inst} 타입이에요.")
    if applied_tier:
        out.append(f"가족 구성·요리 습관에 맞는 {TIER_LABEL[applied_tier]} "
                   f"(실제 {product['total_l']}L) 용량이에요.")
    wanted = set(ans.get("wanted_features", []))
    hit = wanted & product["features"]
    if hit:
        labels = [SOFT_FEATURES[k][0].split(" (")[0] for k in hit]
        out.append("원하신 기능 " + ", ".join(labels) + " 을(를) 갖췄어요.")
    if product["energy"] == 1:
        out.append("에너지 1등급이라 전기료 부담도 적어요.")
    return out
