"""범용 LG 가전 상담 UI 설정 — 카테고리, 질문, 선택지를 모두 데이터로 주입.
이 파일만 교체하면 냉장고/세탁기/TV/에어컨 등 어떤 가전이든 동작합니다.
"""
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class OptionConfig:
    value: str
    label: str
    desc: str
    icon_key: str = "default"


@dataclass
class QuestionConfig:
    q_id: str
    text: str          # HTML 가능 — <strong>, <span class="accent">
    options: List[OptionConfig]


@dataclass
class CategoryConfig:
    name: str          # "냉장고", "세탁기", "TV" …
    subtitle: str
    questions: Dict[str, QuestionConfig] = field(default_factory=dict)


# ── SVG 라인 아이콘 (24×24 viewBox, stroke-based) ──────────────────────────
ICONS: Dict[str, str] = {
    "builtin": (
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9,22 9,12 15,12 15,22"/>'
    ),
    "fitmax": (
        '<rect x="2" y="3" width="8" height="18" rx="1.5"/>'
        '<rect x="14" y="3" width="8" height="18" rx="1.5"/>'
        '<path d="M10 12h4"/>'
    ),
    "freshness": (
        '<path d="M7 20c-1.7-3.9-.9-7.2 2.3-9.8 2.6-2.1 5.7-2.5 8.7-1.9.5 3.8-.4 6.9-2.8 9.1-2.3 2.1-5.1 2.5-8.2 2.6z"/>'
        '<path d="M7.5 19.5c2.4-4.1 5.4-6.5 9-7.2"/>'
        '<path d="M6.2 10.8C4.1 9.8 3.2 7.7 3 5c2.6.1 4.8 1 5.8 3.2"/>'
    ),
    "hygiene": (
        '<path d="M12 22s8-3.8 8-10V5l-8-3-8 3v7c0 6.2 8 10 8 10z"/>'
        '<path d="M9 12l2 2 4-5"/>'
    ),
    "saving": (
        '<path d="M12 3c3.8 2.6 6 5.5 6 8.5A6 6 0 0 1 6 11.5C6 8.5 8.2 5.6 12 3z"/>'
        '<path d="M10 12h4"/><path d="M12 9v6"/>'
    ),
    "storage": (
        '<path d="M3 7l9-4 9 4-9 4-9-4z"/>'
        '<path d="M3 12l9 4 9-4"/>'
        '<path d="M3 17l9 4 9-4"/>'
    ),
    "smart_home": (
        '<rect x="8" y="3" width="8" height="18" rx="2"/>'
        '<circle cx="12" cy="17" r="1"/>'
        '<path d="M5 8a9 9 0 0 1 14 0"/><path d="M7.8 10.5a5.5 5.5 0 0 1 8.4 0"/>'
    ),
    "interior": (
        '<path d="M4 21V9l8-6 8 6v12"/>'
        '<path d="M9 21v-7h6v7"/>'
        '<path d="M4 11h16"/>'
    ),
    "freestanding": (
        '<rect x="4" y="2" width="16" height="20" rx="2"/>'
        '<line x1="8" y1="7" x2="13" y2="7"/>'
        '<line x1="8" y1="11" x2="11" y2="11"/>'
    ),
    "solo": (
        '<circle cx="12" cy="7" r="4"/>'
        '<path d="M5.2 21a8.8 8.8 0 0 1 13.6 0"/>'
    ),
    "couple": (
        '<circle cx="8" cy="8" r="3.5"/>'
        '<path d="M2 21a7 7 0 0 1 12 0"/>'
        '<circle cx="17.5" cy="8" r="3"/>'
        '<path d="M14 21a5.5 5.5 0 0 1 7 0"/>'
    ),
    "family": (
        '<circle cx="9" cy="7" r="3"/>'
        '<path d="M3 21a7 7 0 0 1 12 0"/>'
        '<path d="M16 3.13a4 4 0 0 1 0 7.75"/>'
        '<path d="M21 21c0-2.4-1.9-4.4-4.4-5"/>'
    ),
    "no-cooking": (
        '<path d="M3 11h18v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7z"/>'
        '<path d="M3 11l2-7h14l2 7"/>'
        '<path d="M12 11v9"/>'
    ),
    "sometimes-cooking": (
        '<path d="M8 2v4M12 2v4M16 2v4"/>'
        '<rect x="3" y="6" width="18" height="15" rx="2"/>'
        '<path d="M6 12h4M6 16h3"/>'
    ),
    "often-cooking": (
        '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/>'
        '<path d="M7 2v20"/>'
        '<path d="M21 15V2c-2.8 0-5 2.2-5 5v6c0 1.1.9 2 2 2h3"/>'
        '<path d="M18 15v7"/>'
    ),
    "love-cooking": (
        '<path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2"/>'
        '<path d="M7 2v20"/>'
        '<path d="M21 15V2c-2.8 0-5 2.2-5 5v6c0 1.1.9 2 2 2h3"/>'
        '<path d="M18 15v7"/>'
        '<path d="M12 8h4"/>'
    ),
    "side-by-side": (
        '<rect x="2" y="3" width="9" height="18" rx="2"/>'
        '<rect x="13" y="3" width="9" height="18" rx="2"/>'
        '<path d="M6 9h2M6 13h2M16 9h2M16 13h2"/>'
    ),
    "4door": (
        '<rect x="2" y="3" width="20" height="8" rx="2"/>'
        '<rect x="2" y="13" width="9" height="8" rx="2"/>'
        '<rect x="13" y="13" width="9" height="8" rx="2"/>'
        '<path d="M6 7h3M15 7h3"/>'
    ),
    "4door-ai": (
        '<rect x="2" y="3" width="20" height="8" rx="2"/>'
        '<rect x="2" y="13" width="9" height="8" rx="2"/>'
        '<rect x="13" y="13" width="9" height="8" rx="2"/>'
        '<circle cx="17.5" cy="5.5" r="1"/><circle cx="20" cy="7" r="1"/>'
        '<circle cx="15" cy="7" r="1"/>'
    ),
    "slim": (
        '<rect x="8" y="2" width="8" height="20" rx="2"/>'
        '<path d="M4 5v14M20 5v14"/>'
    ),
    "normal": (
        '<rect x="4" y="2" width="16" height="20" rx="2"/>'
        '<path d="M8 8h5M8 13h3"/>'
    ),
    "wide": (
        '<rect x="2" y="2" width="20" height="20" rx="2"/>'
        '<path d="M8 2v20M16 2v20"/>'
    ),
    "default": (
        '<circle cx="12" cy="12" r="9"/>'
        '<path d="M12 8v4l3 3"/>'
    ),
}


