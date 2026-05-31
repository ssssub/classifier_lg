"""상담 엔진 — 설계된 트리(베스트샵 매니저 스크립트)를 그대로 따라가는 추천 로직."""
from data_loader import SOFT_FEATURES

def tier_index(total_l):
    if total_l is None:
        return None
    if total_l < 200:  return 1
    if total_l < 300:  return 2
    if total_l < 400:  return 3
    if total_l < 500:  return 4
    if total_l < 600:  return 5
    if total_l < 800:  return 6
    return 7

TIER_LABEL = {1: "100L대", 2: "200L대", 3: "300L대", 4: "400L대",
              5: "500L대", 6: "600~700L대", 7: "800L+ 대용량"}

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

LIFESTYLE_LABELS = {
    "freshness_keeper": "신선 집착러",
    "hygiene_master": "위생 마니아",
    "saving_expert": "절약 고수",
    "storage_optimizer": "수납 덕후",
    "tech_early_adopter": "테크 얼리어답터",
    "interior_stylist": "인테리어 감성러",
}

LIFESTYLE_FEATURES = {
    "freshness_keeper": {"door_cooling", "fresh_room", "ai"},
    "hygiene_master": {"uv_filter"},
    "saving_expert": {"energy_top", "ai"},
    "storage_optimizer": {"knock_on", "magic_space"},
    "tech_early_adopter": {"voice", "ai"},
    "interior_stylist": set(),
}


def lifestyle_feature_set(ans):
    return set(LIFESTYLE_FEATURES.get(ans.get("lifestyle"), set()))


def _by_install(products, install):
    return [p for p in products if p["install"] == install]


def _target_in_install(products, install, target_tier):
    pool = _by_install(products, install)
    exact = [p for p in pool if tier_index(p["total_l"]) == target_tier]
    if exact:
        return exact, target_tier
    tiers = sorted({tier_index(p["total_l"]) for p in pool if tier_index(p["total_l"])})
    if not tiers:
        return pool, target_tier
    nearest = min(tiers, key=lambda t: abs(t - target_tier))
    return [p for p in pool if tier_index(p["total_l"]) == nearest], nearest


def filter_candidates(products, ans):
    c = list(products)
    applied_tier = None

    if ans.get("install"):
        c = _by_install(c, ans["install"])

    if ans.get("install") != "빌트인" and ans.get("household") and ans.get("cooking"):
        tt = LIFESTYLE_TIER[(ans["household"], ans["cooking"])]
        c, applied_tier = _target_in_install(c, ans["install"], tt)

    if ans.get("door_style"):
        ds = ans["door_style"]
        if ds == "양문형":
            c = [p for p in c if p["doors"] == "2도어"]
        elif ds == "4도어_no_ai":
            c = [p for p in c if p["doors"] == "4도어" and not p["is_ai"]]
        elif ds == "4도어_ai":
            c = [p for p in c if p["doors"] == "4도어" and p["is_ai"]]

    if ans.get("space") == "slim":
        slim = [p for p in c if p["width"] and p["width"] <= 600]
        if slim:
            c = slim
    return c, applied_tier


def needs_door_style(candidates, ans):
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
    widths = [p["width"] for p in candidates if p["width"]]
    return any(w <= 600 for w in widths) and any(w > 600 for w in widths)


def available_soft_features(candidates):
    present = set()
    for p in candidates:
        present |= p["features"]
    return [(k, SOFT_FEATURES[k][0]) for k in SOFT_FEATURES if k in present]


def score_and_rank(candidates, ans):
    wanted = set(ans.get("wanted_features", [])) | lifestyle_feature_set(ans)
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


def next_question(products, ans):
    # Q1: 라이프스타일 (전체 공통)
    if "lifestyle" not in ans:
        return "lifestyle"

    # Q2: 설치형태 (전체 공통)
    if "install" not in ans:
        return "install"

    # Q2: 인원 / 요리 (빌트인은 skip)
    # Q2-1: 도어 방식 (프리스탠딩 800L+ 경로만 조건부)
    # ※ cand <= 1 이어도 Q3(공통 필수)를 거쳐야 하므로 Q3 이전에는 early-exit 없음
    cand, _ = filter_candidates(products, ans)
    if ans.get("install") != "빌트인":
        if "household" not in ans:
            return "household"
        if "cooking" not in ans:
            return "cooking"
        cand, _ = filter_candidates(products, ans)
        if "door_style" not in ans and needs_door_style(cand, ans):
            return "door_style"

    # Q3: 설치공간 크기 (전체 공통 — 무조건 표시)
    if "space" not in ans:
        return "space"

    # Q4: 추가기능 (전체 공통 — space 포함 최신 후보 기반 채점)
    cand, _ = filter_candidates(products, ans)
    if len(cand) <= 1:
        return "result"
    if "wanted_features" not in ans and available_soft_features(cand):
        return "features"
    return "result"


def reasons_for(product, ans, applied_tier):
    out = []
    lifestyle = ans.get("lifestyle")
    lifestyle_label = LIFESTYLE_LABELS.get(lifestyle)
    lifestyle_hits = lifestyle_feature_set(ans) & product["features"]
    if lifestyle_label and lifestyle_hits:
        labels = [SOFT_FEATURES[k][0].split(" (")[0] for k in sorted(lifestyle_hits)]
        out.append(f"{lifestyle_label} 성향에 맞는 " + ", ".join(labels) + " 기능을 갖췄어요.")
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
