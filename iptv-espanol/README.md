# IPTV en español clasificado

Listas derivadas automáticamente de la lista pública [IPTV-ORG](https://github.com/iptv-org/iptv).

## Listas disponibles

- `espanol.m3u`: clasificación combinada por país y categoría.
- `por-pais.m3u`: agrupada por país.
- `por-categoria.m3u`: agrupada por categoría.
- `ecuador.m3u`: canales identificados como Ecuador, agrupados por categoría.
- `espanol-paises-y-categorias.m3u`: lista combinada para TV.
- `../tv.m3u`: copia de la lista combinada, URL estable para Smart TV.

Prioridad de países: Ecuador, España, Colombia, México, Argentina, Perú, Chile y Venezuela; después otros países latinoamericanos y otros canales en español.

## Sincronización automática

El flujo [Sincronizar IPTV con fuentes originales](../.github/workflows/update-iptv-espanol.yml) consulta **cada 3 horas** (minuto 17 UTC) estas fuentes oficiales:

- https://iptv-org.github.io/iptv/languages/spa.m3u
- https://iptv-org.github.io/iptv/categories/movies.m3u
- https://iptv-org.github.io/iptv/categories/series.m3u

Compara sus huellas SHA-256 con `fuentes_estado.json` y no genera un nuevo commit si las tres fuentes son idénticas a las de la última sincronización exitosa. Antes de publicar valida el formato M3U, el número de canales y el contenido generado. Si alguna descarga falla o pierde más del 40 % de los canales españoles frente al último registro, **no reemplaza la última lista válida** y el trabajo aparece como fallido en GitHub Actions.

Para iniciar una actualización manual, entra en **GitHub → Actions → Sincronizar IPTV con fuentes originales → Run workflow**. Una ejecución manual fuerza la regeneración, incluso si las fuentes no cambiaron.

El archivo `dead_urls.txt` excluye enlaces previamente descartados. Estos enlaces siguen excluidos aunque la fuente original vuelva a incluirlos, hasta que se edite ese archivo.

## Enlace permanente para el reproductor

`https://raw.githubusercontent.com/carlitos022/List1/main/tv.m3u`

Los streams pertenecen a sus proveedores originales. Algunos pueden dejar de funcionar, estar geobloqueados o no emitir 24/7.

## Nueva oferta: 24/7, cine y series

- **Canales lineales 24/7:** `24-7.m3u`, combina señales en español de las categorías Películas/Series de IPTV-ORG con canales de `Free-TV/IPTV` seleccionados por país o variante española.
- **Películas:** `peliculas.m3u`, incorpora todos los candidatos en español de la fuente de películas, no solo los IDs manuales iniciales.
- **Series:** `series.m3u`, incorpora todos los candidatos en español de la fuente de series.
- **Lista combinada:** `../tv.m3u`, ahora con el grupo independiente `📡 24/7`.

Fuentes adicionales: https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8 y los dos grupos temáticos de IPTV-ORG. Solo se enlazan streams públicos; no se alojan contenidos ni se garantiza acceso geográfico.

**Importante:** la expresión "24/7" identifica señales lineales/candidatas a programación continua. Una auditoría puntual no puede demostrar 24 horas ininterrumpidas de reproducción. La categoría contiene señales de televisión en directo, no un catálogo de archivos de películas bajo demanda.

## Auditoría de disponibilidad

La acción [Auditar disponibilidad IPTV](../.github/workflows/auditar-iptv.yml) comprueba diariamente **todos los enlaces únicos publicados** desde la red de GitHub Actions. Descarga una pequeña muestra del manifiesto y, si es HLS, intenta consultar la variante y un segmento de vídeo. La prueba no garantiza que el canal funcione desde todos los países ni durante todo el día.

- **Accesible:** respuesta multimedia, o segmento HLS accesible.
- **Caído de forma concluyente:** HTTP 404/410, HTML o respuesta vacía; solo se excluye de las listas tras dos auditorías realizadas en días distintos.
- **Indeterminado:** HTTP 403, geobloqueo, timeout, fallo temporal o formato que no pueda certificarse. No se borra automáticamente.

Los resultados se conservan en `salud_canales.json` y en el resumen [REPORTE_SALUD.md](REPORTE_SALUD.md) (se genera en la primera auditoría completa). La lista manual `dead_urls.txt` sigue vigente. Todas las salidas y la URL habitual `tv.m3u` conservan sus rutas.

**Frecuencia:** fuentes cada 3 horas y prueba profunda una vez al día. Para ejecutarla de inmediato: pestaña **Actions**, flujo **Auditar disponibilidad IPTV (HLS)**, botón **Run workflow**.
