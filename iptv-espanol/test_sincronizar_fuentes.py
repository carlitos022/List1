#!/usr/bin/env python3
"""Pruebas offline de deteccion, validacion y generacion de IPTV."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import generar_listas as generador
import sincronizar_fuentes as sync


def lista(cuantos: int, pais: str = "es", sufijo: str = "") -> str:
    lineas = ["#EXTM3U"]
    for i in range(cuantos):
        lineas.extend([
            f'#EXTINF:-1 tvg-id="Canal{i}.{pais}@SD" group-title="sports",Canal {i}{sufijo}',
            f"https://example.org/live/{pais}/{i}.m3u8",
        ])
    return "\n".join(lineas) + "\n"


class SincronizacionTests(unittest.TestCase):
    def test_fuente_html_rechazada(self):
        with self.assertRaises(ValueError):
            sync.validar_fuente("<html>error</html>", "spa", 1)

    def test_fuente_incompleta_rechazada(self):
        with self.assertRaises(ValueError):
            sync.validar_fuente(lista(2), "spa", 10)

    def test_caida_anomala_rechazada(self):
        with self.assertRaises(ValueError):
            sync.validar_reduccion(1000, 2402)
        sync.validar_reduccion(2300, 2402)

    def test_regenerar_solo_si_cambia_original(self):
        with tempfile.TemporaryDirectory(prefix="iptv-test-") as carpeta:
            root = Path(carpeta)
            target = root / "iptv-espanol"
            target.mkdir()
            for nombre in ("generar_listas.py", "filtrar_muertos.py"):
                shutil.copy2(Path(generador.__file__).parent / nombre, target / nombre)
            (target / "dead_urls.txt").write_text("", encoding="utf-8")
            # 600 canales, incluidos 20 de Ecuador. Simula fuentes validas.
            espanol = lista(580, "es") + "\n".join(lista(20, "ec").splitlines()[1:]) + "\n"
            respuestas = {
                generador.SOURCE: espanol,
                generador.EXTRA_CATEGORY_SOURCES["PELICULAS"]: lista(12, "es"),
                generador.EXTRA_CATEGORY_SOURCES["SERIES"]: lista(12, "es"),
                generador.FREE_TV_SOURCE: lista(110, "ar"),
            }
            salidas = {
                nombre: ((root / nombre) if nombre == "tv.m3u" else (target / nombre), minimo)
                for nombre, (_, minimo) in sync.OUTPUTS.items()
            }
            with (
                patch.object(sync, "ROOT", root),
                patch.object(sync, "DIR", target),
                patch.object(sync, "STATE_FILE", target / "fuentes_estado.json"),
                patch.object(sync, "OUTPUTS", salidas),
                patch.object(generador, "download_url", side_effect=lambda url: respuestas[url]),
            ):
                sync.sincronizar(False)
                primero = (root / "tv.m3u").read_bytes()
                estado = json.loads((target / "fuentes_estado.json").read_text())
                self.assertEqual(estado["fuentes"]["spa.m3u"]["entradas"], 600)
                self.assertGreaterEqual(len(generador.parse_entries(primero.decode())), 600)
                self.assertTrue((target / "24-7.m3u").is_file())
                self.assertTrue((target / "peliculas.m3u").is_file())
                self.assertTrue((target / "series.m3u").is_file())

                # Mismo hash: no vuelve a generar.
                with patch.object(sync.subprocess, "run", side_effect=AssertionError("Se regenero sin cambios")):
                    sync.sincronizar(False)
                self.assertEqual((root / "tv.m3u").read_bytes(), primero)

                # Fuente actualizada: publica de nuevo.
                respuestas[generador.SOURCE] = espanol.replace("Canal 0", "Canal actualizado 0", 1)
                sync.sincronizar(False)
                self.assertNotEqual((root / "tv.m3u").read_bytes(), primero)


if __name__ == "__main__":
    unittest.main()