# ── 냉장고 카테고리 설정 ────────────────────────────────────────────────────
REFRIGERATOR_CONFIG = CategoryConfig(
    name="냉장고",
    subtitle="몇 가지만 답하면, 딱 맞는 제품을 찾아드려요.",
    questions={
        "lifestyle": QuestionConfig(
            q_id="lifestyle",
            text="<strong>Q. 당신은 어떤 사람인가요?</strong><br><span class=\"hint\">내 라이프 스타일에 가장 가까운 것을 골라주세요</span>",
            options=[
                OptionConfig(
                    "freshness_keeper",
                    "신선집착형",
                    "장을 보면 식재료를 완벽하게 보관하는 사람||AI가 온도 자동 조절|재료별 맞춤 보관|24시간 균일 냉기",
                    "freshness",
                ),
                OptionConfig(
                    "hygiene_master",
                    "깔끔관리형",
                    "냉장고 안까지 늘 깨끗하게 관리하는 사람|| UV로 세균 제거|냄새 자동 탈취|향균 필터 내장",
                    "hygiene",
                ),
                OptionConfig(
                    "saving_expert",
                    "효율중시형",
                    "전기세까지 스마트하게 아끼고 사는 사람||전기요금 절반으로|저소음 운전|AI 절전 모드",
                    "saving",
                ),
                OptionConfig(
                    "storage_optimizer",
                    "생활편의형",
                    "냉장고 기능을 알차게 활용할 줄 아는 사람||공간 두 배 활용|노크해서 내부 확인|정수기 기능 내장",
                    "storage",
                ),
                OptionConfig(
                    "tech_early_adopter",
                    "스마트생활형",
                    "집 안 모든 것을 스마트하게 연결하는 사람||AI가 알아서 관리|앱 연동 제어|스마트 홈 연동",
                    "smart_home",
                ),
                OptionConfig(
                    "interior_stylist",
                    "인테리어 감성형",
                    "주방 분위기까지 직접 디자인하는 사람||컬러 맞춤 선택|프리미엄 소재|공간 인테리어 가전",
                    "interior",
                ),
            ],
        ),
        "install": QuestionConfig(
            q_id="install",
            text="냉장고를 <strong>어떻게 설치</strong>하실 계획이세요?",
            options=[
                OptionConfig(
                    "빌트인",
                    "빌트인",
                    "가구장 안에 깔끔하게 맞춰 넣어 주방을 정돈감 있게 완성하는 타입||주방 가구와 일체감 있는 인테리어를 원할 때 추천",
                    "builtin",
                ),
                OptionConfig(
                    "Fit & Max",
                    "Fit & Max",
                    "기존 빌트인보다 적은 여유 공간으로도 설치 가능한 제로 클리어런스 기능으로, 가구와 자연스럽게 어우러지는 타입||가구와 자연스럽게 어우러지는 미니멀한 주방을 원할 때 추천",
                    "fitmax",
                ),
                OptionConfig(
                    "프리스탠딩",
                    "프리스탠딩",
                    "다양한0 용량 선택지와 넉넉한 수납공간으로 자유로운 배치가 가능한 타입||공간 연출에 자유로움을 두고 싶을 때 추천",
                    "freestanding",
                ),
            ],
        ),
        "budget": QuestionConfig(
            q_id="budget",
            text="<strong>예산은 어느 정도로</strong> 생각하고 계신가요?",
            options=[
                OptionConfig("under_150", "150만원 미만", "가성비, 일반형, 소형 중심", "default"),
                OptionConfig("150_300", "150~300만원", "가장 일반적인 대형 냉장고 후보군", "default"),
                OptionConfig("300_500", "300~500만원", "프리미엄 라인업 및 고급 기능 중심", "default"),
                OptionConfig("over_500", "500만원 이상", "시그니처급 또는 일부 최상위 모델", "default"),
                OptionConfig("any", "상관없어요", "예산 제한 없이 추천을 볼게요", "default"),
            ],
        ),
        "household": QuestionConfig(
            q_id="household",
            text="<strong>몇 분이</strong> 함께 사용하시나요?",
            options=[
                OptionConfig("solo",   "혼자 살아요",         "1인 가구에 최적화된 용량으로",  "solo"),
                OptionConfig("two",    "둘이 살아요",         "2인 생활에 딱 맞는 사이즈로",   "couple"),
                OptionConfig("family", "3인 이상 가족이에요", "넉넉한 용량으로 여유롭게",      "family"),
            ],
        ),
        "cooking": QuestionConfig(
            q_id="cooking",
            text="<strong>요리는 얼마나 자주</strong> 하세요?",
            options=[
                OptionConfig("none",      "요리를 거의 안 해요", "배달·간편식 위주로",       "no-cooking"),
                OptionConfig("sometimes", "요리를 가끔 해요",   "가끔 직접 요리해요",       "sometimes-cooking"),
                OptionConfig("often",     "요리를 자주 해요",   "식재료를 꽤 많이 둬요",    "often-cooking"),
                OptionConfig("love",      "요리를 즐겨요",      "신선 재료를 가득 보관해요", "love-cooking"),
            ],
        ),
        "door_style": QuestionConfig(
            q_id="door_style",
            text="<strong>문 여는 방식</strong>은 어떤 게 편하세요?",
            options=[
                OptionConfig("양문형",      "양문형",       "좌우로 활짝 — 넓은 수납공간",    "side-by-side"),
                OptionConfig("4도어_no_ai", "4도어",        "위·아래 분리 — 합리적인 선택",   "4door"),
                OptionConfig("4도어_ai",    "4도어 + AI",   "AI 자동 절전·신선 케어",         "4door-ai"),
            ],
        ),
        "space": QuestionConfig(
            q_id="space",
            text="설치 공간 크기를 알고 있나요?",
            options=[],
        ),
    },
)
