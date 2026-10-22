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
