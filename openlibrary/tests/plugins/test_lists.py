"""Tests for openlibrary.plugins.openlibrary.lists."""

from unittest.mock import MagicMock, patch

import pytest
import web

from openlibrary.core.lists.model import List
from openlibrary.plugins.openlibrary.lists import (
    _get_recently_modified_lists,
    _preload_lists,
    convert_list,
    export,
    feeds,
    get_active_lists_in_random,
    lists,
    lists_edit,
    lists_embed,
)


@pytest.fixture(autouse=True)
def setup_web_ctx():
    """Ensure web.ctx has required standard attributes initialized for testing."""
    web.ctx.headers = []
    web.ctx.fullpath = "/people/jane/lists/OL1L"
    web.ctx.env = {}


class TestPluginsListsSiteContext:
    """Ensure plugin lists functions use the request-scoped site context."""

    def test_convert_list_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site._load.return_value = {"key": "/people/jane/lists/OL1L", "name": "Favorites"}

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            result = convert_list("/people/jane/lists/OL1L")

        mock_site_var.get.assert_called()
        current_site._load.assert_called_once_with("/people/jane/lists/OL1L")
        assert isinstance(result, List)
        assert result.key == "/people/jane/lists/OL1L"

    def test_preload_lists_uses_request_scoped_site(self):
        current_site = MagicMock()
        lists_data = [
            {"key": "/people/jane/lists/OL1L", "seeds": [{"key": "/works/OL1W"}]},
            {"key": "/people/john/lists/OL2L", "seeds": [{"key": "/works/OL2W"}]},
        ]

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            _preload_lists(lists_data)

        mock_site_var.get.assert_called()
        assert current_site.get_many.called
        requested_keys = current_site.get_many.call_args[0][0]
        assert "/people/jane" in requested_keys
        assert "/people/john" in requested_keys
        assert "/works/OL1W" in requested_keys
        assert "/works/OL2W" in requested_keys

    def test_get_recently_modified_lists_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.things.return_value = ["/people/jane/lists/OL1L"]
        mock_list = MagicMock()
        mock_list.dict.return_value = {"key": "/people/jane/lists/OL1L", "name": "Jane's List"}
        current_site.get_many.return_value = [mock_list]

        with (
            patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var,
            patch("infogami.utils.delegate.fakeload"),
            patch("openlibrary.plugins.openlibrary.lists.set_context_from_legacy_web_py"),
        ):
            mock_site_var.get.return_value = current_site
            result = _get_recently_modified_lists(limit=5, offset=0)

        mock_site_var.get.assert_called()
        current_site.things.assert_called_once_with(
            {
                "type": "/type/list",
                "sort": "-last_modified",
                "limit": 5,
                "offset": 0,
            }
        )
        current_site.get_many.assert_called_once_with(["/people/jane/lists/OL1L"])
        assert result == [{"key": "/people/jane/lists/OL1L", "name": "Jane's List"}]

    def test_get_doc_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.get.return_value = MagicMock()

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            handler = lists()
            result = handler.get_doc("/people/jane")

        mock_site_var.get.assert_called()
        current_site.get.assert_called_once_with("/people/jane")
        assert result == current_site.get.return_value

    def test_lists_edit_permission_denied_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.can_write.return_value = False

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            with patch("openlibrary.plugins.openlibrary.lists.render_template") as mock_render:
                mock_render.return_value = "Permission Denied"
                handler = lists_edit()
                res = handler.GET("/people/jane", "lists", "OL1L")

        mock_site_var.get.assert_called()
        current_site.can_write.assert_called_once_with("/people/jane/lists/OL1L")
        assert res == "Permission Denied"

    def test_lists_embed_uses_request_scoped_site(self):
        current_site = MagicMock()
        mock_doc = MagicMock()
        mock_doc.type.key = "/type/list"
        current_site.get.return_value = mock_doc

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            with patch("openlibrary.plugins.openlibrary.lists.render_template") as mock_render:
                mock_render.return_value = "<iframe src='...'></iframe>"
                handler = lists_embed()
                res = handler.GET("/people/jane/lists/OL1L")

        mock_site_var.get.assert_called()
        current_site.get.assert_called_once_with("/people/jane/lists/OL1L")
        assert res == "<iframe src='...'></iframe>"

    def test_export_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.get.return_value = None

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            handler = export()
            with pytest.raises(web.HTTPError):
                handler.GET("/people/jane/lists/OL1L")

        mock_site_var.get.assert_called()
        current_site.get.assert_called_once_with("/people/jane/lists/OL1L")

    def test_feeds_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.get.return_value = None

        with patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var:
            mock_site_var.get.return_value = current_site
            handler = feeds()
            with pytest.raises(web.HTTPError):
                handler.GET("/people/jane/lists/OL1L", "updates", "atom")

        mock_site_var.get.assert_called()
        current_site.get.assert_called_once_with("/people/jane/lists/OL1L")

    def test_get_active_lists_in_random_uses_request_scoped_site(self):
        current_site = MagicMock()
        current_site.new.return_value = MagicMock()

        with (
            patch("openlibrary.plugins.openlibrary.lists.site") as mock_site_var,
            patch(
                "openlibrary.core.cache.memcache_memoize",
                return_value=lambda limit, preload: [{"key": "/people/jane/lists/OL1L"}],
            ),
        ):
            mock_site_var.get.return_value = current_site
            result = get_active_lists_in_random(limit=1, preload=False)

        mock_site_var.get.assert_called()
        current_site.new.assert_called_once_with("/people/jane/lists/OL1L", {"key": "/people/jane/lists/OL1L"})
        assert len(result) == 1
