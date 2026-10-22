#!/usr/bin/env python3
"""Regresión editorial: 24/7 significa un solo programa, nunca TV general."""
from __future__ import annotations
import unittest
import canales_monoserie as mono
import generar_listas as generador

def e(id_, nombre, url="https://example.org/live.m3u8"):
    return {"tvg_id":id_, "name":nombre, "url":url,
            "extinf": f'#EXTINF:-1 tvg-id="{id_}" group-title="kids",{nombre}',
            "extras": [], "cc": "es", "original_group": "kids", "category": "Infancia"}


class MonoserieTests(unittest.TestCase):
    def test_franchises_reales(self):
        samples = [
            ("BobEsponja.de@ES", "Bob Esponja (720p)", "Bob Esponja"),
            ("BobEsponjaPantalonesCuadrados.us@LatAm", "Bob Esponja", "Bob Esponja"),
            ("AvatarLaLeyendadeAang.us@LatAm", "Avatar", "Avatar: La Leyenda de Aang"),
            ("Ben10.us@LatAm", "Ben 10", "Ben 10"),
            ("DragonBallSuper.us@LatAm", "Dragon Ball Super", "Dragon Ball Super"),
            ("TheWalkingDead.us@LatAm", "The Walking Dead", "The Walking Dead"),
            ("Futurama.us@LatAm", "Futurama", "Futurama"),
            ("iCarly.us@LatAm", "iCarly", "iCarly"),
            ("Rugrats.de@ES", "Rugrats", "Rugrats"),
            ("CSIMiami.us@LatAm", "CSI: Miami", "CSI: Miami"),
        ]
        for index, (identifier, name, expected) in enumerate(samples):
            with self.subTest(name=name):
                got = mono.identificar(e(identifier, name, f"https://example.org/{index}.m3u8"))
                self.assertIsNotNone(got)
                self.assertEqual(got[0], expected)

    def test_canales_especificos_pluto_por_pais(self):
        cases = [
            ("", "Dragon Ball Z", "Dragon Ball Z"),
            ("", "Dragon Ball", "Dragon Ball"),
            ("", "Death Note", "Death Note"),
            ("", "Los Padrinos Mágicos", "Los padrinos mágicos"),
            ("", "Los Pitufos", "Los Pitufos"),
            ("", "Winx Club", "Winx Club"),
            ("", "Los caballeros del Zodiaco", "Los Caballeros del Zodiaco"),
            ("", "Pokémon en español", "Pokémon"),
            ("PlutoTVPokemon.us@US", "Pokémon", "Pokémon"),
            ("GarfieldandFriends.us@US", "Garfield and Friends", "Garfield y sus amigos"),
            ("TheWalkingDeadenEspanol.us@SD", "The Walking Dead en español", "The Walking Dead"),
            ("", "Qué Culpa Tiene Fatmagül", "¿Qué culpa tiene Fatmagül?"),
            ("", "Pocoyo (1080p)", "Pocoyó"),
        ]
        for index, (identifier, nombre, titulo) in enumerate(cases):
            with self.subTest(nombre=nombre):
                result = mono.identificar(e(identifier, nombre, f"https://example.org/{index}.m3u8"))
                self.assertIsNotNone(result)
                self.assertEqual(result[0], titulo)

    def test_genericos_y_falsos_positivos_no_entran(self):
        denied = [
            ("CanalNoticias.es@SD", "24 horas"),
            ("247CanaldeNoticias.ar@SD", "24/7 Canal Noticias"),
            ("NickelodeonLatinAmerica.us@SD", "Nickelodeon"),
            ("PlutoTVKids.us@LatAm", "Pluto TV Kids"),
            ("PlutoTVSeries.us@LatAm", "Pluto TV Series"),
            ("PlutoTVSciFi.us@LatAm", "Pluto TV Sci-Fi"),
            ("ElPinguinoTV.cl@SD", "El Pingüino TV"),
            ("StarTrek.us@LatAm", "Star Trek Latinoamérica"),
            ("CanalRandom.us@LatAm", "Bob Esponja Mix"),
        ]
        for identifier, name in denied:
            with self.subTest(name=name):
                self.assertIsNone(mono.identificar(e(identifier, name)))

    def test_no_repetir_episodios_por_feed_duplicado(self):
        common = "https://example.org/bob.m3u8"
        entries = [
            e("BobEsponja.de@ES", "Bob Esponja", common),
            e("BobEsponja.de@ES", "Bob Esponja", common),
            e("CanalNews.us@SD", "Noticias", "https://example.org/news.m3u8")
        ]
        chosen = mono.seleccionar(entries)
        self.assertEqual(len(chosen), 1)
        self.assertEqual(chosen[0]["titulo_247"], "Bob Esponja")
        self.assertIn("Infancia", chosen[0]["grupo_247"])

    def test_metadatos_con_coma_tienen_nombre_valido(self):
        data = ('#EXTM3U\n'
                '#EXTINF:-1 tvg-id="BobEsponja.de@ES" http-user-agent="Mozilla/5.0, foo" '
                'group-title="kids",Bob Esponja\n'
                'https://example.org/bob.m3u8\n')
        entries = generador.parse_entries(data)
        self.assertEqual(entries[0]["name"], "Bob Esponja")


if __name__ == "__main__":
    unittest.main()
