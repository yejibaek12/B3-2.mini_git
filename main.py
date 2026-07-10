import os
import sys
import shlex
from datetime import datetime
from collections import deque

# ==============================================================================
# SECTION 1. UTILS & HELPER ALGORITHMS (Merge Sort)
# ==============================================================================

def merge_sort(arr, key=lambda x: x):
    """
    병합 정렬(Merge Sort) 알고리즘을 사용하여 리스트를 정렬합니다.
    O(N log N) 시간 복잡도와 정렬의 안정성(Stability)을 보장합니다.
    
    [복잡도 분석]
    - 시간 복잡도: 모든 경우(최선, 평균, 최악)에 O(N log N)을 가집니다.
    - 공간 복잡도: O(N)의 보조 공간이 필요합니다. 퀵 정렬과 달리 병합 정렬은 
      정렬된 서브 리스트들을 병합하기 위해 추가적인 임시 리스트가 필요합니다.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key)
    right = merge_sort(arr[mid:], key)
    return merge(left, right, key)

def merge(left, right, key):
    """
    정렬의 안정성(Stability)을 유지하면서 두 개의 정렬된 리스트를 하나로 병합합니다.
    """
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if key(left[i]) <= key(right[j]):
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# ==============================================================================
# SECTION 2. DATA MODELS (CommitNode)
# ==============================================================================

class CommitNode:
    """
    버전 관리 그래프의 커밋 노드를 나타냅니다.
    커밋 히스토리를 나타내는 방향성 비순환 그래프(DAG)의 정점(Vertex) 역할을 합니다.
    """
    def __init__(self, commit_hash, message, author, parents, branch, timestamp=None):
        self.hash = commit_hash
        self.message = message
        self.author = author
        self.parents = parents  # 부모 커밋 해시 목록 (이전 커밋을 가리키는 방향성 에지)
        self.branch = branch    # 이 커밋이 생성될 당시의 활성 브랜치
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# SECTION 3. CORE ENGINE (Repository)
# ==============================================================================

class Repository:
    """
    저장소 상태, 브랜치 포인터, 커밋 그래프 및 인덱스를 관리합니다.
    
    [상태 변수 역할]
    - `is_initialized`: 'INIT' 명령을 통해 저장소가 초기화되었는지 여부를 추적합니다.
    - `current_user`: 현재 사용자 이름(커밋 작성자)을 추적합니다.
    - `commits`: 커밋 해시를 CommitNode 객체(DAG 노드)로 매핑하는 딕셔너리입니다.
    - `branches`: 브랜치 이름을 커밋 해시(브랜치의 가장 최신 커밋)로 매핑하는 딕셔너리입니다.
    - `head`: 현재 활성화된 브랜치 이름을 가리키는 문자열입니다. (branches 딕셔너리의 키를 가리킴)
    """
    
    # ---------------------------------------------------------
    # 3-1. 엔진 초기화 및 해시 생성기
    # ---------------------------------------------------------
    def __init__(self):
        self.is_initialized = False
        self.current_user = None
        self.commits = {}           # 커밋 해시 -> CommitNode 매핑
        self.branches = {}          # 브랜치 이름 -> 커밋 해시 매핑 (끝점 가리킴)
        self.head = 'main'          # 현재 활성 브랜치 이름 (HEAD 포인터)
        self.keyword_index = {}     # 키워드 단어 -> 커밋 해시 목록 매핑 (역색인)
        self.author_index = {}      # 작성자 이름 -> 커밋 해시 목록 매핑 (역색인)
        self.commit_counter = 0     # 순차적이고 고유한 해시 생성을 위한 카운터

    def generate_hash(self):
        """
        'a1b2c3', 'd4e5f6', 'g7h8i9'와 같은 중복되지 않는 해시 패턴을 생성합니다.
        테스트와 재현성을 위해 결정론적(Deterministic)인 해시를 제공합니다.
        """
        c = self.commit_counter
        self.commit_counter += 1
        char1 = chr(ord('a') + (3 * c) % 26)
        char2 = chr(ord('b') + (3 * c) % 26)
        char3 = chr(ord('c') + (3 * c) % 26)
        num1 = str(1 + 3 * c)
        num2 = str(2 + 3 * c)
        num3 = str(3 + 3 * c)
        return f"{char1}{num1}{char2}{num2}{char3}{num3}"

    # ---------------------------------------------------------
    # 3-1-Helper. 공통 그래프 인접 리스트 생성기
    # ---------------------------------------------------------
    def _build_adjacency_list(self, undirected=True):
        """
        self.commits로부터 커밋 그래프의 인접 리스트(Adjacency List)를 생성하여 반환합니다.
        LOG, PATH 및 그래프 탐색 전반에서 코드 재사용을 높이기 위한 공통 헬퍼 메서드입니다.
        
        - undirected가 True인 경우: 부모와 자식 사이에 무방향 에지를 생성합니다. (BFS 거리 측정용)
        - undirected가 False인 경우: 부모에서 자식 방향으로 향하는 방향성 에지를 생성합니다. (순방향 위상 정렬용)
        """
        adj = {h: set() for h in self.commits}
        for h, node in self.commits.items():
            for p in node.parents:
                if p in self.commits:
                    if undirected:
                        adj[h].add(p)
                        adj[p].add(h)
                    else:
                        adj[p].add(h)  # 부모가 자식을 가리키도록 설정 (순방향 에지)
        return adj

    # ---------------------------------------------------------
    # 3-2. 버전 관리 명령 핸들러
    # ---------------------------------------------------------
    def init(self, user_name):
        """
        지정된 사용자 이름으로 저장소를 초기화하고 'main' 브랜치를 생성합니다.
        경고: 이미 초기화된 저장소에서 INIT을 다시 호출하면 모든 커밋과 인덱스가 초기화됩니다.
        """
        self.is_initialized = True
        self.current_user = user_name
        self.commits = {}
        self.branches = {'main': None}
        self.head = 'main'          # HEAD 포인터를 'main' 브랜치로 리셋
        self.keyword_index = {}
        self.author_index = {}
        self.commit_counter = 0
        print("Initialized repository.")
        print(f"Current branch: {self.head}")
        print(f"Current user: {self.current_user}")

    def branch(self, branch_name):
        """
        현재 활성화된 브랜치의 최신 커밋을 가리키는 새로운 브랜치 포인터를 생성합니다.
        self.branches 매핑을 업데이트합니다.
        """
        if branch_name in self.branches:
            print(f"Branch already exists: {branch_name}")
            return
        
        current_commit = self.branches[self.head]
        self.branches[branch_name] = current_commit
        print(f"Created branch: {branch_name}")

    def switch(self, branch_name):
        """
        현재 활성화된 브랜치(HEAD)를 지정된 브랜치로 전환합니다.
        self.head 포인터를 업데이트합니다.
        """
        if branch_name not in self.branches:
            print(f"Unknown branch: {branch_name}")
            return
        self.head = branch_name     # 활성 브랜치 포인터 전환
        print(f"Switched to branch: {branch_name}")

    def commit(self, message, parents=None):
        """
        새로운 커밋을 생성하고, 활성 브랜치의 최신 커밋 포인터를 업데이트하며, 역색인(Inverted Index)을 구축합니다.
        역할: self.branches 내의 활성 브랜치 끝(tip) 포인터를 앞으로 이동시키고 커밋 노드를 추가합니다.
        """
        commit_hash = self.generate_hash()
        
        if parents is None:
            parent_hash = self.branches[self.head]
            parents = [parent_hash] if parent_hash else []

        node = CommitNode(
            commit_hash=commit_hash,
            message=message,
            author=self.current_user,
            parents=parents,
            branch=self.head
        )
        self.commits[commit_hash] = node
        self.branches[self.head] = commit_hash  # 활성 브랜치 끝점 포인터를 앞으로 이동

        # 키워드 인덱스 업데이트 (대소문자 구분 없는 단어 매핑)
        words = message.lower().split()
        for term in set(words):
            if term not in self.keyword_index:
                self.keyword_index[term] = []
            self.keyword_index[term].append(commit_hash)

        # 작성자 인덱스 업데이트 (대소문자 구분 없는 작성자 매핑)
        author_key = self.current_user.lower()
        if author_key not in self.author_index:
            self.author_index[author_key] = []
        self.author_index[author_key].append(commit_hash)

        print(f"[{self.head} {commit_hash}] {message}")
        return commit_hash

    # ---------------------------------------------------------
    # 3-3. 역색인 검색 엔진
    # ---------------------------------------------------------
    def search_keyword(self, keyword):
        """
        역색인에서 키워드와 일치하는 커밋을 검색합니다 (대소문자 구분 없음).
        """
        term = keyword.lower()
        matching_hashes = self.keyword_index.get(term, [])
        count = len(matching_hashes)
        unit = "commit" if count == 1 else "commits"
        print(f"Found {count} {unit}:")
        for h in matching_hashes:
            node = self.commits[h]
            print(f"- {h}: {node.message}")

    def search_author(self, author_name):
        """
        역색인에서 특정 작성자가 작성한 커밋을 검색합니다 (대소문자 구분 없음).
        """
        author_key = author_name.lower()
        matching_hashes = self.author_index.get(author_key, [])
        count = len(matching_hashes)
        unit = "commit" if count == 1 else "commits"
        print(f"Found {count} {unit}:")
        for h in matching_hashes:
            node = self.commits[h]
            print(f"- {h}: {node.message}")

    # ---------------------------------------------------------
    # 3-4. 그래프 위상 정렬 및 히스토리 탐색
    # ---------------------------------------------------------
    def log(self, sort_by=None):
        """
        모든 커밋을 출력합니다. 기본 모드에서는 루트부터 시작하는 위상 정렬(Topological Order) 순서로 출력합니다.
        정렬 모드에서는 날짜나 작성자를 기준으로 한 커스텀 병합 정렬을 사용합니다.
        """
        if not self.commits:
            return

        if sort_by is None:
            # 재사용 가능한 그래프 빌더: 순방향 인접 리스트 구축 (부모 -> 자식)
            children = self._build_adjacency_list(undirected=False)
            
            # 현재 커밋들의 자식 관계를 바탕으로 진입 차수(In-degree) 계산
            in_degree = {h: 0 for h in self.commits}
            for h, node in self.commits.items():
                for p in node.parents:
                    if p in self.commits:
                        in_degree[h] += 1

            # 루트 커밋 추출 (현재 세트에서 부모가 없는 커밋들)
            roots = [h for h in self.commits if in_degree[h] == 0]
            
            # 큐 초기화 및 커스텀 정렬 적용 (타임스탬프 우선, 동일한 경우 해시의 알파벳 순서로 정렬)
            # 다중 부모 머지 커밋이나 병렬 브랜치가 있는 경우 결정론적인 출력을 보장하기 위한 규칙입니다.
            queue = merge_sort(roots, key=lambda h: (self.commits[h].timestamp, h))

            result = []
            while queue:
                curr = queue.pop(0)  # 위상 정렬 순서대로 다음 커밋 노드를 꺼냄
                result.append(curr)
                for child in children[curr]:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
                # 여러 브랜치가 동시에 처리될 때 결정론적인 순서를 유지하기 위해 활성 큐를 다시 정렬
                queue = merge_sort(queue, key=lambda h: (self.commits[h].timestamp, h))

            for h in result:
                node = self.commits[h]
                print(f"commit {node.hash} ({node.author}, {node.timestamp}) [{node.branch}]")
                print(node.message)
        else:
            commit_list = list(self.commits.values())
            if sort_by == 'date':
                sorted_nodes = merge_sort(commit_list, key=lambda x: (x.timestamp, x.hash))
            elif sort_by == 'author':
                sorted_nodes = merge_sort(commit_list, key=lambda x: (x.author.lower(), x.hash))
            else:
                print("Invalid args")
                return

            for node in sorted_nodes:
                print(f"commit {node.hash} ({node.author}, {node.timestamp})")
                print(node.message)

    def path(self, commit1, commit2):
        """
        두 커밋 사이의 연결 관계를 무방향으로 간주하여 최단 경로를 찾습니다.
        동일한 길이의 경로가 여러 개일 경우: 경로의 문자열 표현이 사전순으로 가장 작은 경로를 선택합니다. (예: 'a1 -> b1' vs 'a1 -> b2')
        """
        if commit1 not in self.commits:
            print(f"Unknown commit: {commit1}")
            return
        if commit2 not in self.commits:
            print(f"Unknown commit: {commit2}")
            return

        if commit1 == commit2:
            print(f"Path: {commit1}")
            return

        # 재사용 가능한 그래프 빌더: 무방향 그래프 인접 리스트 생성
        adj = self._build_adjacency_list(undirected=True)

        # BFS를 통한 최단 경로 탐색 (큐에는 탐색한 경로 자체를 저장)
        queue = deque([[commit1]])
        visited = {commit1: 0}  # 노드별 도달하는 최소 경로 길이를 저장
        shortest_paths = []
        shortest_length = None

        while queue:
            path = queue.popleft()
            curr = path[-1]

            # 이미 찾은 최단 경로의 길이를 초과하는 경로는 더 이상 탐색하지 않음
            if shortest_length is not None and len(path) > shortest_length:
                break

            if curr == commit2:
                shortest_length = len(path)
                shortest_paths.append(path)
                continue

            # 이웃 노드들을 결정론적으로 정렬된 순서에 따라 방문 (일관된 경로 생성)
            sorted_neighbors = merge_sort(list(adj[curr]), key=lambda x: x)
            for neighbor in sorted_neighbors:
                new_dist = len(path)
                # 처음 방문하거나 기존 최단 거리와 같거나 더 짧은 경로로 도달하는 경우만 큐에 추가
                if neighbor not in visited or visited[neighbor] >= new_dist:
                    visited[neighbor] = new_dist
                    queue.append(path + [neighbor])

        if not shortest_paths:
            print("No path")
            return

        path_strings = []
        for p in shortest_paths:
            path_str = " -> ".join(p)
            path_strings.append((path_str, p))

        # 동점 제거 로직 (사전순으로 가장 작은 문자열 표현 경로 선택)
        best_path_str, best_path = path_strings[0]
        for p_str, p in path_strings[1:]:
            if p_str < best_path_str:
                best_path_str = p_str
                best_path = p

        print(f"Path: {best_path_str}")

    def ancestors(self, commit_hash):
        """
        지정된 커밋의 모든 조상(Ancestor) 커밋을 찾습니다.
        """
        if commit_hash not in self.commits:
            print(f"Unknown commit: {commit_hash}")
            return

        visited = set()
        stack = []
        start_node = self.commits[commit_hash]
        
        # 부모 커밋 해시들(조상)을 스택에 삽입
        for p in start_node.parents:
            if p in self.commits and p not in visited:
                visited.add(p)
                stack.append(p)

        ancestor_list = []
        # DFS 루프를 돌며 재귀적으로 과거의 모든 부모 노드를 탐색
        while stack:
            curr = stack.pop()
            ancestor_list.append(curr)
            curr_node = self.commits[curr]
            for p in curr_node.parents:
                if p in self.commits and p not in visited:
                    visited.add(p)
                    stack.append(p)

        if not ancestor_list:
            print("Ancestors: None")
            return

        # 조상 커밋들을 시간순(타임스탬프 우선, 동일할 경우 해시 사전순)으로 정렬
        sorted_ancestors = merge_sort(ancestor_list, key=lambda h: (self.commits[h].timestamp, h))
        print("Ancestors:")
        for h in sorted_ancestors:
            node = self.commits[h]
            print(f"- {h}: {node.message}")

    # ---------------------------------------------------------
    # 3-5. 고급 그래프 연산 (브랜치 머지)
    # ---------------------------------------------------------
    def merge_branch(self, branch_name):
        """
        대상 브랜치를 현재 활성화된 브랜치에 병합하고 머지 커밋을 생성합니다.
        """
        if branch_name not in self.branches:
            print(f"Unknown branch: {branch_name}")
            return

        parent1 = self.branches[self.head]
        parent2 = self.branches[branch_name]

        if parent1 is None:
            self.branches[self.head] = parent2
            print(f"Fast-forwarded {self.head} to {branch_name}")
            return

        if parent2 is None:
            print("Target branch has no commits to merge.")
            return

        if parent1 == parent2:
            print("Already up to date.")
            return

        # 두 개의 부모를 갖는 머지 커밋 생성 (parent1 = 현재 HEAD 끝점, parent2 = 대상 브랜치 끝점)
        msg = f"Merge branch '{branch_name}' into {self.head}"
        parents = [parent1, parent2]
        self.commit(message=msg, parents=parents)



# ==============================================================================
# SECTION 4. INTERACTIVE CONSOLE (REPL - Main Loop)
# ==============================================================================

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


            elif cmd == "MERGE":
                if len(args) != 1:
                    print("Invalid args")
                elif not repo.is_initialized:
                    print("Repository not initialized")
                else:
                    repo.merge_branch(args[0])

            else:
                print("Invalid args")

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break


if __name__ == "__main__":
    main()
