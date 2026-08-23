"""리스트 선형 탐색 vs 커스텀 해시맵 조회 비교.

일반 Python 리스트를 for문으로 순회하는 O(N) 조회와
커스텀 HashMap의 평균 O(1) 조회를 충분한 요소 수로 비교한다.

데이터가 늘어날수록 선형 탐색 비용은 증가하지만
해시 조회 경로는 짧게 유지되는 차이를 관찰하기 위한 학습용 스크립트이다.

실행: python lookup_benchmark.py
"""

import time

from mini_redis.hash_map import HashMap

# ─── 설정 ───
NUM_ENTRIES = 50_000   # 저장할 (key, value) 쌍 수
NUM_LOOKUPS = 1_000    # 조회 반복 횟수
# 뒤쪽 키를 대상으로 탐색해야 리스트의 O(N) 특성이 드러난다
TARGET_INDEX = NUM_ENTRIES - 1


def build_data():
    """리스트와 해시맵에 동일한 데이터를 준비한다."""
    data_list = []
    data_map = HashMap(initial_capacity=64)

    for i in range(NUM_ENTRIES):
        key = f"key:{i}"
        value = f"value:{i}"
        data_list.append((key, value))
        data_map.put(key, value)

    return data_list, data_map


def list_linear_search(data_list, target_key):
    """리스트를 처음부터 순회하여 키를 찾는다. O(N)"""
    for key, value in data_list:
        if key == target_key:
            return value
    return None


def benchmark_list(data_list, target_key, repeats):
    """리스트 선형 탐색을 repeats회 반복하고 경과 시간을 반환한다."""
    start = time.perf_counter()
    for _ in range(repeats):
        list_linear_search(data_list, target_key)
    elapsed = time.perf_counter() - start
    return elapsed


def benchmark_hashmap(data_map, target_key, repeats):
    """커스텀 해시맵 조회를 repeats회 반복하고 경과 시간을 반환한다."""
    start = time.perf_counter()
    for _ in range(repeats):
        data_map.get(target_key)
    elapsed = time.perf_counter() - start
    return elapsed


def main():
    print(f"데이터 수: {NUM_ENTRIES:,}개")
    print(f"조회 반복: {NUM_LOOKUPS:,}회")
    print(f"대상 키: key:{TARGET_INDEX} (리스트 끝쪽)")
    print("-" * 50)

    data_list, data_map = build_data()
    target_key = f"key:{TARGET_INDEX}"

    # 정합성 확인
    assert list_linear_search(data_list, target_key) == data_map.get(target_key)

    list_time = benchmark_list(data_list, target_key, NUM_LOOKUPS)
    map_time = benchmark_hashmap(data_map, target_key, NUM_LOOKUPS)

    print(f"리스트 선형 탐색: {list_time:.4f}초")
    print(f"해시맵 조회:      {map_time:.4f}초")
    print(f"속도 차이:        약 {list_time / map_time:.1f}배")
    print("-" * 50)
    print("리스트는 O(N), 해시맵은 평균 O(1)이므로")
    print("데이터가 많을수록 차이가 커진다.")


if __name__ == "__main__":
    main()
