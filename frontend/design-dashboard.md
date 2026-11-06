# Cambio de alcance del frontend — 2026-11-06

El usuario solicitó rediseñar el inicio del productor siguiendo la identidad de la landing y usando ForestTrace AI como referencia de composición.

- Mostrar lotes rastreados, volumen homologado, conformidad EUDR y alertas territoriales.
- Incluir la distribución de una matriz de riesgo y una tabla con código/especie, origen/CAR, volumen, estado/riesgo y motivo del aviso.
- Conservar las rutas existentes, el resumen ambiental y el nivel público del CNPJ.
- Incorporar búsqueda y filtros locales sobre los datos visibles de la tabla.

## Límite confirmado de esta implementación

Solo frontend; no se modifica el backend ni sus contratos. La API actual no ofrece lotes, homologación de volúmenes, conformidad EUDR ni clasificación determinística de riesgo. En la vista autenticada esos campos se muestran como no disponibles, nunca como cero. Las alertas territoriales conservan el conteo de alertas de desmonte recibido del dashboard, con su fuente y fecha.

La ruta de desarrollo `/preview/painel` muestra un escenario ficticio de tres lotes. Los indicadores y las clasificaciones se suministran explícitamente como fixtures de diseño; no implementan un método real de scoring, una validación legal EUDR ni una certificación. El módulo y sus fixtures se excluyen del build de producción. La información privada permanece en la vista autenticada; la consulta pública no recibe nuevos campos.

## Validación manual

1. Ejecutar `npm run dev` y abrir `/preview/painel` sin backend.
2. Comprobar la advertencia de datos ficticios, los cuatro indicadores, la matriz y los tres lotes.
3. Filtrar por riesgo elevado: aparecen dos lotes. Buscar `jatoba`: aparece solamente el lote de jatobá.
4. Buscar un término inexistente y limpiar los filtros para recuperar todos los lotes.
5. Revisar en desktop y en móvil: la tabla tiene desplazamiento horizontal propio y los indicadores se reorganizan.
6. Con sesión real, verificar que no aparecen los lotes de demostración y que los campos sin fuente se indican como no disponibles.
