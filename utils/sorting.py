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
