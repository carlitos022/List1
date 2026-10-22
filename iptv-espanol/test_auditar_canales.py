#!/usr/bin/env python3
"""Pruebas aisladas del auditor de IPTV, sin depender de internet."""
from __future__ import annotations

from datetime import date
import io
from pathlib import Path
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import auditar_canales as health
import generar_listas as gen


class AuditorTests(unittest.TestCase):
    def test_rechaza_redes_privadas(self):
        for url in ("http://127.0.0.1:8080/live.m3u8",
                    "http://10.0.0.8/live.m3u8",
                    "http://169.254.169.254/latest/"):
            self.assertFalse(health.public_url(url))
        self.assertTrue(health.public_url("https://example.org/stream.m3u8"))

    def test_404_caido_y_403_indeterminado(self):
        for status, expected in [(404, "down"), (410, "down"), (403, "unknown")]:
            with self.subTest(status=status):
                err = urllib.error.HTTPError(
                    "https://example.org/test.m3u8", status,
                    "error", {}, io.BytesIO()
                )
                with patch.object(health, "get_sample", side_effect=err):
                    actual, _ = health.check_stream("https://example.org/test.m3u8")
                self.assertEqual(actual, expected)

    def test_hls_master_segmento_real(self):
        def fake_get(url, timeout):
            if url.endswith("master.m3u8"):
                return 200, "application/vnd.apple.mpegurl", (
                    b"#EXTM3U\n#EXT-X-STREAM-INF:BANDWIDTH=1234\nsub/index.m3u8\n"
                ), url
            if url.endswith("index.m3u8"):
                return 200, "application/vnd.apple.mpegurl", (
                    b"#EXTM3U\n#EXT-X-TARGETDURATION:6\n#EXTINF:6,\nsegment.ts\n"
                ), url
            return 206, "video/mp2t", b"\x47" * 188, url
        with patch.object(health, "get_sample", side_effect=fake_get):
            status, _ = health.check_stream("https://example.org/master.m3u8")
        self.assertEqual(status, "up")

    def test_dos_dias_para_eliminar(self):
        first = health.update_record({}, "down", "HTTP 404", "2026-10-21")
        self.assertEqual(first["consecutive_down"], 1)
        same_day = health.update_record(first, "down", "HTTP 404", "2026-10-21")
        self.assertEqual(same_day["consecutive_down"], 1)
        second = health.update_record(same_day, "down", "HTTP 404", "2026-10-22")
        self.assertEqual(second["consecutive_down"], 2)
        uncertain = health.update_record(second, "unknown", "geo", "2026-10-23")
        self.assertEqual(uncertain["consecutive_down"], 2)
        healthy = health.update_record(uncertain, "up", "HLS OK", "2026-10-24")
        self.assertEqual(healthy["consecutive_down"], 0)

    def test_playlist_estricta_solo_publica_probados(self):
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "all.m3u"
            out = Path(tmp) / "verified.m3u"
            inp.write_text(
                '#EXTM3U\n'
                '#EXTINF:-1 group-title="24/7",Canal vivo\n'
                'https://example.org/good.m3u8\n'
                '#EXTINF:-1 group-title="24/7",Canal caído\n'
                'https://example.org/bad.m3u8\n',
                encoding="utf-8",
            )
            with patch.object(health, "VERIFIED_PLAYLISTS", {inp: out}):
                counts = health.write_verified_only({
                    "https://example.org/good.m3u8": "up",
                    "https://example.org/bad.m3u8": "unknown",
                })
            self.assertEqual(counts[out.name], 1)
            text = out.read_text(encoding="utf-8")
            self.assertIn("good.m3u8", text)
            self.assertNotIn("bad.m3u8", text)

    def test_tv_espanol_sin_paginas_web(self):
        entry = {"cc": "es", "tvg_id": "Test.es@SD",
                 "url": "https://example.org/live.m3u8", "name": "Test"}
        self.assertTrue(gen.is_spanish(entry))
        self.assertTrue(gen.is_stream(entry))
        self.assertFalse(gen.is_stream({**entry, "url": "https://youtube.com/live/abc"}))
        self.assertEqual(len(gen.distinct([entry, entry])), 1)


if __name__ == "__main__":
    unittest.main()
