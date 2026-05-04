# Documento de Requisitos — Backend MVP

## Introducción

Este documento define los requisitos del backend para el MVP de una plataforma de diseño interior con IA orientada a empresas de construcción e inmobiliarias. El objetivo es demostrar la viabilidad de generar variantes de diseño interior mediante inteligencia artificial a partir de imágenes reales de espacios. El backend expone una API REST construida con FastAPI bajo el prefijo `/api/v1/`, utiliza PostgreSQL como base de datos, Redis + Celery para procesamiento asíncrono, y almacenamiento local en sistema de archivos (volumen Docker) para imágenes. Todo el stack se levanta con Docker Compose, preparado para deploy en staging y producción. La arquitectura sigue el patrón Hexagonal (Ports & Adapters) con Clean Architecture. Este documento cubre el alcance completo del backend MVP; la división en fases de implementación se realizará posteriormente.

**Decisiones arquitectónicas tomadas para este MVP:**
- Autenticación: fuera del MVP. Se agrega `owner_id` (nullable) a `Project` como preparación para multi-tenancy futuro.
- Rate limiting: configurable por variables de entorno. Sin límites por defecto (desarrollo/testing). Preparado para activar límites cuando haya grupo de testers.
- Observabilidad: logs JSON estructurados con `structlog` + `correlation_id` propagado en cada request y tarea worker.
- Versionado de API: prefijo `/api/v1/` en todos los endpoints desde el inicio.
- Paginación: offset/limit en todos los endpoints de listado desde el inicio.

## Glosario

- **API**: Interfaz de programación de aplicaciones REST expuesta por el backend FastAPI.
- **Proyecto**: Entidad principal que agrupa imágenes y generaciones relacionadas con un inmueble o espacio.
- **ImageAsset**: Registro de metadatos de una imagen (original o generada) almacenada en el sistema.
- **Imagen_Original**: Imagen subida por el usuario que sirve como base para generaciones.
- **Imagen_Generada**: Imagen producida por un proveedor de IA a partir de una imagen original.
- **SceneInventory**: Inventario estructurado en JSON que describe los elementos visuales de una escena (mobiliario, arquitectura, decoración, candidatos editables, reglas de preservación).
- **GenerationRequest**: Solicitud de generación de una variante de imagen mediante IA, con modo, preset, instrucciones y proveedor.
- **Modo_de_Generación**: Tipo de transformación solicitada: commercial_enhancement, style_redesign, functional_variant o localized_edit.
- **Preset**: Plantilla predefinida de estilo o transformación (ej: modern_mediterranean, premium_contemporary, localized_wall_art).
- **PromptBuilder**: Componente que construye el prompt final enviado al proveedor de IA a partir del modo, preset, instrucciones del usuario, inventario de escena y reglas de preservación.
- **Proveedor_IA**: Servicio externo de generación de imágenes (OpenAI Images API como primario, FLUX como secundario opcional).
- **ProviderRouter**: Componente que enruta solicitudes de generación al proveedor de IA correspondiente sin acoplar el sistema a un proveedor específico.
- **ImageVariant**: Registro de una variante generada, vinculada a la imagen fuente, la solicitud de generación, con número de versión y metadatos del proveedor.
- **Evaluación**: Valoración manual de una variante generada con puntuaciones en múltiples dimensiones y un veredicto final.
- **Worker**: Proceso Celery que ejecuta tareas asíncronas (análisis de escena, generación de imágenes).
- **Storage**: Servicio de almacenamiento de imágenes. En el MVP utiliza el sistema de archivos local (volumen Docker). La interfaz StorageService está abstraída para permitir migración futura a S3/Cloudflare R2 sin cambios en la lógica de negocio.
- **Thumbnail**: Versión reducida de una imagen generada automáticamente al subir o generar una imagen.
- **URL_Servida**: URL generada por la API que sirve el archivo directamente desde el almacenamiento local. En el MVP, la API expone un endpoint de archivos estáticos; en producción futura se puede migrar a URLs firmadas de S3/R2.
- **owner_id**: Campo UUID nullable en `Project` que identifica al propietario del proyecto. Nullable en el MVP (sin auth). Preparado para multi-tenancy cuando se implemente autenticación.
- **Correlation_ID**: Identificador único generado por request HTTP y propagado a todos los logs y tareas Celery asociadas, permitiendo trazar un flujo completo de punta a punta.
- **Rate_Limit**: Límite configurable de generaciones por período. Desactivado por defecto (sin límites) para desarrollo y testing. Activable por variables de entorno cuando haya grupo de testers o producción.

