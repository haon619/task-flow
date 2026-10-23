"""D-018: 기존 DB에 users · owner_id를 더하고 주인 없는 카드를 legacy에게 붙인다.

사용: python scripts/migrate_owner.py [DB 경로]
실행 전에 DB를 백업하고, 전후 카드 수가 같고 주인 없는 카드가 0건인지 검증한다.
검증에 실패하면 0이 아닌 값으로 끝난다.
"""
import os
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402


def count(path: Path, sql: str) -> int:
    conn = sqlite3.connect(path)
    try:
        return conn.execute(sql).fetchone()[0]
    finally:
        conn.close()


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else db.DEFAULT_DB_PATH
    if not path.exists():
        print(f"DB가 없습니다: {path}")
        return 1
    backup = path.with_name(path.name + ".bak")
    shutil.copy2(path, backup)
    before = count(path, "SELECT COUNT(*) FROM tasks")
    print(f"백업: {backup}")
    print(f"마이그레이션 전 카드 수: {before}")

    os.environ["TASK_FLOW_DB"] = str(path)
    db.init_db()

    after = count(path, "SELECT COUNT(*) FROM tasks")
    orphans = count(path, "SELECT COUNT(*) FROM tasks WHERE owner_id IS NULL")
    print(f"마이그레이션 후 카드 수: {after}")
    print(f"주인 없는 카드 수: {orphans}")
    if before != after or orphans != 0:
        print("검증 실패: 백업 파일로 되돌리세요.")
        return 1
    print("검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
