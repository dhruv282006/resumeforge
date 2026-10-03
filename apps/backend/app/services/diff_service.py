"""Diff and Versioning Service for ResumeForge Phase 3.

Provides text-level and section-level diff generation,
calculates similarity ratios, and safely applies accepted suggestions
to produce new immutable resume versions.
"""

from __future__ import annotations

import difflib
from typing import Any, Dict, List, Optional


class DiffService:
    """Computes transparent human-readable diffs between resume versions and text content."""

    def compute_text_diff(self, original_text: str, updated_text: str) -> Dict[str, Any]:
        """Generates unified diff, line stats, and semantic changes between two text versions."""
        orig_lines = original_text.splitlines(keepends=True) if original_text else []
        upd_lines = updated_text.splitlines(keepends=True) if updated_text else []

        # Unified diff generator
        diff_generator = difflib.unified_diff(
            orig_lines,
            upd_lines,
            fromfile="Original Version",
            tofile="Tailored Version",
            lineterm="",
        )
        unified_diff_str = "\n".join(diff_generator)

        # Detailed ndiff for line-by-line inspection
        matcher = difflib.SequenceMatcher(None, original_text or "", updated_text or "")
        similarity_ratio = round(matcher.ratio() * 100, 2)

        added_lines = 0
        removed_lines = 0
        line_diffs: List[Dict[str, str]] = []

        differ = difflib.Differ()
        orig_clean = (original_text or "").splitlines()
        upd_clean = (updated_text or "").splitlines()

        for line in differ.compare(orig_clean, upd_clean):
            prefix = line[:2]
            content = line[2:]
            if prefix == "+ ":
                added_lines += 1
                line_diffs.append({"type": "ADD", "content": content})
            elif prefix == "- ":
                removed_lines += 1
                line_diffs.append({"type": "REMOVE", "content": content})
            elif prefix == "  ":
                line_diffs.append({"type": "UNCHANGED", "content": content})
            elif prefix == "? ":
                # Intra-line guide
                continue

        return {
            "similarity_ratio": similarity_ratio,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
            "unified_diff": unified_diff_str,
            "line_diffs": line_diffs,
        }

    def compute_snapshot_diff(
        self,
        original_snapshot: Optional[Dict[str, Any]],
        updated_snapshot: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Compares section by section between two structured resume snapshots."""
        orig = original_snapshot or {}
        upd = updated_snapshot or {}

        sections = ["summary", "skills", "experience", "projects", "education", "certifications"]
        section_diffs: Dict[str, Any] = {}

        for sec in sections:
            sec_orig = orig.get(sec)
            sec_upd = upd.get(sec)

            orig_str = self._stringify_section(sec_orig)
            upd_str = self._stringify_section(sec_upd)

            text_diff = self.compute_text_diff(orig_str, upd_str)
            section_diffs[sec] = {
                "has_changes": text_diff["similarity_ratio"] < 100.0,
                "similarity_ratio": text_diff["similarity_ratio"],
                "added_lines": text_diff["added_lines"],
                "removed_lines": text_diff["removed_lines"],
                "diff": text_diff["line_diffs"],
            }

        return section_diffs

    def apply_accepted_suggestions(
        self,
        base_snapshot: Optional[Dict[str, Any]],
        accepted_suggestions: List[Any],
    ) -> Dict[str, Any]:
        """Applies accepted/modified suggestions onto structured snapshot to yield new version."""
        new_snapshot: Dict[str, Any] = dict(base_snapshot or {})

        # Ensure fundamental sections exist
        for sec in ["summary", "skills", "experience", "projects", "education", "certifications"]:
            if sec not in new_snapshot:
                new_snapshot[sec] = [] if sec != "summary" else ""

        for sug in accepted_suggestions:
            section_key = getattr(sug, "section", "").lower()
            sug_type = getattr(sug, "suggestion_type", "")
            orig_text = getattr(sug, "original_content", "") or ""
            prop_text = getattr(sug, "proposed_content", "")

            if not section_key:
                continue

            if section_key == "summary":
                # For summary, replace content
                new_snapshot["summary"] = prop_text
                continue

            # For list sections
            current_list = list(new_snapshot.get(section_key, []))

            if section_key == "skills":
                # Skills list handling
                if sug_type == "ADD_FROM_PROFILE":
                    # Proposed content might be comma-separated or single skill
                    new_skills = [s.strip() for s in prop_text.split(",") if s.strip()]
                    for ns in new_skills:
                        if ns not in current_list:
                            current_list.append(ns)
                elif sug_type == "REMOVE":
                    current_list = [s for s in current_list if s != orig_text]
                elif sug_type in {"EMPHASIZE", "REORDER"}:
                    # Place proposed skills at front
                    promoted = [s.strip() for s in prop_text.split(",") if s.strip()]
                    remaining = [s for s in current_list if s not in promoted]
                    current_list = promoted + remaining
                new_snapshot["skills"] = current_list
                continue

            # Experience / Projects list handling (dicts or bullet strings)
            if sug_type in {"REPHRASE", "EMPHASIZE"}:
                updated = False
                for idx, item in enumerate(current_list):
                    if isinstance(item, str) and (orig_text in item or item in orig_text):
                        current_list[idx] = prop_text
                        updated = True
                        break
                    elif isinstance(item, dict):
                        desc = item.get("description", "")
                        if orig_text and orig_text in desc:
                            item["description"] = desc.replace(orig_text, prop_text)
                            updated = True
                            break
                        # Check responsibilities or bullets
                        bullets = item.get("responsibilities") or item.get("bullets") or []
                        if isinstance(bullets, list):
                            for b_idx, b in enumerate(bullets):
                                if orig_text and (orig_text in b or b in orig_text):
                                    bullets[b_idx] = prop_text
                                    updated = True
                                    break
                if not updated:
                    # Append as new bullet / entry if not matched
                    current_list.append(prop_text)

            elif sug_type == "ADD_FROM_PROFILE":
                current_list.append(prop_text)

            elif sug_type == "REMOVE":
                if orig_text:
                    current_list = [i for i in current_list if (isinstance(i, str) and orig_text not in i)]

            new_snapshot[section_key] = current_list

        return new_snapshot

    def render_snapshot_to_text(self, snapshot: Dict[str, Any]) -> str:
        """Converts structured resume snapshot into canonical text representation."""
        lines: List[str] = []

        # Summary
        summary = snapshot.get("summary")
        if summary:
            lines.append("SUMMARY")
            lines.append(str(summary).strip())
            lines.append("")

        # Skills
        skills = snapshot.get("skills")
        if skills:
            lines.append("SKILLS")
            if isinstance(skills, list):
                lines.append(", ".join(str(s) for s in skills))
            else:
                lines.append(str(skills).strip())
            lines.append("")

        # Experience
        experiences = snapshot.get("experience") or snapshot.get("experiences")
        if experiences:
            lines.append("EXPERIENCE")
            if isinstance(experiences, list):
                for exp in experiences:
                    if isinstance(exp, dict):
                        role = exp.get("role") or exp.get("title") or "Role"
                        comp = exp.get("company", "Company")
                        lines.append(f"{role} - {comp}")
                        if exp.get("description"):
                            lines.append(str(exp["description"]))
                        bullets = exp.get("responsibilities") or exp.get("bullets") or []
                        for b in bullets:
                            lines.append(f"• {b}")
                    else:
                        lines.append(f"• {str(exp)}")
            else:
                lines.append(str(experiences).strip())
            lines.append("")

        # Projects
        projects = snapshot.get("projects")
        if projects:
            lines.append("PROJECTS")
            if isinstance(projects, list):
                for p in projects:
                    if isinstance(p, dict):
                        title = p.get("title") or p.get("name") or "Project"
                        lines.append(str(title))
                        if p.get("description"):
                            lines.append(str(p["description"]))
                        techs = p.get("technologies") or []
                        if techs:
                            lines.append(f"Technologies: {', '.join(str(t) for t in techs)}")
                    else:
                        lines.append(f"• {str(p)}")
            else:
                lines.append(str(projects).strip())
            lines.append("")

        # Education
        educations = snapshot.get("education") or snapshot.get("educations")
        if educations:
            lines.append("EDUCATION")
            if isinstance(educations, list):
                for edu in educations:
                    if isinstance(edu, dict):
                        degree = edu.get("degree", "")
                        inst = edu.get("institution", "")
                        lines.append(f"{degree}, {inst}".strip(", "))
                    else:
                        lines.append(f"• {str(edu)}")
            else:
                lines.append(str(educations).strip())
            lines.append("")

        # Certifications
        certifications = snapshot.get("certifications")
        if certifications:
            lines.append("CERTIFICATIONS")
            if isinstance(certifications, list):
                for cert in certifications:
                    if isinstance(cert, dict):
                        name = cert.get("name", "")
                        issuer = cert.get("issuer", "")
                        lines.append(f"{name} - {issuer}".strip(" -"))
                    else:
                        lines.append(f"• {str(cert)}")
            else:
                lines.append(str(certifications).strip())
            lines.append("")

        return "\n".join(lines).strip()

    def _stringify_section(self, val: Any) -> str:
        if not val:
            return ""
        if isinstance(val, str):
            return val
        if isinstance(val, list):
            return "\n".join(str(x) for x in val)
        if isinstance(val, dict):
            return "\n".join(f"{k}: {v}" for k, v in val.items())
        return str(val)


diff_service = DiffService()