## Requisitos

### Requisito 1: Gestión de Proyectos

**Historia de Usuario:** Como usuario de la plataforma, quiero crear y gestionar proyectos inmobiliarios, para organizar las imágenes y generaciones por espacio o propiedad.

#### Criterios de Aceptación

1. WHEN el usuario envía una solicitud POST /api/v1/projects con nombre y descripción válidos, THE API SHALL crear un Proyecto y retornar el recurso creado con id, nombre, descripción, owner_id, created_at y updated_at.
2. WHEN el usuario envía una solicitud GET /api/v1/projects, THE API SHALL retornar la lista paginada de todos los Proyectos existentes con campos page, page_size, total y items.
3. WHEN el usuario envía una solicitud GET /api/v1/projects/{project_id} con un project_id existente, THE API SHALL retornar el Proyecto correspondiente con todos sus campos.
4. WHEN el usuario envía una solicitud PATCH /api/v1/projects/{project_id} con campos actualizados, THE API SHALL actualizar únicamente los campos proporcionados y retornar el Proyecto actualizado.
5. WHEN el usuario envía una solicitud DELETE /api/v1/projects/{project_id} con un project_id existente, THE API SHALL eliminar el Proyecto y retornar confirmación de eliminación.
6. IF el usuario envía una solicitud con un project_id inexistente, THEN THE API SHALL retornar un error HTTP 404 con un mensaje descriptivo.
7. IF el usuario envía una solicitud POST /api/v1/projects sin nombre, THEN THE API SHALL retornar un error HTTP 422 con detalle de validación.
8. THE Project entity SHALL incluir un campo owner_id (UUID, nullable) para preparar la futura implementación de autenticación y multi-tenancy sin modificar el schema.

---

### Requisito 2: Subida de Imágenes Originales

**Historia de Usuario:** Como usuario de la plataforma, quiero subir imágenes de interiores a un proyecto, para usarlas como base de generaciones con IA.

#### Criterios de Aceptación

1. WHEN el usuario envía una solicitud POST /projects/{project_id}/images con un archivo de imagen válido, THE API SHALL subir el archivo a Storage, generar un Thumbnail, crear un registro ImageAsset con type "original" y retornar los metadatos de la imagen.
2. WHEN el usuario sube una imagen, THE API SHALL extraer y almacenar los metadatos: filename, mime_type, width, height y storage_path.
3. WHEN el usuario envía una solicitud GET /projects/{project_id}/images, THE API SHALL retornar la lista de todos los ImageAsset asociados al Proyecto (originales y generados).
4. WHEN el usuario envía una solicitud GET /images/{image_id} con un image_id existente, THE API SHALL retornar los metadatos completos del ImageAsset correspondiente.
5. WHEN el usuario envía una solicitud DELETE /images/{image_id}, THE API SHALL eliminar el registro ImageAsset y el archivo correspondiente en Storage.
6. IF el usuario sube un archivo con un tipo MIME no permitido (fuera de image/jpeg, image/png, image/webp), THEN THE API SHALL rechazar la solicitud con un error HTTP 422 indicando los tipos permitidos.
7. IF el usuario sube un archivo que excede el tamaño máximo configurado, THEN THE API SHALL rechazar la solicitud con un error HTTP 413 indicando el límite de tamaño.
8. IF el usuario referencia un project_id inexistente al subir una imagen, THEN THE API SHALL retornar un error HTTP 404.

---

