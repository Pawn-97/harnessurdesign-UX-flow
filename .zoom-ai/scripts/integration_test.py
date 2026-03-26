#!/usr/bin/env python3
"""
integration_test.py — End-to-end static consistency checker for Zoom AI-UX Workflow.

Validates that all components (state machine, skills, scripts, assets, directories)
are consistent and complete WITHOUT running the actual workflow.

Usage:
    python3 .zoom-ai/scripts/integration_test.py

Exit codes:
    0 = all checks passed
    1 = one or more checks failed
"""

import ast
import json
import os
import re
import sys
import tempfile
import shutil

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # .zoom-ai/scripts/ → project root

# MVP state chain (source of truth: zoom-router.md §2.1)
MVP_STATE_CHAIN = [
    "onboarding", "init", "alignment", "research_jtbd", "interaction_design",
    "prepare_design_contract", "contract_review", "hifi_generation",
    "review", "knowledge_extraction", "complete",
]

# Reserved V0.4 states (allowed in schema enum but not in TRANSITIONS)
RESERVED_STATES = ["logic_inquisitor", "baseline_validation"]

# Expected skill files and their router mappings
EXPECTED_SKILLS = {
    "zoom-router.md": "Central router",
    "guided-dialogue.md": "Dialogue protocol",
    "alignment-skill.md": "Phase 1: alignment",
    "research-strategist-skill.md": "Phase 2: research + JTBD",
    "interaction-designer-skill.md": "Phase 3: interaction design",
    "design-contract-skill.md": "Phase 3→4: design contract",
    "alchemist-skill.md": "Phase 4: hi-fi generation",
    "onboarding-skill.md": "Phase 0: onboarding",
    "knowledge-extractor-skill.md": "Knowledge extraction",
}

# Expected Python scripts
EXPECTED_ZOOM_SCRIPTS = [
    "validate_html.py",
    "cognitive_load_audit.py",
    "dom_assembler.py",
    "dom_extractor.py",
    "completeness_lint.py",
    "requirements.txt",
]

EXPECTED_ROOT_SCRIPTS = [
    "validate_transition.py",
    "verify_archive.py",
    "hook_pre_write.py",
    "hook_post_write.py",
    "task_progress_schema.json",
]

# Expected directories
EXPECTED_DIRS = [
    ".zoom-ai/knowledge/skills",
    ".zoom-ai/knowledge/product-context",
    ".zoom-ai/knowledge/rules",
    ".zoom-ai/knowledge/zds/components",
    ".zoom-ai/memory/sessions",
    ".zoom-ai/memory/constraints",
    ".zoom-ai/scripts",
    "scripts",
]

# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def ok(self, msg: str):
        self.passed += 1
        self.details.append(f"  ✅ {msg}")

    def fail(self, msg: str):
        self.failed += 1
        self.details.append(f"  ❌ {msg}")

    def warn(self, msg: str):
        self.warnings += 1
        self.details.append(f"  ⚠️  {msg}")

    def section(self, title: str):
        self.details.append(f"\n{'='*60}")
        self.details.append(f"  {title}")
        self.details.append(f"{'='*60}")

    def summary(self) -> str:
        lines = self.details + [
            f"\n{'='*60}",
            f"  SUMMARY: {self.passed} passed, {self.failed} failed, {self.warnings} warnings",
            f"{'='*60}",
        ]
        return "\n".join(lines)


def p(*parts: str) -> str:
    """Build path relative to project root."""
    return os.path.join(PROJECT_ROOT, *parts)


# ---------------------------------------------------------------------------
# Test 1: State machine consistency
# ---------------------------------------------------------------------------

