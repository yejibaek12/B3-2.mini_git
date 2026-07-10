from collections import deque
from utils.sorting import merge_sort

def build_adjacency_list(commits, undirected=True, reverse=False):
    """
    commits로부터 커밋 그래프의 인접 리스트(Adjacency List)를 생성하여 반환합니다.
    LOG, PATH 및 그래프 탐색 전반에서 코드 재사용을 높이기 위한 공통 헬퍼 메서드입니다.
    
    - undirected가 True인 경우: 부모와 자식 사이에 무방향 에지를 생성합니다. (BFS 거리 측정용)
    - undirected가 False이고:
      - reverse가 False인 경우: 부모에서 자식 방향으로 향하는 순방향 에지를 생성합니다. (순방향 위상 정렬용)
      - reverse가 True인 경우: 자식에서 부모 방향으로 향하는 역방향 에지를 생성합니다. (조상 역추적용)
    """
    adj = {h: set() for h in commits}
    for h, node in commits.items():
        for p in node.parents:
            if p in commits:
                if undirected:
                    adj[h].add(p)
                    adj[p].add(h)
                else:
                    if reverse:
                        adj[h].add(p)  # 자식이 부모를 가리키도록 설정 (역방향 에지)
                    else:
                        adj[p].add(h)  # 부모가 자식을 가리키도록 설정 (순방향 에지)
    return adj


def topological_sort(commits):
    """
    Kahn 알고리즘을 사용하여 커밋들을 위상 정렬(Topological Sort) 순서로 정렬합니다.
    다중 브랜치나 병합 커밋 등으로 인해 큐에 동시에 들어오는 동일 수준(동일 타임스탬프)의
    커밋 노드들은 커밋 해시의 알파벳 사전순으로 오름차순 정렬하여 출력 순서를 보장합니다.
    """
    if not commits:
        return []

    # 재사용 가능한 그래프 빌더: 순방향 인접 리스트 구축 (부모 -> 자식)
    children = build_adjacency_list(commits, undirected=False)
    
    # 현재 커밋들의 자식 관계를 바탕으로 진입 차수(In-degree) 계산
    in_degree = {h: 0 for h in commits}
    for h, node in commits.items():
        for p in node.parents:
            if p in commits:
                in_degree[h] += 1

    # 루트 커밋 추출 (현재 세트에서 부모가 없는 커밋들)
    roots = [h for h in commits if in_degree[h] == 0]
    
    # 큐 초기화 및 커스텀 정렬 적용 (타임스탬프 우선, 동일한 경우 해시의 알파벳 순서로 정렬)
    queue = merge_sort(roots, key=lambda h: (commits[h].timestamp, h))

    result = []
    while queue:
        curr = queue.pop(0)  # 위상 정렬 순서대로 다음 커밋 노드를 꺼냄
        result.append(curr)
        for child in children[curr]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
        # 여러 브랜치가 동시에 처리될 때 결정론적인 순서를 유지하기 위해 활성 큐를 다시 정렬
        queue = merge_sort(queue, key=lambda h: (commits[h].timestamp, h))

    return result


def find_shortest_path(commits, commit1, commit2):
    """
    두 커밋 사이의 연결 관계를 무방향으로 간주하여 최단 경로를 찾습니다.
    동일한 길이의 경로가 여러 개일 경우: 경로의 문자열 표현이 사전순으로 가장 작은 경로를 선택합니다. (예: 'a1 -> b1' vs 'a1 -> b2')
    """
    if commit1 not in commits or commit2 not in commits:
        return None

    if commit1 == commit2:
        return [commit1]

    # 재사용 가능한 그래프 빌더: 무방향 그래프 인접 리스트 생성
    adj = build_adjacency_list(commits, undirected=True)

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
        return []

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

    return best_path


def find_ancestors(commits, commit_hash):
    """
    지정된 커밋의 모든 조상(Ancestor) 커밋을 DFS로 찾아서 반환합니다.
    """
    if commit_hash not in commits:
        return None

    # 공용 adjacency 빌더로부터 역방향 인접 리스트(자식 -> 부모) 생성
    adj = build_adjacency_list(commits, undirected=False, reverse=True)

    visited = set()
    stack = []
    
    # 시작 노드의 부모(이웃)를 스택에 적재
    for p in adj[commit_hash]:
        if p not in visited:
            visited.add(p)
            stack.append(p)

    ancestor_list = []
    # DFS 루프를 돌며 역방향 인접 리스트를 타고 조상 노드를 탐색
    while stack:
        curr = stack.pop()
        ancestor_list.append(curr)
        for p in adj[curr]:
            if p not in visited:
                visited.add(p)
                stack.append(p)

    return ancestor_list