### Requisito 3: Almacenamiento de Imágenes

**Historia de Usuario:** Como operador de la plataforma, quiero que las imágenes se almacenen de forma organizada y accesible mediante URLs servidas por la API, para gestionar los activos sin exponer rutas internas del sistema de archivos.

#### Criterios de Aceptación

1. THE API SHALL almacenar todas las imágenes (originales y generadas) en Storage local (volumen Docker) utilizando rutas internas que no se expongan al cliente.
2. WHEN el cliente solicita acceso a una imagen, THE API SHALL generar una URL_Servida que permita acceder al archivo a través de un endpoint de la API.
3. THE API SHALL generar un Thumbnail para cada imagen almacenada (original o generada) en el momento de su creación.
4. THE API SHALL nunca retornar rutas internas de Storage (storage_path) en las respuestas al cliente.
5. THE StorageService SHALL implementar una interfaz abstracta que permita reemplazar el almacenamiento local por S3/Cloudflare R2 en el futuro cambiando solo la configuración, sin modificar la lógica de negocio.

---

### Requisito 4: Inventario de Escena

**Historia de Usuario:** Como usuario de la plataforma, quiero analizar una imagen para obtener un inventario estructurado de la escena, para que el sistema pueda construir prompts más precisos y aplicar reglas de preservación.

#### Criterios de Aceptación

1. WHEN el usuario envía una solicitud POST /images/{image_id}/scene-inventory, THE API SHALL encolar una tarea asíncrona para analizar la imagen mediante un Proveedor_IA y generar un SceneInventory en formato JSON.
2. WHEN el Worker completa el análisis de escena, THE API SHALL almacenar el SceneInventory con los campos: scene_type, información de cámara, arquitectura (must_preserve), mobiliario, decoración, candidatos editables y reglas de preservación.
3. WHEN el usuario envía una solicitud GET /images/{image_id}/scene-inventory, THE API SHALL retornar el SceneInventory más reciente asociado a la imagen.
4. THE API SHALL registrar en el SceneInventory el proveedor y modelo utilizados para el análisis.
5. IF el Proveedor_IA retorna un error durante el análisis de escena, THEN THE API SHALL registrar el error y retornar un estado descriptivo al consultar el inventario.
6. IF el usuario solicita el inventario de una imagen que no tiene SceneInventory generado, THEN THE API SHALL retornar un error HTTP 404 indicando que no existe inventario para esa imagen.

---

### Requisito 5: Solicitudes de Generación

**Historia de Usuario:** Como usuario de la plataforma, quiero solicitar generaciones de variantes de diseño interior con IA, para explorar opciones comerciales y funcionales sobre mis imágenes.

#### Criterios de Aceptación

1. WHEN el usuario envía una solicitud POST /images/{image_id}/generations con modo, preset, instrucciones y proveedor, THE API SHALL crear un GenerationRequest con estado "pending" y encolar una tarea asíncrona para procesarla.
2. THE API SHALL soportar los siguientes modos de generación: commercial_enhancement, style_redesign, functional_variant y localized_edit.
3. WHEN el usuario envía una solicitud GET /generations/{generation_id}, THE API SHALL retornar el GenerationRequest con su estado actual y metadatos.
4. WHEN el usuario envía una solicitud GET /images/{image_id}/generations, THE API SHALL retornar la lista de todos los GenerationRequest asociados a la imagen.
5. THE API SHALL transicionar el estado del GenerationRequest a través de la secuencia: pending → analyzing → generating → completed, registrando cada cambio de estado.
6. IF ocurre un error durante el procesamiento de la generación, THEN THE API SHALL transicionar el estado a "failed" y registrar el mensaje de error.
7. IF el usuario solicita una generación con un modo no válido, THEN THE API SHALL retornar un error HTTP 422 indicando los modos permitidos.
8. IF el usuario solicita una generación para una imagen inexistente, THEN THE API SHALL retornar un error HTTP 404.

---

### Requisito 6: Construcción de Prompts

