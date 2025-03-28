import pytest
from pinecone import Vector, SparseValues
from ..helpers import poll_stats_for_namespace


@pytest.fixture(scope="class")
def seed_sparse_index(sparse_idx):
    sparse_idx.upsert(
        vectors=[
            Vector(
                id=str(i),
                sparse_values=SparseValues(
                    indices=[i, i * 2, i * 3], values=[i * 0.1, i * 0.2, i * 0.3]
                ),
            )
            for i in range(1000)
        ],
        batch_size=100,
        namespace="",
    )

    sparse_idx.upsert(
        vectors=[
            Vector(
                id=str(i),
                sparse_values=SparseValues(
                    indices=[i, i * 2, i * 3], values=[i * 0.1, i * 0.2, i * 0.3]
                ),
            )
            for i in range(1000)
        ],
        batch_size=100,
        namespace="nondefault",
    )

    print("seeding sparse index")
    poll_stats_for_namespace(sparse_idx, "", 1000, max_sleep=120)
    poll_stats_for_namespace(sparse_idx, "nondefault", 1000, max_sleep=120)

    yield


@pytest.mark.skip(reason="Sparse indexes are not yet supported")
@pytest.mark.usefixtures("seed_sparse_index")
class TestListPaginated_SparseIndex:
    def test_list_when_no_results(self, sparse_idx):
        results = sparse_idx.list_paginated(namespace="no-results")
        assert results is not None
        assert results.namespace == "no-results"
        assert len(results.vectors) == 0
        # assert results.pagination == None

    def test_list_no_args(self, sparse_idx):
        results = sparse_idx.list_paginated()

        assert results is not None
        assert len(results.vectors) == 9
        assert results.namespace == ""
        # assert results.pagination == None

    def test_list_when_limit(self, sparse_idx, list_namespace):
        results = sparse_idx.list_paginated(limit=10, namespace=list_namespace)

        assert results is not None
        assert len(results.vectors) == 10
        assert results.namespace == list_namespace
        assert results.pagination is not None
        assert results.pagination.next is not None
        assert isinstance(results.pagination.next, str)
        assert results.pagination.next != ""

    def test_list_when_using_pagination(self, sparse_idx, list_namespace):
        results = sparse_idx.list_paginated(prefix="99", limit=5, namespace=list_namespace)
        next_results = sparse_idx.list_paginated(
            prefix="99", limit=5, namespace=list_namespace, pagination_token=results.pagination.next
        )
        next_next_results = sparse_idx.list_paginated(
            prefix="99",
            limit=5,
            namespace=list_namespace,
            pagination_token=next_results.pagination.next,
        )

        assert results.namespace == list_namespace
        assert len(results.vectors) == 5
        assert [v.id for v in results.vectors] == ["99", "990", "991", "992", "993"]
        assert len(next_results.vectors) == 5
        assert [v.id for v in next_results.vectors] == ["994", "995", "996", "997", "998"]
        assert len(next_next_results.vectors) == 1
        assert [v.id for v in next_next_results.vectors] == ["999"]
        # assert next_next_results.pagination == None


@pytest.mark.skip(reason="Sparse indexes are not yet supported")
@pytest.mark.usefixtures("seed_sparse_index")
class TestList:
    def test_list_with_defaults(self, sparse_idx):
        pages = []
        page_sizes = []
        page_count = 0
        for ids in sparse_idx.list():
            page_count += 1
            assert ids is not None
            page_sizes.append(len(ids))
            pages.append(ids)

        assert page_count == 1
        assert page_sizes == [9]

    def test_list(self, sparse_idx, list_namespace):
        results = sparse_idx.list(prefix="99", limit=20, namespace=list_namespace)

        page_count = 0
        for ids in results:
            page_count += 1
            assert ids is not None
            assert len(ids) == 11
            assert ids == [
                "99",
                "990",
                "991",
                "992",
                "993",
                "994",
                "995",
                "996",
                "997",
                "998",
                "999",
            ]
        assert page_count == 1

    def test_list_when_no_results_for_prefix(self, sparse_idx, list_namespace):
        page_count = 0
        for ids in sparse_idx.list(prefix="no-results", namespace=list_namespace):
            page_count += 1
        assert page_count == 0

    def test_list_when_no_results_for_namespace(self, sparse_idx):
        page_count = 0
        for ids in sparse_idx.list(prefix="99", namespace="no-results"):
            page_count += 1
        assert page_count == 0

    def test_list_when_multiple_pages(self, sparse_idx, list_namespace):
        pages = []
        page_sizes = []
        page_count = 0

        for ids in sparse_idx.list(prefix="99", limit=5, namespace=list_namespace):
            page_count += 1
            assert ids is not None
            page_sizes.append(len(ids))
            pages.append(ids)

        assert page_count == 3
        assert page_sizes == [5, 5, 1]
        assert pages[0] == ["99", "990", "991", "992", "993"]
        assert pages[1] == ["994", "995", "996", "997", "998"]
        assert pages[2] == ["999"]

    def test_list_then_fetch(self, sparse_idx, list_namespace):
        vectors = []

        for ids in sparse_idx.list(prefix="99", limit=5, namespace=list_namespace):
            result = sparse_idx.fetch(ids=ids, namespace=list_namespace)
            vectors.extend([v for _, v in result.vectors.items()])

        assert len(vectors) == 11
        assert isinstance(vectors[0], Vector)
        assert set([v.id for v in vectors]) == set(
            ["99", "990", "991", "992", "993", "994", "995", "996", "997", "998", "999"]
        )
