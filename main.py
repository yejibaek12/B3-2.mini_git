import shlex
from repository import Repository

def main():
    repo = Repository()

    while True:
        try:
            line = input("mini-git> ").strip()
            if not line:
                continue

            # shlex를 사용하여 큰따옴표를 지원하는 명령줄 토큰화 수행
            try:
                tokens = shlex.split(line)
            except ValueError:
                print("Invalid args")
                continue

            if not tokens:
                continue

            cmd = tokens[0].upper()
            args = tokens[1:]

            # 명령어 라우팅
            if cmd in ("EXIT", "QUIT"):
                if len(args) != 0:
                    print("Invalid args")
                else:
                    break

            elif cmd == "INIT":
                if len(args) != 1:
                    print("Invalid args")
                else:
                    repo.init(args[0])

            elif cmd == "BRANCH":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.branch(args[0])

            elif cmd == "SWITCH":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.switch(args[0])

            elif cmd == "COMMIT":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.commit(args[0])

            elif cmd == "LOG":
                if len(args) == 0:
                    if not repo.is_initialized:
                        print("Repository not initialized")
                    else:
                        repo.log()
                elif len(args) == 1:
                    if not repo.is_initialized:
                        print("Repository not initialized")
                    else:
                        part = args[0].split('=', 1)
                        # 정렬 파라미터 옵션에 대한 유효성 검사
                        if len(part) == 2 and part[0] == '--sort-by' and part[1] in ('date', 'author'):
                            repo.log(part[1])
                        else:
                            print("Invalid args")
                else:
                    print("Invalid args")

            elif cmd == "PATH":
                if len(args) != 2:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.path(args[0], args[1])

            elif cmd == "ANCESTORS":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.ancestors(args[0])

            elif cmd == "SEARCH":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    arg = args[0]
                    if arg.startswith('--author='):
                        part = arg.split('=', 1)
                        if len(part) == 2:
                            repo.search_author(part[1])
                        else:
                            print("Invalid args")
                    else:
                        repo.search_keyword(arg)

            else:
                print("Invalid args")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