def test_state_machine_consistency(r: TestResult):
    r.section("1. State Machine Consistency")

    # 1a. Read TRANSITIONS from validate_transition.py
    vt_path = p("scripts", "validate_transition.py")
    if not os.path.isfile(vt_path):
        r.fail(f"validate_transition.py not found at {vt_path}")
        return

    # Import TRANSITIONS dict
    sys.path.insert(0, p("scripts"))
    try:
        import importlib
        vt_mod = importlib.import_module("validate_transition")
        importlib.reload(vt_mod)  # Ensure fresh load
        transitions = vt_mod.TRANSITIONS
    except Exception as e:
        r.fail(f"Failed to import validate_transition.py: {e}")
        return

    # Extract chain from TRANSITIONS
    vt_chain = []
    state = "onboarding"
    visited = set()
    while state and state not in visited:
        visited.add(state)
        vt_chain.append(state)
        next_state = transitions.get(state, {}).get("next")
        state = next_state

    if vt_chain == MVP_STATE_CHAIN:
        r.ok(f"validate_transition.py chain matches MVP ({len(vt_chain)} states)")
    else:
        r.fail(f"validate_transition.py chain mismatch!\n"
               f"    Expected: {MVP_STATE_CHAIN}\n"
               f"    Got:      {vt_chain}")

    # 1b. Read schema enum
    schema_path = p("scripts", "task_progress_schema.json")
    if not os.path.isfile(schema_path):
        r.fail(f"task_progress_schema.json not found")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    schema_enum = schema.get("properties", {}).get("current_state", {}).get("enum", [])

    # Schema should contain all MVP states + reserved states
    for state in MVP_STATE_CHAIN:
        if state in schema_enum:
            r.ok(f"Schema contains MVP state: {state}")
        else:
            r.fail(f"Schema missing MVP state: {state}")

    for state in RESERVED_STATES:
        if state in schema_enum:
            r.ok(f"Schema contains reserved V0.4 state: {state}")
        else:
            r.warn(f"Schema missing reserved state: {state} (optional)")

    # 1c. Check schema uses 'states' not 'gates'
    required = schema.get("required", [])
    if "states" in required:
        r.ok("Schema uses 'states' key (aligned with zoom-router)")
    elif "gates" in required:
        r.fail("Schema still uses 'gates' key — should be 'states'")
    else:
        r.warn("Schema doesn't require 'states' or 'gates' in top-level required")

    # 1d. Check phase2_state, archive_index, accumulated_constraints exist in schema
    props = schema.get("properties", {})
    for field in ["phase2_state", "archive_index", "accumulated_constraints", "prd_path"]:
        if field in props:
            r.ok(f"Schema contains field: {field}")
        else:
            r.fail(f"Schema missing field: {field}")

    # 1e. Parse zoom-router.md state chain
    router_path = p(".zoom-ai", "knowledge", "skills", "zoom-router.md")
    if os.path.isfile(router_path):
        with open(router_path, "r", encoding="utf-8") as f:
            router_content = f.read()
        # Look for the state chain line (§2.1)
        chain_match = re.search(
            r"onboarding\s*→\s*init\s*→\s*alignment\s*→\s*research_jtbd\s*→\s*interaction_design"
            r"\s*[→\n]*\s*prepare_design_contract\s*→\s*contract_review\s*→\s*hifi_generation"
            r"\s*[→\n]*\s*review\s*→\s*knowledge_extraction\s*→\s*complete",
            router_content,
        )
        if chain_match:
            r.ok("zoom-router.md state chain matches MVP")
        else:
            r.warn("Could not parse state chain from zoom-router.md §2.1 — verify manually")
    else:
        r.fail("zoom-router.md not found")


# ---------------------------------------------------------------------------
# Test 2: Skill file completeness
# ---------------------------------------------------------------------------

def test_skill_files(r: TestResult):
    r.section("2. Skill File Completeness")

    skills_dir = p(".zoom-ai", "knowledge", "skills")
    if not os.path.isdir(skills_dir):
        r.fail(f"Skills directory not found: {skills_dir}")
        return

    for filename, description in EXPECTED_SKILLS.items():
        filepath = os.path.join(skills_dir, filename)
        if not os.path.isfile(filepath):
            r.fail(f"Missing skill: {filename} ({description})")
            continue

        size = os.path.getsize(filepath)
        if size < 1024:
            r.fail(f"Skill too small ({size}B): {filename} — expected >1KB")
            continue

        # Check YAML frontmatter
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read(500)

        if content.startswith("---"):
            fm_end = content.find("---", 3)
            if fm_end > 0:
                fm = content[3:fm_end]
                has_name = "name:" in fm
                has_desc = "description:" in fm
                if has_name and has_desc:
                    r.ok(f"{filename} ({size//1024}KB, frontmatter OK)")
                else:
                    r.warn(f"{filename}: frontmatter missing name/description")
            else:
                r.warn(f"{filename}: malformed frontmatter")
        else:
            r.warn(f"{filename}: no YAML frontmatter")


# ---------------------------------------------------------------------------
# Test 3: Python script availability
# ---------------------------------------------------------------------------

