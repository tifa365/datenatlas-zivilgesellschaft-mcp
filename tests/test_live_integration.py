import os
import unittest

import httpx

import tools


def _env(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _find_first(obj, keys):
    if isinstance(obj, dict):
        for key in keys:
            value = obj.get(key)
            if isinstance(value, str) and value:
                return value
        for value in obj.values():
            found = _find_first(value, keys)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_first(item, keys)
            if found:
                return found
    return None


def _find_dataset_id(search_result: dict) -> str | None:
    results = search_result.get("result", {}).get("results", [])
    for item in results:
        dataset_id = item.get("id")
        if isinstance(dataset_id, str) and dataset_id:
            return dataset_id
    return None


class LiveIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_live_search_datasets(self):
        query = _env("PIVEAU_LIVE_SEARCH_QUERY") or "berlin"
        result = await tools.search_datasets(q=query, filters=["dataset"], limit=3)

        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    async def test_live_search_datasets_advanced(self):
        query = _env("PIVEAU_LIVE_SEARCH_QUERY") or "berlin"
        result = await tools.search_datasets_advanced(
            q=query,
            filters=["dataset"],
            limit=3,
            includes=["id", "title", "description"],
            show_score=True,
            aggregation=True,
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    async def test_live_autocomplete_location(self):
        query = _env("PIVEAU_LIVE_AUTOCOMPLETE_QUERY") or "ber"
        try:
            result = await tools.autocomplete_location(query)
        except RuntimeError as exc:
            if "/gazetteer/autocomplete" in str(exc) and "500" in str(exc):
                self.skipTest(f"upstream autocomplete unavailable: {exc}")
            raise

        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    async def test_live_scroll_search(self):
        query = _env("PIVEAU_LIVE_SEARCH_QUERY") or "berlin"
        initial = await tools.search_datasets(q=query, filters=["dataset"], limit=1, scroll=True)

        scroll_id = _env("PIVEAU_LIVE_SCROLL_ID") or _find_first(initial, {"scrollId", "_scroll_id"})
        if not scroll_id:
            self.skipTest("live server did not return a scroll id; set PIVEAU_LIVE_SCROLL_ID to force this test")

        result = await tools.scroll_search(scroll_id)
        self.assertIsInstance(result, dict)

    async def test_live_get_dataset_details(self):
        dataset_id = _env("PIVEAU_LIVE_DATASET_ID")

        if not dataset_id:
            query = _env("PIVEAU_LIVE_SEARCH_QUERY") or "berlin"
            search_result = await tools.search_datasets(q=query, filters=["dataset"], limit=3)
            dataset_id = _find_dataset_id(search_result) or _find_first(search_result, {"id"})

        if not dataset_id:
            self.skipTest("no dataset id available; set PIVEAU_LIVE_DATASET_ID to run this test deterministically")

        try:
            result = await tools.get_dataset_details(dataset_id)
        except httpx.TimeoutException as exc:
            self.skipTest(f"dataset detail endpoint timed out for {dataset_id}: {exc}")
        self.assertIsInstance(result, dict)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
