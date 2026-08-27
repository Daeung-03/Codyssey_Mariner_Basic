"""Mini Git — 엔트리 포인트 (REPL 루프)."""

from mini_git.parser import parse
from mini_git.repository import Repository


def run_repl() -> None:
    """REPL 루프를 실행한다."""
    repo = Repository()

    while True:
        try:
            line = input("mini-git> ")
        except (EOFError, KeyboardInterrupt):
            break

        parsed = parse(line)
        if parsed is None:
            continue

        # 종료 명령
        if parsed.command in ("EXIT", "QUIT"):
            break

        output = dispatch(repo, parsed)
        if output:
            print(output)


def dispatch(repo: Repository, parsed) -> str:
    """파싱된 명령을 Repository 메서드에 매핑한다."""
    cmd = parsed.command
    args = parsed.args
    options = parsed.options

    match cmd:
        case "INIT":
            if len(args) != 1:
                return "Invalid args"
            return repo.init(args[0])

        case "BRANCH":
            if len(args) != 1:
                return "Invalid args"
            return repo.branch(args[0])

        case "SWITCH":
            if len(args) != 1:
                return "Invalid args"
            return repo.switch(args[0])

        case "COMMIT":
            if len(args) != 1:
                return "Invalid args"
            return repo.commit(args[0])

        case "LOG":
            sort_by = options.get("sort-by")
            if sort_by and sort_by not in ("date", "author"):
                return "Invalid args"
            return repo.log(sort_by=sort_by)

        case "PATH":
            if len(args) != 2:
                return "Invalid args"
            return repo.path(args[0], args[1])

        case "ANCESTORS":
            if len(args) != 1:
                return "Invalid args"
            return repo.ancestors(args[0])

        case "SEARCH":
            author = options.get("author")
            if author:
                return repo.search(author=author)
            if len(args) != 1:
                return "Invalid args"
            return repo.search(keyword=args[0])

        case _:
            return f"Unknown command: {cmd}"


if __name__ == "__main__":
    run_repl()
