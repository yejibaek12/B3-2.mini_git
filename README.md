# Mini Git

Mini Git은 커밋 그래프(DAG), 브랜치 제어, 위상 정렬 기반 로그 출력, 고속 검색 색인, 최단 경로 탐색 등 Git의 핵심 메커니즘을 메모리 상에서 시뮬레이션하는 CLI 프로그램입니다.

---

## 1. 실행방법

### 사전 요구사항
* **Python 3.10 이상**
* **별도 패키지 설치 불필요** — 표준 라이브러리만 사용합니다 (`shlex` 등).

### 실행
진입점 파일인 `main.py`가 있는 `B3-2` 디렉터리에서 아래 명령어를 실행하여 대화형 CLI 콘솔을 작동시킵니다.

```bash
cd B3-2
python main.py
```

Windows에서 `python` 명령이 인식되지 않으면 `py main.py`를 사용합니다.

정상 실행 시 `mini-git>` 프롬프트가 표시됩니다.

### 종료
* `EXIT` 또는 `QUIT` 명령 입력
* `Ctrl+C` 또는 `Ctrl+Z`(EOF) — `Exiting...` 메시지 후 종료

### 빠른 시작 예시
저장소를 사용하려면 **반드시 `INIT`으로 먼저 초기화**해야 합니다. 공백이 포함된 인수는 큰따옴표로 감싸 입력합니다.

```text
mini-git> INIT "Alice"
mini-git> COMMIT "First commit"
mini-git> LOG
mini-git> EXIT
```

