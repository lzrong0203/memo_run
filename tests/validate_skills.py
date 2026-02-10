#!/usr/bin/env python3
"""
驗證 OpenClaw SKILL.md 檔案的語法正確性
- 檢查 YAML frontmatter 格式
- 檢查必要欄位是否存在
- 檢查環境變數命名一致性
"""

import os
import sys
import yaml
import re
from pathlib import Path


def extract_yaml_frontmatter(skill_path):
    """從 SKILL.md 提取 YAML frontmatter"""
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 檢查是否有 YAML frontmatter
    if not content.startswith('---'):
        return None, f"Missing YAML frontmatter (should start with '---')"

    # 提取 frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return None, "Invalid YAML frontmatter format"

    yaml_content = parts[1].strip()

    try:
        data = yaml.safe_load(yaml_content)
        return data, None
    except yaml.YAMLError as e:
        return None, f"YAML parsing error: {e}"


def validate_skill(skill_path):
    """驗證單個 SKILL.md 檔案"""
    print(f"\n{'='*60}")
    print(f"Validating: {skill_path}")
    print(f"{'='*60}")

    # 提取 YAML frontmatter
    data, error = extract_yaml_frontmatter(skill_path)

    if error:
        print(f"❌ YAML Error: {error}")
        return False

    # 檢查必要欄位
    required_fields = ['name', 'description', 'user-invocable', 'homepage']
    missing_fields = [f for f in required_fields if f not in data]

    if missing_fields:
        print(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return False

    print(f"✅ Required fields present: {', '.join(required_fields)}")

    # 檢查 metadata.openclaw
    if 'metadata' not in data:
        print("⚠️  Warning: No metadata field")
    elif 'openclaw' not in data['metadata']:
        print("⚠️  Warning: No openclaw metadata")
    else:
        openclaw_meta = data['metadata']['openclaw']

        # 檢查 openclaw 必要欄位
        if 'emoji' not in openclaw_meta:
            print("⚠️  Warning: No emoji in openclaw metadata")
        else:
            print(f"✅ Emoji: {openclaw_meta['emoji']}")

        if 'primaryEnv' not in openclaw_meta:
            print("⚠️  Warning: No primaryEnv in openclaw metadata")
        else:
            print(f"✅ Primary env: {openclaw_meta['primaryEnv']}")

        if 'requires' not in openclaw_meta:
            print("⚠️  Warning: No requires in openclaw metadata")
        else:
            requires = openclaw_meta['requires']
            if 'binaries' in requires:
                print(f"✅ Required binaries: {', '.join(requires['binaries'])}")
            if 'envVars' in requires:
                print(f"✅ Required env vars: {', '.join(requires['envVars'])}")

    # 檢查 user-invocable
    if data.get('user-invocable') is True:
        print("✅ User-invocable: true")
    else:
        print("⚠️  Warning: user-invocable is not true")

    print(f"\n✅ {skill_path.name} validation PASSED\n")
    return True


def extract_env_vars_from_content(skill_path):
    """從 SKILL.md 內容中提取所有提到的環境變數"""
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 找出所有 ENV_VAR_NAME 格式的環境變數
    env_pattern = r'\b([A-Z][A-Z0-9_]+)\b'
    matches = re.findall(env_pattern, content)

    # 過濾掉常見的非環境變數關鍵字
    excluded = {'SKILL', 'MD', 'API', 'URL', 'AI', 'CLI', 'DB', 'SQL', 'YAML', 'JSON',
                'HTTP', 'HTTPS', 'UTF', 'EOF', 'OK', 'GREEN', 'RED', 'REFACTOR',
                'TDD', 'CRUD', 'REST', 'CDP', 'LLM', 'CRITICAL', 'HIGH', 'MEDIUM',
                'LOW', 'CVE', 'XSS', 'CSRF', 'AGPL'}

    env_vars = set()
    for var in matches:
        if var not in excluded and not var.startswith('CVE'):
            env_vars.add(var)

    return env_vars


def check_env_var_consistency():
    """檢查所有 SKILL.md 中的環境變數命名一致性"""
    print(f"\n{'='*60}")
    print("Checking Environment Variable Consistency")
    print(f"{'='*60}\n")

    skills_dir = Path(__file__).parent.parent / 'skills'

    all_env_vars = {}

    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue

        skill_md = skill_dir / 'SKILL.md'
        if not skill_md.exists():
            continue

        env_vars = extract_env_vars_from_content(skill_md)
        all_env_vars[skill_dir.name] = env_vars

        print(f"📦 {skill_dir.name}:")
        for var in sorted(env_vars):
            print(f"   - {var}")
        print()

    # 找出所有環境變數
    all_vars = set()
    for vars_set in all_env_vars.values():
        all_vars.update(vars_set)

    print(f"✅ Total unique environment variables: {len(all_vars)}")
    print(f"   {', '.join(sorted(all_vars))}")

    return True


def main():
    """主函數"""
    print("\n" + "="*60)
    print("OpenClaw SKILL.md Validation Script")
    print("="*60)

    # 找到所有 SKILL.md 檔案
    skills_dir = Path(__file__).parent.parent / 'skills'

    if not skills_dir.exists():
        print(f"❌ Skills directory not found: {skills_dir}")
        return 1

    skill_files = list(skills_dir.glob('*/SKILL.md'))

    if not skill_files:
        print(f"❌ No SKILL.md files found in {skills_dir}")
        return 1

    print(f"\nFound {len(skill_files)} SKILL.md files\n")

    # 驗證每個檔案
    all_passed = True
    for skill_file in sorted(skill_files):
        if not validate_skill(skill_file):
            all_passed = False

    # 檢查環境變數一致性
    check_env_var_consistency()

    # 總結
    print("\n" + "="*60)
    if all_passed:
        print("✅ All Skills validation PASSED")
        print("="*60 + "\n")
        return 0
    else:
        print("❌ Some Skills validation FAILED")
        print("="*60 + "\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
