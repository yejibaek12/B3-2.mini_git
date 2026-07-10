from models import CommitNode
from utils.sorting import merge_sort
from utils.graph import (
    topological_sort,
    find_shortest_path,
    find_ancestors
)

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

    def log(self, sort_by=None):
        """
        모든 커밋을 출력합니다. 기본 모드에서는 루트부터 시작하는 위상 정렬(Topological Order) 순서로 출력합니다.
        정렬 모드에서는 날짜나 작성자를 기준으로 한 커스텀 병합 정렬을 사용합니다.
        """
        if not self.commits:
            return

        if sort_by is None:
            result = topological_sort(self.commits)
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

        best_path = find_shortest_path(self.commits, commit1, commit2)
        if not best_path:
            print("No path")
            return

        print(f"Path: {' -> '.join(best_path)}")

    def ancestors(self, commit_hash):
        """
        지정된 커밋의 모든 조상(Ancestor) 커밋을 찾습니다.
        """
        if commit_hash not in self.commits:
            print(f"Unknown commit: {commit_hash}")
            return

        ancestor_list = find_ancestors(self.commits, commit_hash)
        if not ancestor_list:
            print("Ancestors: None")
            return

        # 조상 커밋들을 시간순(타임스탬프 우선, 동일할 경우 해시 사전순)으로 정렬
        sorted_ancestors = merge_sort(ancestor_list, key=lambda h: (self.commits[h].timestamp, h))
        print("Ancestors:")
        for h in sorted_ancestors:
            node = self.commits[h]
            print(f"- {h}: {node.message}")

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