초기화 전에 다른 명령을 입력하면 `Repository not initialized`가 출력됩니다. 전체 명령어는 [§3. 명령어 레퍼런스](#3-명령어-레퍼런스)를 참고하세요.

---

## 2. 개발 제약 사항 및 범위

### 기술 제약
* **개발 언어**: Python 3.10 이상 
* **라이브러리**: 그래프 전용 서드파티 라이브러리(NetworkX 등) 사용 금지. `list`, `dict`, `set` 등 기본 자료구조와 Python 표준 라이브러리는 사용 가능.
* **정렬**: `sorted()`, `list.sort()` 사용 금지. 정렬 알고리즘은 직접 구현.

### 구현 범위
* **커밋 메타데이터만** 관리하며, 실제 파일 내용은 추적하지 않습니다.
* **네트워크·원격 저장소** 기능은 없습니다. 로컬에서 단독으로 동작합니다.
* **인메모리**만 지원합니다. 프로그램을 종료하면 데이터가 사라집니다.

---

## 3. 명령어 레퍼런스

### 입력 규칙
* 명령어는 대소문자를 구분하지 않습니다 (`INIT` = `init`).
* 공백이 있는 인수는 큰따옴표로 감쌉니다 (`COMMIT "Add login feature"`).

### 주요 에러 메시지
| 상황 | 메시지 |
|------|--------|
| 인수·옵션 오류 | `Invalid args` |
| 미초기화 상태 | `Repository not initialized` |
| 없는 브랜치 | `Unknown branch: <name>` |
| 없는 커밋 | `Unknown commit: <hash>` |
| 브랜치 중복 | `Branch already exists: <name>` |

### 명령어

| 명령어 | 설명 |
|--------|------|
| `INIT <user_name>` | 저장소 초기화. `main` 브랜치·작성자 설정. 재실행 시 기존 데이터 초기화 |
| `BRANCH <name>` | 현재 HEAD 위치에 새 브랜치 생성 |
| `SWITCH <name>` | 활성 브랜치 전환 |
| `COMMIT <message>` | 현재 HEAD를 부모로 새 커밋 생성. 역색인 갱신 |
| `LOG` | 부모가 자식보다 먼저 나오는 위상 정렬 순서로 출력 |
| `LOG --sort-by=date\|author` | 날짜 또는 작성자 기준 정렬 출력 |
| `PATH <c1> <c2>` | 두 커밋 간 최단 경로 (무방향). 없으면 `No path` |
| `ANCESTORS <hash>` | 조상 커밋 전체 출력. 없으면 `Ancestors: None` |
| `SEARCH <keyword>` | 메시지 키워드 검색 (대소문자 무시, 단어 단위) |
| `SEARCH --author=<name>` | 작성자별 커밋 검색 |
| `EXIT` / `QUIT` | 프로그램 종료 |

---

## 4. 프로젝트 구조

```
B3-2/
├── main.py          # REPL 진입점, 명령 파싱·라우팅
├── models.py        # CommitNode (커밋 DAG 노드)
├── repository.py    # 저장소 상태, 명령 처리, 역색인
└── utils/
    ├── __init__.py  # 패키지 마커
    ├── sorting.py   # merge_sort (직접 구현)
    └── graph.py     # 위상 정렬, BFS, DFS
```

**실행 흐름:** 사용자 입력 → `main.py`(파싱) → `repository.py`(명령 처리) → 필요 시 `utils/`(정렬·그래프 알고리즘). 커밋 데이터 형태는 `models.py`의 `CommitNode`로 표현합니다.

### 파일별 설명

**[main.py](./main.py)** — 콘솔 입출력·명령 분기
- `python main.py` 실행 시 가장 먼저 돌아가는 진입점입니다.
- `mini-git>` 프롬프트에서 한 줄씩 입력을 받고, `shlex`로 `COMMIT "hello world"`처럼 따옴표·공백을 올바르게 나눕니다.
- 인수 개수가 맞는지, 알려진 명령인지만 확인한 뒤 `repo.commit(...)`처럼 `Repository` 메서드를 호출합니다. 커밋 생성·브랜치·검색 같은 Git 동작 자체는 이 파일에 없습니다.

**[models.py](./models.py)** — 커밋 한 건의 데이터 모양
- `CommitNode` 클래스 하나만 정의합니다. 커밋이 가져야 할 필드(해시, 메시지, 작성자, 시각, 부모 목록 등)를 담는 그릇입니다.
- `parents`에 이전 커밋 해시를 넣어 커밋끼리 화살표로 이어지는 DAG(분기 가능한 이력 그래프)를 만듭니다.
- 저장소 상태를 바꾸거나 명령을 처리하지 않습니다.

**[repository.py](./repository.py)** — Mini Git의 핵심 엔진
- 메모리 안의 가짜 Git 저장소 전체를 `Repository` 클래스 하나로 관리합니다.
- `commits`(해시 → 커밋 객체), `branches`(브랜치명 → 그 브랜치 최신 커밋), `head`(지금 작업 중인 브랜치), 키워드·작성자 역색인 등을 들고 있습니다.
- §3의 `INIT`, `COMMIT`, `LOG`, `SEARCH`, `PATH` 등 대부분의 명령이 결국 이 파일의 메서드를 실행합니다.

**[utils/__init__.py](./utils/__init__.py)** — `utils` 패키지 선언
- 내용은 비어 있지만, Python이 `utils` 폴더를 패키지로 인식하게 해 `from utils.graph import ...` import가 가능해집니다.

**[utils/sorting.py](./utils/sorting.py)** — 직접 구현한 정렬
- 과제 제약으로 `sorted()`, `list.sort()`를 쓸 수 없어 `merge_sort`를 직접 구현했습니다.
- `LOG --sort-by=date|author`로 날짜·작성자순 출력할 때, `ANCESTORS` 결과를 시간순으로 맞출 때 등 `repository.py`에서 호출합니다.

**[utils/graph.py](./utils/graph.py)** — 커밋 그래프 탐색 알고리즘
- 커밋 관계를 그래프로 보고 돌리는 함수만 모아 둔 모듈입니다. 저장소 상태는 다루지 않습니다.
- `topological_sort` → `LOG`(부모가 자식보다 먼저 나오게), `find_shortest_path` → `PATH`(BFS 최단 경로), `find_ancestors` → `ANCESTORS`(조상 추적)에 쓰입니다.

---

## 5. 확장 시 고려사항 (참고)

본 과제는 인메모리 시뮬레이션이므로 커밋 수가 크게 늘면 아래 지점에서 병목이 생길 수 있습니다.

* **역색인·커밋 저장**: 전체를 메모리 dict로 유지 → SQLite/RocksDB 등 영속 저장소 검토
* **PATH (BFS)**: 그래프가 커지면 탐색 비용 증가 → 양방향 BFS 등으로 완화 가능
* **LOG (위상 정렬)**: 호출마다 전체 그래프 정렬 → 페이지네이션, 증분 갱신 검토