def test_python_scripts(r: TestResult):
    r.section("3. Python Script Availability")

    # .zoom-ai/scripts/
    for script in EXPECTED_ZOOM_SCRIPTS:
        filepath = p(".zoom-ai", "scripts", script)
        if os.path.isfile(filepath):
            if script.endswith(".py"):
                # Check syntax by compiling
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()
                    ast.parse(source)
                    r.ok(f".zoom-ai/scripts/{script} (syntax OK)")
                except SyntaxError as e:
                    r.fail(f".zoom-ai/scripts/{script}: syntax error at line {e.lineno}: {e.msg}")
            else:
                r.ok(f".zoom-ai/scripts/{script}")
        else:
            r.fail(f"Missing: .zoom-ai/scripts/{script}")

    # scripts/
    for script in EXPECTED_ROOT_SCRIPTS:
        filepath = p("scripts", script)
        if os.path.isfile(filepath):
            if script.endswith(".py"):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()
                    ast.parse(source)
                    r.ok(f"scripts/{script} (syntax OK)")
                except SyntaxError as e:
                    r.fail(f"scripts/{script}: syntax error at line {e.lineno}: {e.msg}")
            else:
                r.ok(f"scripts/{script}")
        else:
            r.fail(f"Missing: scripts/{script}")


# ---------------------------------------------------------------------------
# Test 4: ZDS asset completeness
# ---------------------------------------------------------------------------