**Historia de Usuario:** Como sistema de generación, quiero construir prompts consistentes y específicos para cada modo de generación, para maximizar la calidad y relevancia de las imágenes generadas por IA.

#### Criterios de Aceptación

1. WHEN el Worker procesa un GenerationRequest, THE PromptBuilder SHALL recibir la imagen fuente, el modo de generación, el preset, las instrucciones del usuario, el SceneInventory (si existe) y las reglas de preservación, y retornar un prompt final, instrucciones de preservación/negativas y parámetros específicos del proveedor.
2. THE PromptBuilder SHALL mantener plantillas predefinidas para los siguientes presets: commercial_enhancement, modern_mediterranean, premium_contemporary, urban_contemporary, living_tv_wall, dining_room, home_office_lounge, localized_wall_art, localized_sofa, localized_rug, localized_tv_cabinet, localized_remove_plants y localized_wall_color.
3. WHEN el modo es localized_edit, THE PromptBuilder SHALL incluir en el prompt las reglas de preservación del SceneInventory para proteger los elementos que no deben modificarse.
4. THE PromptBuilder SHALL generar parámetros específicos adaptados al Proveedor_IA seleccionado (OpenAI o FLUX).
5. THE PromptBuilder SHALL registrar el prompt final construido para cada generación, permitiendo trazabilidad y reproducibilidad parcial.

---

### Requisito 7: Enrutamiento de Proveedores de IA

**Historia de Usuario:** Como operador de la plataforma, quiero que el sistema soporte múltiples proveedores de IA sin acoplamiento, para poder agregar o cambiar proveedores sin reescribir la lógica de generación.

#### Criterios de Aceptación

1. THE ProviderRouter SHALL implementar una interfaz ImageGenerationProvider con los métodos generate_variant() y analyze_scene().
2. THE ProviderRouter SHALL soportar OpenAI Images API como Proveedor_IA primario.
3. WHERE FLUX está configurado como proveedor secundario, THE ProviderRouter SHALL enrutar solicitudes a FLUX cuando el usuario lo especifique.
4. WHEN el Worker invoca al ProviderRouter, THE ProviderRouter SHALL registrar el proveedor y modelo utilizados, el prompt final enviado, y la respuesta o error recibido.
5. THE ProviderRouter SHALL permitir agregar nuevos proveedores implementando la interfaz ImageGenerationProvider sin modificar la lógica existente de generación.
6. IF el Proveedor_IA seleccionado no está disponible o retorna un error, THEN THE ProviderRouter SHALL registrar el error con detalle suficiente para diagnóstico.

---

### Requisito 8: Almacenamiento y Versionado de Variantes

**Historia de Usuario:** Como usuario de la plataforma, quiero que cada imagen generada se almacene como una nueva versión vinculada a la imagen original, para mantener un historial completo sin perder ningún resultado.

#### Criterios de Aceptación

1. WHEN el Worker completa una generación exitosa, THE API SHALL crear un nuevo ImageAsset con type "generated" y un ImageVariant vinculado a la imagen fuente y al GenerationRequest.
2. WHEN se crea un ImageVariant, THE API SHALL asignar un version_number incremental respecto a las variantes existentes de la misma imagen fuente.
3. THE API SHALL almacenar en el ImageVariant el proveedor, modelo, label y storage_path de la imagen generada.
4. THE API SHALL generar un Thumbnail para cada imagen generada en el momento de su creación.
5. THE API SHALL nunca sobrescribir una Imagen_Original ni una Imagen_Generada existente; cada generación produce un nuevo registro.

---

### Requisito 9: Comparación de Imágenes

**Historia de Usuario:** Como usuario de la plataforma, quiero comparar la imagen original con las variantes generadas, para evaluar visualmente los cambios realizados por la IA.

#### Criterios de Aceptación

