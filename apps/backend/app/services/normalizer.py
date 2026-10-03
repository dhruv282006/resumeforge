"""Skill normalization service.

Provides extensible, rule-based and canonical alias normalization
for technical, tool, and domain skills without requiring massive rigid dictionaries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class NormalizedSkill:
    original_skill: str
    normalized_skill: str
    normalization_source: str  # EXACT, ALIAS_MAP, RULE_BASED


class SkillNormalizer:
    """Normalizes skill strings into canonical representations."""

    # Curated canonical alias mappings (case-insensitive keys)
    CANONICAL_ALIASES: Dict[str, str] = {
        # Frontend
        "react": "React",
        "reactjs": "React",
        "react.js": "React",
        "react js": "React",
        "vue": "Vue.js",
        "vuejs": "Vue.js",
        "vue.js": "Vue.js",
        "nextjs": "Next.js",
        "next.js": "Next.js",
        "next js": "Next.js",
        "angularjs": "Angular",
        "angular": "Angular",
        "angular.js": "Angular",
        "svelte": "Svelte",
        "sveltekit": "SvelteKit",
        # Languages
        "js": "JavaScript",
        "javascript": "JavaScript",
        "ts": "TypeScript",
        "typescript": "TypeScript",
        "py": "Python",
        "python": "Python",
        "python3": "Python",
        "golang": "Go",
        "go lang": "Go",
        "cpp": "C++",
        "c++": "C++",
        "csharp": "C#",
        "c#": "C#",
        "dotnet": ".NET",
        ".net": ".NET",
        "rust": "Rust",
        "ruby": "Ruby",
        "ruby on rails": "Ruby on Rails",
        "rails": "Ruby on Rails",
        # Backend & APIs
        "node": "Node.js",
        "nodejs": "Node.js",
        "node.js": "Node.js",
        "fastapi": "FastAPI",
        "fast-api": "FastAPI",
        "fast api": "FastAPI",
        "django": "Django",
        "flask": "Flask",
        "express": "Express.js",
        "expressjs": "Express.js",
        "express.js": "Express.js",
        "graphql": "GraphQL",
        "rest": "REST APIs",
        "restful": "REST APIs",
        "rest api": "REST APIs",
        "rest apis": "REST APIs",
        "restful apis": "REST APIs",
        "grpc": "gRPC",
        # Databases
        "postgres": "PostgreSQL",
        "postgresql": "PostgreSQL",
        "psql": "PostgreSQL",
        "mongo": "MongoDB",
        "mongodb": "MongoDB",
        "redis": "Redis",
        "mysql": "MySQL",
        "sqlite": "SQLite",
        "elasticsearch": "Elasticsearch",
        "elastic search": "Elasticsearch",
        # Cloud & DevOps
        "aws": "AWS",
        "amazon web services": "AWS",
        "gcp": "Google Cloud",
        "google cloud": "Google Cloud",
        "google cloud platform": "Google Cloud",
        "azure": "Microsoft Azure",
        "microsoft azure": "Microsoft Azure",
        "docker": "Docker",
        "k8s": "Kubernetes",
        "kubernetes": "Kubernetes",
        "terraform": "Terraform",
        "ansible": "Ansible",
        "ci/cd": "CI/CD",
        "cicd": "CI/CD",
        "github actions": "GitHub Actions",
        # AI / ML
        "pytorch": "PyTorch",
        "tensorflow": "TensorFlow",
        "tf": "TensorFlow",
        "scikit-learn": "Scikit-Learn",
        "sklearn": "Scikit-Learn",
        "llm": "LLMs",
        "llms": "LLMs",
        "rag": "RAG",
        "nlp": "NLP",
        # Mobile
        "swift": "Swift",
        "swiftui": "SwiftUI",
        "uikit": "UIKit",
        "objective-c": "Objective-C",
        "objc": "Objective-C",
        "coredata": "CoreData",
        "ios": "iOS",
        "android": "Android",
        "react native": "React Native",
        "flutter": "Flutter",
        "kotlin": "Kotlin",
    }

    # Version patterns like Python 3.11, Angular 14, React 18, etc.
    VERSION_REGEX = re.compile(r"\s+v?(\d+(\.\d+)*)$", re.IGNORECASE)

    def normalize(self, skill_name: str) -> NormalizedSkill:
        """Normalize a skill name string into its canonical representation."""
        if not skill_name or not skill_name.strip():
            return NormalizedSkill(
                original_skill=skill_name or "",
                normalized_skill="",
                normalization_source="EXACT",
            )

        trimmed = skill_name.strip()
        lower = trimmed.lower()

        # 1. Exact alias match
        if lower in self.CANONICAL_ALIASES:
            return NormalizedSkill(
                original_skill=trimmed,
                normalized_skill=self.CANONICAL_ALIASES[lower],
                normalization_source="ALIAS_MAP",
            )

        # 2. Strip trailing version numbers (e.g. "Python 3.10" -> "Python")
        without_version = self.VERSION_REGEX.sub("", trimmed).strip()
        without_version_lower = without_version.lower()
        if without_version_lower in self.CANONICAL_ALIASES:
            return NormalizedSkill(
                original_skill=trimmed,
                normalized_skill=self.CANONICAL_ALIASES[without_version_lower],
                normalization_source="ALIAS_MAP",
            )

        # 3. Rule-based cleaning (clean repeated spacing, standard capitalization)
        cleaned = re.sub(r"\s+", " ", without_version)

        # Preserve known capitalized tech names like 'SQL', 'HTML', 'CSS', 'AWS', 'API'
        if cleaned.upper() in {"SQL", "HTML", "CSS", "AWS", "API", "APIS", "UI", "UX", "SDK", "CLI"}:
            return NormalizedSkill(
                original_skill=trimmed,
                normalized_skill=cleaned.upper(),
                normalization_source="RULE_BASED",
            )

        # Title case for multi-word or single word
        # Handle special characters like C++, C#, .NET
        if cleaned.upper() in {"C++", "C#", ".NET"}:
            return NormalizedSkill(
                original_skill=trimmed,
                normalized_skill=cleaned.upper(),
                normalization_source="RULE_BASED",
            )

        # Default title-case formatting
        normalized = cleaned.title()
        source = "EXACT" if normalized == trimmed else "RULE_BASED"

        return NormalizedSkill(
            original_skill=trimmed,
            normalized_skill=normalized,
            normalization_source=source,
        )


# Global singleton instance
skill_normalizer = SkillNormalizer()
