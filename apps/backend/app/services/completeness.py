"""Deterministic profile completeness calculator for Master Career Profile."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.profile import Profile


def calculate_profile_completeness(profile: Profile) -> dict[str, Any]:
    """Calculate internal deterministic profile completeness percentage.

    Weighting breakdown (total: 100%):
      - Personal Info (20%): headline (4%), summary (4%), email (4%), phone (4%), location (4%)
      - Education (15%): at least 1 education entry (15%)
      - Experience (25%): at least 1 experience entry (25%)
      - Skills (20%): 1 skill (10%), >=3 skills (20%)
      - Projects (10%): at least 1 project (10%)
      - Certifications (5%): at least 1 certification (5%)
      - Links (5%): at least 1 of linkedin, github, or portfolio (5%)
    """
    # 1. Personal section (20 max)
    personal_score = 0
    if profile.headline and profile.headline.strip():
        personal_score += 4
    if profile.summary and profile.summary.strip():
        personal_score += 4
    if profile.email and profile.email.strip():
        personal_score += 4
    if profile.phone and profile.phone.strip():
        personal_score += 4
    if profile.location and profile.location.strip():
        personal_score += 4
    # Normalize to 0-100 for section
    personal_pct = int((personal_score / 20) * 100)

    # 2. Education section (15 max)
    edu_count = len(profile.educations) if profile.educations else 0
    edu_score = 15 if edu_count > 0 else 0
    edu_pct = 100 if edu_count > 0 else 0

    # 3. Experience section (25 max)
    exp_count = len(profile.experiences) if profile.experiences else 0
    exp_score = 25 if exp_count > 0 else 0
    exp_pct = 100 if exp_count > 0 else 0

    # 4. Skills section (20 max)
    skills_count = len(profile.skills) if profile.skills else 0
    if skills_count >= 3:
        skills_score = 20
        skills_pct = 100
    elif skills_count >= 1:
        skills_score = 10
        skills_pct = 50
    else:
        skills_score = 0
        skills_pct = 0

    # 5. Projects section (10 max)
    proj_count = len(profile.projects) if profile.projects else 0
    proj_score = 10 if proj_count > 0 else 0
    proj_pct = 100 if proj_count > 0 else 0

    # 6. Certifications section (5 max)
    cert_count = len(profile.certifications) if profile.certifications else 0
    cert_score = 5 if cert_count > 0 else 0
    cert_pct = 100 if cert_count > 0 else 0

    # 7. Links section (5 max)
    has_links = bool(
        (profile.linkedin_url and profile.linkedin_url.strip())
        or (profile.github_url and profile.github_url.strip())
        or (profile.portfolio_url and profile.portfolio_url.strip())
    )
    links_score = 5 if has_links else 0
    links_pct = 100 if has_links else 0

    overall = personal_score + edu_score + exp_score + skills_score + proj_score + cert_score + links_score

    return {
        "overall": overall,
        "sections": {
            "personal": personal_pct,
            "education": edu_pct,
            "experience": exp_pct,
            "skills": skills_pct,
            "projects": proj_pct,
            "certifications": cert_pct,
            "links": links_pct,
        },
    }