1. WHEN el usuario solicita la comparación de una imagen, THE API SHALL retornar la Imagen_Original y la lista de ImageVariant asociadas, cada una con su URL_Servida correspondiente.
2. WHEN el usuario solicita las variantes de una imagen fuente, THE API SHALL retornar las variantes ordenadas por version_number ascendente.
3. THE API SHALL incluir en cada variante retornada los metadatos del GenerationRequest asociado (modo, preset, proveedor) para contexto de la comparación.

---

### Requisito 10: Evaluación Manual de Resultados

**Historia de Usuario:** Como usuario de la plataforma, quiero evaluar manualmente cada variante generada con puntuaciones en múltiples dimensiones, para determinar la viabilidad comercial de cada resultado.

#### Criterios de Aceptación

1. WHEN el usuario envía una solicitud POST /image-variants/{variant_id}/evaluation con puntuaciones y veredicto, THE API SHALL crear una Evaluación asociada al ImageVariant.
2. THE API SHALL aceptar puntuaciones en escala de 1 a 5 para las siguientes dimensiones: geometry, architecture, perspective, photorealism, commercial_quality, instruction_obedience, style_differentiation, localized_edit_accuracy, human_retouch_needed y construction_company_fit.
3. THE API SHALL aceptar uno de los siguientes veredictos: approved, usable_with_retouch o rejected.
4. THE API SHALL aceptar un campo de notas de texto libre en la Evaluación.
5. WHEN el usuario envía una solicitud GET /image-variants/{variant_id}/evaluation, THE API SHALL retornar la Evaluación asociada al ImageVariant.
6. WHEN el usuario envía una solicitud PATCH /evaluations/{evaluation_id}, THE API SHALL actualizar los campos proporcionados de la Evaluación existente.
7. IF el usuario envía una puntuación fuera del rango 1-5, THEN THE API SHALL retornar un error HTTP 422 indicando el rango válido.
8. IF el usuario envía un veredicto no válido, THEN THE API SHALL retornar un error HTTP 422 indicando los veredictos permitidos.
9. IF el usuario intenta crear una Evaluación para un variant_id inexistente, THEN THE API SHALL retornar un error HTTP 404.

---

### Requisito 11: Descarga de Imágenes Generadas

**Historia de Usuario:** Como usuario de la plataforma, quiero descargar las imágenes generadas, para utilizarlas en presentaciones comerciales o materiales de marketing.

#### Criterios de Aceptación

1. WHEN el usuario solicita la descarga de una imagen generada, THE API SHALL retornar una URL_Servida que permita la descarga directa del archivo desde Storage.
2. THE API SHALL incluir en la respuesta de descarga el nombre de archivo original y el tipo MIME correspondiente.
3. IF el usuario solicita la descarga de una imagen inexistente, THEN THE API SHALL retornar un error HTTP 404.

---

### Requisito 12: Procesamiento Asíncrono

**Historia de Usuario:** Como operador de la plataforma, quiero que las tareas de generación y análisis se procesen de forma asíncrona, para no bloquear la API y permitir múltiples solicitudes concurrentes.

#### Criterios de Aceptación

1. THE API SHALL encolar todas las tareas de generación de imágenes y análisis de escena en una cola Redis procesada por Workers Celery.
2. WHEN una tarea se encola, THE API SHALL retornar inmediatamente al cliente con el identificador del recurso y estado "pending".
3. WHEN el Worker completa una tarea, THE Worker SHALL actualizar el estado del recurso correspondiente (GenerationRequest o SceneInventory) en la base de datos.
4. IF un Worker falla durante el procesamiento de una tarea, THEN THE Worker SHALL registrar el error, actualizar el estado a "failed" y no dejar la tarea en un estado intermedio indefinido.

---

### Requisito 13: Trazabilidad de Generaciones

**Historia de Usuario:** Como operador de la plataforma, quiero tener trazabilidad completa de cada generación, para poder diagnosticar problemas, reproducir resultados parcialmente y estimar costos.

#### Criterios de Aceptación

