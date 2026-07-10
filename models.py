from datetime import datetime

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
