"""
Reflexダッシュボード サブエージェント

各タブの実装を担当するモジュール群
"""

from .tab_age_gender import create_age_gender_tab
from .tab_persona import create_persona_tab
from .tab_flow import create_flow_tab
from .tab_gap import create_gap_tab
from .tab_rarity import create_rarity_tab
from .tab_competition import create_competition_tab
from .tab_career_cross import create_career_cross_tab
from .tab_urgency_age import create_urgency_age_tab
from .tab_urgency_employment import create_urgency_employment_tab

__all__ = [
    "create_age_gender_tab",
    "create_persona_tab",
    "create_flow_tab",
    "create_gap_tab",
    "create_rarity_tab",
    "create_competition_tab",
    "create_career_cross_tab",
    "create_urgency_age_tab",
    "create_urgency_employment_tab",
]