1. THE API SHALL registrar para cada GenerationRequest: la imagen fuente, el prompt final enviado, el proveedor y modelo utilizados, el estado final, el error (si aplica) y la imagen de salida.
2. THE API SHALL registrar la fecha y hora de creación y finalización de cada GenerationRequest.
3. THE API SHALL permitir consultar el historial de generaciones filtrado por Proyecto, imagen fuente o proveedor.
4. THE API SHALL registrar cada generación con información suficiente para estimar costos por proveedor, por usuario y por Proyecto.

---

### Requisito 14: Seguridad Básica

**Historia de Usuario:** Como operador de la plataforma, quiero que el sistema aplique medidas de seguridad básicas, para proteger los datos y prevenir abusos.

#### Criterios de Aceptación

1. THE API SHALL validar el tipo MIME de cada archivo subido contra una lista blanca configurable (image/jpeg, image/png, image/webp).
2. THE API SHALL validar que el tamaño de cada archivo subido no exceda un límite configurable.
3. THE API SHALL nunca exponer rutas internas de Storage en las respuestas al cliente.
4. THE API SHALL servir las imágenes a través de un endpoint dedicado de la API, sin exponer la estructura del sistema de archivos local. En producción futura, este mecanismo se puede reemplazar por URLs firmadas de S3/R2.
5. THE API SHALL validar y sanitizar todos los parámetros de entrada en cada endpoint.
6. IF un archivo subido no pasa la validación de tipo o tamaño, THEN THE API SHALL rechazar la solicitud antes de almacenar el archivo.

---

### Requisito 15: Extensibilidad de Proveedores

**Historia de Usuario:** Como desarrollador de la plataforma, quiero que la arquitectura permita agregar nuevos proveedores de IA sin modificar la lógica existente, para facilitar la evolución del sistema.

#### Criterios de Aceptación

1. THE ProviderRouter SHALL definir una interfaz abstracta ImageGenerationProvider que todo proveedor debe implementar.
2. THE ProviderRouter SHALL resolver el proveedor a utilizar basándose en la configuración de la solicitud sin lógica condicional acoplada a proveedores específicos.
3. WHEN se agrega un nuevo proveedor, THE ProviderRouter SHALL requerir únicamente la implementación de la interfaz ImageGenerationProvider y su registro en la configuración, sin modificar código existente.

---

### Requisito 16: Control de Costos

**Historia de Usuario:** Como operador de la plataforma, quiero registrar el uso de cada generación para estimar costos, para controlar el gasto en proveedores de IA.

#### Criterios de Aceptación

1. THE API SHALL registrar para cada generación completada: el proveedor utilizado, el modelo específico, el Proyecto asociado y la fecha de ejecución.
2. THE API SHALL exponer un endpoint o mecanismo para consultar el número de generaciones agrupadas por proveedor, por Proyecto y por período de tiempo.
3. THE API SHALL registrar las generaciones fallidas de forma separada de las completadas para un cálculo de costos preciso.

---

### Requisito 17: Infraestructura Docker

**Historia de Usuario:** Como desarrollador de la plataforma, quiero que todo el stack se levante con Docker Compose en un solo comando, para facilitar el desarrollo local, staging y producción.

#### Criterios de Aceptación

1. THE PROJECT SHALL incluir un archivo docker-compose.yml que levante todos los servicios necesarios: FastAPI, PostgreSQL, Redis y Celery workers.
2. THE PROJECT SHALL incluir un Dockerfile multi-stage para la aplicación FastAPI que produzca una imagen optimizada para producción.
3. THE docker-compose.yml SHALL utilizar volúmenes Docker para persistir los datos de PostgreSQL y las imágenes almacenadas localmente.
4. THE PROJECT SHALL utilizar variables de entorno (archivo .env) para toda la configuración sensible y específica de entorno (credenciales de BD, API keys de proveedores IA, rutas de storage, etc.).
5. THE docker-compose.yml SHALL permitir levantar el stack completo con un solo comando `docker compose up`.
6. THE PROJECT SHALL incluir configuraciones separadas o perfiles para desarrollo local, staging y producción (por ejemplo, docker-compose.override.yml o perfiles Docker Compose).
7. THE Celery workers SHALL ejecutarse como servicios separados dentro del mismo Docker Compose, compartiendo el volumen de imágenes con la API.
8. THE PROJECT SHALL ejecutar las migraciones de Alembic automáticamente al iniciar el servicio de la API.

