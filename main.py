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
    Sorts a list using the merge sort algorithm.
    Guarantees O(N log N) time complexity and stability.
    """
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = merge_sort(arr[:mid], key)
    right = merge_sort(arr[mid:], key)
    return merge(left, right, key)

def merge(left, right, key):
    """
    Merges two sorted lists while preserving stability.
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
    Represents a commit node in the version control graph.
    """
    def __init__(self, commit_hash, message, author, parents, branch, timestamp=None):
        self.hash = commit_hash
        self.message = message
        self.author = author
        self.parents = parents  # List of parent commit hashes
        self.branch = branch    # The active branch when this commit was made
        if timestamp:
            self.timestamp = timestamp
        else:
            self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==============================================================================
# SECTION 3. CORE ENGINE (Repository)
# ==============================================================================

class Repository:
    """
    Manages the repository state, branch pointers, commit graph, and indexes.
    """
    
    # ---------------------------------------------------------
    # 3-1. Engine Initialization & Hash Generator
    # ---------------------------------------------------------
    def __init__(self):
        self.is_initialized = False
        self.current_user = None
        self.commits = {}           # Mapping of commit_hash -> CommitNode
        self.branches = {}          # Mapping of branch_name -> commit_hash (pointing to tip)
        self.head = 'main'          # Current active branch name
        self.keyword_index = {}     # Inverted index for keywords: term -> list of hashes
        self.author_index = {}      # Inverted index for authors: author_name -> list of hashes
        self.commit_counter = 0     # For sequential, non-duplicate hash generation

    def generate_hash(self):
        """
        Generates a non-duplicating hash mimicking the 'a1b2c3', 'd4e5f6', 'g7h8i9' pattern.
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
    # 3-2. Version Control Command Handlers
    # ---------------------------------------------------------
    def init(self, user_name):
        """
        Initializes the repository with the specified user name and creates 'main' branch.
        """
        self.is_initialized = True
        self.current_user = user_name
        self.commits = {}
        self.branches = {'main': None}
        self.head = 'main'
        self.keyword_index = {}
        self.author_index = {}
        self.commit_counter = 0
        print("Initialized repository.")
        print(f"Current branch: {self.head}")
        print(f"Current user: {self.current_user}")

    def branch(self, branch_name):
        """
        Creates a new branch pointer pointing to the current commit of the active branch.
        """
        if branch_name in self.branches:
            print(f"Branch already exists: {branch_name}")
            return
        
        current_commit = self.branches[self.head]
        self.branches[branch_name] = current_commit
        print(f"Created branch: {branch_name}")

    def switch(self, branch_name):
        """
        Switches the current active branch (HEAD) to the specified branch.
        """
        if branch_name not in self.branches:
            print(f"Unknown branch: {branch_name}")
            return
        self.head = branch_name
        print(f"Switched to branch: {branch_name}")

    def commit(self, message, parents=None):
        """
        Creates a new commit, updates the active branch tip, and builds the inverted indexes.
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
        self.branches[self.head] = commit_hash

        # Update keyword index
        words = message.lower().split()
        for term in set(words):
            if term not in self.keyword_index:
                self.keyword_index[term] = []
            self.keyword_index[term].append(commit_hash)

        # Update author index
        author_key = self.current_user.lower()
        if author_key not in self.author_index:
            self.author_index[author_key] = []
        self.author_index[author_key].append(commit_hash)

        print(f"[{self.head} {commit_hash}] {message}")
        return commit_hash

    # ---------------------------------------------------------
    # 3-3. Inverted Index Search Engine
    # ---------------------------------------------------------
    def search_keyword(self, keyword):
        """
        Searches the inverted index for commits matching the keyword (case-insensitive).
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
        Searches the inverted index for commits by the specified author (case-insensitive).
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
    # 3-4. Graph Topology & History Traversal
    # ---------------------------------------------------------
    def log(self, sort_by=None):
        """
        Displays all commits. Under default mode, it displays them in root-first topological order.
        Under sorted mode, it uses custom merge sort based on date or author.
        """
        if not self.commits:
            return

        if sort_by is None:
            # Topological sort using Kahn's algorithm
            in_degree = {h: 0 for h in self.commits}
            children = {h: [] for h in self.commits}
            for h, node in self.commits.items():
                for p in node.parents:
                    if p in self.commits:
                        children[p].append(h)
                        in_degree[h] += 1

            # Get root commits
            roots = [h for h in self.commits if in_degree[h] == 0]
            # Deterministic queue ordering
            queue = merge_sort(roots, key=lambda h: (self.commits[h].timestamp, h))

            result = []
            while queue:
                curr = queue.pop(0)
                result.append(curr)
                for child in children[curr]:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        queue.append(child)
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
        Finds the shortest path between two commits considering commit connections as undirected.
        Tie-breaker: choose the lexicographically smallest path representation.
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

        # Build undirected graph adjacency list
        adj = {h: set() for h in self.commits}
        for h, node in self.commits.items():
            for p in node.parents:
                if p in self.commits:
                    adj[h].add(p)
                    adj[p].add(h)

        # BFS to find the shortest path
        queue = deque([[commit1]])
        visited = {commit1: 0}  # map node -> min path length to reach it
        shortest_paths = []
        shortest_length = None

        while queue:
            path = queue.popleft()
            curr = path[-1]

            if shortest_length is not None and len(path) > shortest_length:
                break

            if curr == commit2:
                shortest_length = len(path)
                shortest_paths.append(path)
                continue

            sorted_neighbors = merge_sort(list(adj[curr]), key=lambda x: x)
            for neighbor in sorted_neighbors:
                new_dist = len(path)
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

        # Tie-breaker logic (choose lexicographically smallest string)
        best_path_str, best_path = path_strings[0]
        for p_str, p in path_strings[1:]:
            if p_str < best_path_str:
                best_path_str = p_str
                best_path = p

        print(f"Path: {best_path_str}")

    def ancestors(self, commit_hash):
        """
        Finds all ancestor commits of the specified commit.
        """
        if commit_hash not in self.commits:
            print(f"Unknown commit: {commit_hash}")
            return

        visited = set()
        stack = []
        start_node = self.commits[commit_hash]
        for p in start_node.parents:
            if p in self.commits and p not in visited:
                visited.add(p)
                stack.append(p)

        ancestor_list = []
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

        # Sort ancestors chronologically (by timestamp, then hash)
        sorted_ancestors = merge_sort(ancestor_list, key=lambda h: (self.commits[h].timestamp, h))
        print("Ancestors:")
        for h in sorted_ancestors:
            node = self.commits[h]
            print(f"- {h}: {node.message}")

    # ---------------------------------------------------------
    # 3-5. Advanced Graph Operations (Merge Branch)
    # ---------------------------------------------------------
    def merge_branch(self, branch_name):
        """
        Merges the target branch into the current branch by creating a merge commit.
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

        # Create merge commit
        msg = f"Merge branch '{branch_name}' into {self.head}"
        parents = [parent1, parent2]
        self.commit(message=msg, parents=parents)


# ==============================================================================
# SECTION 4. BONUS UTILITIES (File Diff - LCS DP)
# ==============================================================================

def diff_command(file1, file2):
    """
    Compares two files line by line using standard LCS DP algorithm.
    Displays deletions with '-', additions with '+', and identical lines with ' '.
    """
    if not os.path.exists(file1):
        print(f"File not found: {file1}")
        return
    if not os.path.exists(file2):
        print(f"File not found: {file2}")
        return

    try:
        with open(file1, 'r', encoding='utf-8') as f:
            lines1 = [line.rstrip('\r\n') for line in f]
        with open(file2, 'r', encoding='utf-8') as f:
            lines2 = [line.rstrip('\r\n') for line in f]
    except Exception as e:
        print(f"Error reading files: {e}")
        return

    m, n = len(lines1), len(lines2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if lines1[i-1] == lines2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])

    # Backtracking to reconstruct the diff
    i, j = m, n
    diff = []
    while i > 0 or j > 0:
        if i > 0 and j > 0 and lines1[i-1] == lines2[j-1]:
            diff.append(f"  {lines1[i-1]}")
            i -= 1
            j -= 1
        elif j > 0 and (i == 0 or dp[i][j-1] >= dp[i-1][j]):
            diff.append(f"+ {lines2[j-1]}")
            j -= 1
        else:
            diff.append(f"- {lines1[i-1]}")
            i -= 1

    diff.reverse()
    for line in diff:
        print(line)


# ==============================================================================
# SECTION 5. INTERACTIVE CONSOLE (REPL - Main Loop)
# ==============================================================================

def main():
    repo = Repository()

    while True:
        try:
            line = input("mini-git> ").strip()
            if not line:
                continue

            # Command line tokenization supporting double quotes
            try:
                tokens = shlex.split(line)
            except ValueError:
                print("Invalid args")
                continue

            if not tokens:
                continue

            cmd = tokens[0].upper()
            args = tokens[1:]

            # Route commands
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

            elif cmd == "DIFF":
                if len(args) != 2:
                    print("Invalid args")
                else:
                    diff_command(args[0], args[1])

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