def test_zds_assets(r: TestResult):
    r.section("4. ZDS Asset Completeness")

    # Design.md
    design_path = p(".zoom-ai", "knowledge", "Design.md")
    if os.path.isfile(design_path):
        with open(design_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if len(lines) >= 50:
            r.ok(f"Design.md ({len(lines)} lines)")
        else:
            r.warn(f"Design.md only {len(lines)} lines — expected ≥50")
    else:
        r.fail("Design.md not found")

    # zds-index.md
    index_path = p(".zoom-ai", "knowledge", "zds-index.md")
    if os.path.isfile(index_path):
        r.ok("zds-index.md exists")
    else:
        r.fail("zds-index.md not found")

    # Component specs
    components_dir = p(".zoom-ai", "knowledge", "zds", "components")
    if os.path.isdir(components_dir):
        specs = [f for f in os.listdir(components_dir) if f.endswith(".md")]
        if len(specs) >= 5:
            r.ok(f"ZDS components: {len(specs)} specs ({', '.join(sorted(specs)[:5])}...)")
        else:
            r.warn(f"Only {len(specs)} ZDS component specs — expected ≥5")
    else:
        r.fail("ZDS components directory not found")


# ---------------------------------------------------------------------------
# Test 5: Directory structure
# ---------------------------------------------------------------------------

def test_directories(r: TestResult):
    r.section("5. Directory Structure")

    for dir_path in EXPECTED_DIRS:
        full_path = p(dir_path)
        if os.path.isdir(full_path):
            r.ok(f"{dir_path}/")
        else:
            r.fail(f"Missing directory: {dir_path}/")

    # CLAUDE.md
    if os.path.isfile(p("CLAUDE.md")):
        r.ok("CLAUDE.md exists")
    else:
        r.fail("CLAUDE.md not found")

    # ux-heuristics.yaml
    heuristics = p(".zoom-ai", "knowledge", "rules", "ux-heuristics.yaml")
    if os.path.isfile(heuristics):
        r.ok("ux-heuristics.yaml exists")
    else:
        r.fail("ux-heuristics.yaml not found")


# ---------------------------------------------------------------------------
# Test 6: Simulated state chain walkthrough
# ---------------------------------------------------------------------------

def test_state_chain_simulation(r: TestResult):
    r.section("6. Simulated State Chain Walkthrough")

    # Create a temporary task directory UNDER the project root (so validate_transition
    # can find project-level artifacts via os.path.dirname(task_dir))
    tasks_dir = p("tasks")
    os.makedirs(tasks_dir, exist_ok=True)
    tmp_dir = tempfile.mkdtemp(prefix="zoom-test-", dir=tasks_dir)

    try:
        # Import validate_transition
        sys.path.insert(0, p("scripts"))
        import importlib
        vt_mod = importlib.import_module("validate_transition")
        importlib.reload(vt_mod)

        # Build initial task-progress.json (from zoom-router §1.1)
        states = {}
        for state in MVP_STATE_CHAIN:
            states[state] = {
                "passes": False,
                "approved_by": None,
                "approved_at": None,
                "artifacts": [],
            }
        states["init"]["passes"] = True  # init is auto-passed on creation

        progress = {
            "task_name": "integration-test",
            "prd_path": "test-prd.md",
            "created_at": "2026-03-26T00:00:00Z",
            "current_state": "onboarding",
            "expected_next_state": "init",
            "states": states,
            "phase2_state": {
                "insight_cards_path": None,
                "current_topic_domain": None,
                "topic_count": 0,
            },
            "archive_index": [],
            "accumulated_constraints": [],
        }

        # Create required artifact stubs for each state
        artifact_stubs = {
            "onboarding": [
                (p(".zoom-ai", "knowledge", "product-context", "product-context-index.md"),
                 "# Product Context\nStub for testing.")
            ],
            "alignment": [
                (os.path.join(tmp_dir, "confirmed_intent.md"),
                 "# Confirmed Intent\nStub for testing.")
            ],
            "research_jtbd": [
                (os.path.join(tmp_dir, "00-research.md"), "# Research\nStub."),
                (os.path.join(tmp_dir, "01-jtbd.md"), "# JTBD\nStub."),
            ],
            "interaction_design": [
                (os.path.join(tmp_dir, "02-structure.md"), "# Structure\nStub.")
            ],
            "prepare_design_contract": [
                (os.path.join(tmp_dir, "03-design-contract.md"), "# Contract\nStub.")
            ],
            "contract_review": [
                (os.path.join(tmp_dir, "03-design-contract.md"), "# Contract\nStub.")
            ],
            "hifi_generation": [
                (os.path.join(tmp_dir, "index.html"), "<html><body>Stub</body></html>")
            ],
            "review": [
                (os.path.join(tmp_dir, "index.html"), "<html><body>Stub</body></html>")
            ],
        }

        # Track files we created outside tmp_dir for cleanup
        external_stubs = []

        # Walk through the entire chain
        chain_ok = True
        for i in range(len(MVP_STATE_CHAIN) - 1):
            current = MVP_STATE_CHAIN[i]
            next_state = MVP_STATE_CHAIN[i + 1]

            # Create required artifact stubs for current state
            if current in artifact_stubs:
                for stub_path, stub_content in artifact_stubs[current]:
                    os.makedirs(os.path.dirname(stub_path), exist_ok=True)
                    already_existed = os.path.isfile(stub_path)
                    if not already_existed:
                        with open(stub_path, "w", encoding="utf-8") as f:
                            f.write(stub_content)
                        if not stub_path.startswith(tmp_dir):
                            external_stubs.append(stub_path)

            # Set current state as passed + approved
            progress["current_state"] = current
            progress["expected_next_state"] = next_state
            progress["states"][current]["passes"] = True
            if vt_mod.TRANSITIONS.get(current, {}).get("requires_approval"):
                progress["states"][current]["approved_by"] = "designer"
                progress["states"][current]["approved_at"] = "2026-03-26T00:00:00Z"

            # Write progress file
            progress_path = os.path.join(tmp_dir, "task-progress.json")
            with open(progress_path, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=2)

            # Validate transition
            result = vt_mod.validate_transition(tmp_dir, next_state)
            if result["valid"]:
                r.ok(f"Transition {current} → {next_state}")
            else:
                r.fail(f"Transition {current} → {next_state} FAILED: {result['errors']}")
                chain_ok = False

        if chain_ok:
            r.ok("Full MVP state chain walkthrough: ALL TRANSITIONS VALID")

    except Exception as e:
        r.fail(f"Simulation error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup temp task dir
        shutil.rmtree(tmp_dir, ignore_errors=True)
        # Clean up external stubs we created (only if they're our test stubs)
        for stub_path in external_stubs:
            if os.path.isfile(stub_path):
                with open(stub_path, "r", encoding="utf-8") as f:
                    content = f.read()
                if "Stub for testing" in content:
                    os.remove(stub_path)
        # Remove tasks/ dir if empty
        if os.path.isdir(tasks_dir) and not os.listdir(tasks_dir):
            os.rmdir(tasks_dir)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    r = TestResult()

    print("Zoom AI-UX Workflow — Integration Test Suite")
    print(f"Project root: {PROJECT_ROOT}\n")

    test_state_machine_consistency(r)
    test_skill_files(r)
    test_python_scripts(r)
    test_zds_assets(r)
    test_directories(r)
    test_state_chain_simulation(r)

    print(r.summary())

    sys.exit(0 if r.failed == 0 else 1)


if __name__ == "__main__":
    main()