---

### Requisito 18: Versionado de API

**Historia de Usuario:** Como desarrollador de la plataforma, quiero que todos los endpoints estén bajo un prefijo de versión, para poder evolucionar la API sin romper clientes existentes.

#### Criterios de Aceptación

1. THE API SHALL exponer todos los endpoints bajo el prefijo `/api/v1/`.
2. THE API SHALL retornar un endpoint de health check en `GET /api/v1/health` que indique el estado del servicio.
3. THE API SHALL incluir la versión actual en la documentación OpenAPI generada automáticamente.

---

### Requisito 19: Paginación

**Historia de Usuario:** Como usuario de la plataforma, quiero que los listados de recursos estén paginados, para que la API sea eficiente con grandes volúmenes de datos.

#### Criterios de Aceptación

1. THE API SHALL implementar paginación offset/limit en todos los endpoints de listado: GET /api/v1/projects, GET /api/v1/projects/{id}/images, GET /api/v1/images/{id}/generations.
2. THE API SHALL aceptar los parámetros de query `page` (entero ≥ 1, default: 1) y `page_size` (entero entre 1 y 100, default: 20) en todos los endpoints de listado.
3. THE API SHALL retornar en cada respuesta paginada los campos: `items` (lista de recursos), `total` (total de registros), `page` (página actual) y `page_size` (tamaño de página).
4. IF el usuario envía un valor de `page_size` mayor a 100, THEN THE API SHALL retornar un error HTTP 422.

---

### Requisito 20: Observabilidad

**Historia de Usuario:** Como operador de la plataforma, quiero que el sistema genere logs estructurados con trazabilidad de requests, para poder diagnosticar problemas en producción.

#### Criterios de Aceptación

1. THE API SHALL generar logs en formato JSON estructurado usando `structlog` para todos los eventos relevantes (requests, errores, generaciones, tareas).
2. THE API SHALL generar un `correlation_id` único (UUID) para cada request HTTP entrante y propagarlo en todos los logs y tareas Celery asociadas a ese request.
3. THE API SHALL incluir el `correlation_id` en la respuesta HTTP como header `X-Correlation-ID`.
4. WHEN un Celery worker procesa una tarea, THE worker SHALL incluir el `correlation_id` del request original en todos sus logs.
5. THE API SHALL registrar en cada log de request: método HTTP, path, status code, duración en ms y correlation_id.
6. THE API SHALL registrar en cada log de error: mensaje de error, traceback, correlation_id y contexto relevante (generation_request_id, image_id, etc.).

---

### Requisito 21: Rate Limiting Configurable

**Historia de Usuario:** Como operador de la plataforma, quiero poder configurar límites de uso de generaciones IA, para controlar costos cuando el sistema tenga usuarios reales.

#### Criterios de Aceptación

1. THE SYSTEM SHALL implementar un mecanismo de rate limiting para generaciones IA configurable por variables de entorno.
2. WHEN `RATE_LIMIT_ENABLED=false` (valor por defecto), THE SYSTEM SHALL permitir generaciones sin ningún límite — modo desarrollo y testing.
3. WHEN `RATE_LIMIT_ENABLED=true`, THE SYSTEM SHALL aplicar el límite definido en `RATE_LIMIT_GENERATIONS_PER_DAY` (default: 50) por `owner_id` o por IP si no hay owner_id.
4. IF el límite diario de generaciones es alcanzado, THEN THE API SHALL retornar un error HTTP 429 con el mensaje de límite alcanzado y el tiempo de reset.
5. THE rate limit counter SHALL resetearse cada 24 horas desde la primera generación del día.
6. THE SYSTEM SHALL registrar el conteo de generaciones por owner_id/IP en Redis para eficiencia.
