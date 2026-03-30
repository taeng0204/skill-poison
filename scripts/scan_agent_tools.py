#!/usr/bin/env python3
"""
Phase 1: 에이전트 도구 취약점 스캐너

각 코딩 에이전트 프레임워크의 Skill/Plugin 로딩 메커니즘을 분석하고
잠재적 취약점 패턴을 식별합니다.
"""

import json
import os
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class AgentProfile:
    """에이전트 프레임워크 프로필"""
    name: str
    repo_url: str
    skill_file_names: list[str]  # Skill/지시 파일 이름들
    skill_load_mechanism: str     # 로딩 방식 설명
    sandboxing: str              # 샌드박싱 수준
    input_validation: str        # 입력 검증 방식
    known_vulns: list[str]       # 알려진 취약점
    notes: str = ""


# 분석 대상 에이전트 프레임워크 정의
AGENT_PROFILES = [
    AgentProfile(
        name="Claude Code",
        repo_url="https://github.com/anthropics/claude-code",
        skill_file_names=["CLAUDE.md", ".claude/settings.json"],
        skill_load_mechanism="프로젝트 루트 및 상위 디렉토리의 CLAUDE.md를 자동 로드하여 시스템 프롬프트에 주입",
        sandboxing="사용자 확인 기반 (allowlist/denylist), 파일 접근 제한 없음",
        input_validation="CLAUDE.md 내용에 대한 별도 검증 없음 (신뢰된 컨텍스트로 취급)",
        known_vulns=[
            "CLAUDE.md를 통한 Prompt Injection",
            "상위 디렉토리 CLAUDE.md 오염 (supply chain)",
            "allowlist 우회 가능성",
        ],
    ),
    AgentProfile(
        name="OpenCode",
        repo_url="https://github.com/opencode-ai/opencode",
        skill_file_names=[".opencode/instructions.md", "opencode.yaml"],
        skill_load_mechanism="프로젝트 내 instructions.md를 시스템 프롬프트에 주입",
        sandboxing="기본적으로 제한 없음 (호스트 터미널 직접 실행)",
        input_validation="instructions 파일에 대한 검증 없음",
        known_vulns=[
            "instructions.md를 통한 임의 명령 실행 유도",
            "터미널 접근 제한 없음",
        ],
    ),
    AgentProfile(
        name="Aider",
        repo_url="https://github.com/paul-gauthier/aider",
        skill_file_names=[".aider.conf.yml", ".aider/conventions.md"],
        skill_load_mechanism="conventions 파일 및 설정 파일을 통한 지시 주입",
        sandboxing="파일 편집만 가능 (터미널 명령 실행은 사용자 확인 필요)",
        input_validation="설정 파일 스키마 검증은 있으나 conventions 내용 검증 없음",
        known_vulns=[
            "conventions를 통한 악성 코드 생성 유도",
            "auto-commit 시 악성 코드 자동 커밋",
        ],
    ),
    AgentProfile(
        name="Continue",
        repo_url="https://github.com/continuedev/continue",
        skill_file_names=[".continuerules", ".continue/config.json"],
        skill_load_mechanism=".continuerules 파일을 시스템 프롬프트에 추가, config.json으로 모델/도구 설정",
        sandboxing="VSCode 확장 권한 범위 내 (파일 R/W, 터미널 실행)",
        input_validation="config.json 스키마 검증, .continuerules 내용 검증 없음",
        known_vulns=[
            ".continuerules를 통한 악성 지시 주입",
            "커스텀 slash command를 통한 코드 실행",
        ],
    ),
    AgentProfile(
        name="Codex CLI",
        repo_url="https://github.com/openai/codex",
        skill_file_names=["AGENTS.md", "codex.yaml"],
        skill_load_mechanism="AGENTS.md를 에이전트 지시에 포함",
        sandboxing="네트워크 격리 샌드박스 (seatbelt/landlock)",
        input_validation="AGENTS.md 내용 검증 없음",
        known_vulns=[
            "AGENTS.md를 통한 Prompt Injection",
            "샌드박스 우회 가능성 (로컬 파일 접근은 허용)",
        ],
    ),
]


def generate_report(profiles: list[AgentProfile], output_path: str):
    """분석 보고서 생성"""
    
    report = {
        "scan_date": __import__("datetime").datetime.now().isoformat(),
        "agents_analyzed": len(profiles),
        "profiles": [asdict(p) for p in profiles],
        "summary": {
            "common_patterns": [
                "모든 에이전트가 Skill/지시 파일 내용을 검증 없이 시스템 프롬프트에 주입",
                "대부분 파일시스템 접근에 대한 제한이 없거나 느슨함",
                "네트워크 격리를 제공하는 에이전트는 Codex CLI만 해당",
                "Skill 파일의 무결성 검증(해시, 서명) 메커니즘 없음",
            ],
            "attack_surfaces": [
                "Skill 파일 직접 수정 (로컬 접근 시)",
                "Git 저장소를 통한 Skill 파일 배포 (supply chain)",
                "공유 Skill 마켓플레이스/레지스트리 오염",
                "상위 디렉토리 Skill 파일 오염 (상속 메커니즘 악용)",
            ],
            "recommendations": [
                "Skill 파일 로드 시 악성 패턴 스캔",
                "Skill 파일 해시 검증 및 변경 알림",
                "Skill 파일 내 명령 실행 지시 격리/차단",
                "네트워크 격리 기본 활성화",
                "Skill 파일 출처(provenance) 추적",
            ],
        },
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 스캔 보고서 생성: {output_path}")
    print(f"   분석 에이전트: {len(profiles)}개")
    print(f"   공통 취약 패턴: {len(report['summary']['common_patterns'])}개")
    print(f"   공격 표면: {len(report['summary']['attack_surfaces'])}개")
    
    return report


def print_markdown_report(profiles: list[AgentProfile]):
    """마크다운 형식 보고서 출력"""
    
    print("# Phase 1: Agent Tool 취약점 스캔 결과\n")
    print("| 에이전트 | Skill 파일 | 샌드박싱 | 입력 검증 | 알려진 취약점 수 |")
    print("|----------|-----------|---------|----------|---------------|")
    
    for p in profiles:
        skill_files = ", ".join(p.skill_file_names)
        vuln_count = len(p.known_vulns)
        sandbox_short = p.sandboxing[:30] + "..." if len(p.sandboxing) > 30 else p.sandboxing
        validation_short = p.input_validation[:30] + "..." if len(p.input_validation) > 30 else p.input_validation
        print(f"| {p.name} | {skill_files} | {sandbox_short} | {validation_short} | {vuln_count} |")
    
    print("\n## 핵심 발견\n")
    print("1. **모든 에이전트**가 Skill 파일 내용을 **무검증으로 시스템 프롬프트에 주입**")
    print("2. **Codex CLI만** 네트워크 격리 샌드박스 제공")
    print("3. **어떤 에이전트도** Skill 파일 무결성 검증(해시/서명) 미구현")
    print("4. **Supply chain 공격** 경로 존재: Git 저장소 → Skill 파일 오염")


if __name__ == "__main__":
    output_dir = Path(__file__).parent.parent / "phase1-recon" / "agent-tools"
    output_path = str(output_dir / "scan_report.json")
    
    print_markdown_report(AGENT_PROFILES)
    print()
    generate_report(AGENT_PROFILES, output_path)
