# Variables
REPO_URL = https://github.com/edunavata/gpu-bd.git
EXTERNAL_DIR = gpu-bd
EXTERNAL_DB = $(EXTERNAL_DIR)/db/pc_builder.db

.PHONY: all setup clone init-ext help clean

# Tarea por defecto
all: setup

## setup: Clona e inicializa el repositorio externo
setup: clone init-ext
	@echo "✅ Proceso completado con éxito."

## clone: Clona el repositorio si no existe
clone:
	@if [ ! -d "$(EXTERNAL_DIR)" ]; then \
		echo "🚀 Clonando repositorio externo..."; \
		git clone $(REPO_URL); \
	else \
		echo "✔ El repositorio ya está clonado."; \
	fi

## init-ext: Ejecuta el make init dentro del repositorio clonado
init-ext:
	@if [ -d "$(EXTERNAL_DIR)" ]; then \
		echo "🛠 Inicializando base de datos externa..."; \
		$(MAKE) -C $(EXTERNAL_DIR) init; \
		if [ -f "$(EXTERNAL_DB)" ]; then \
			echo "📂 Base de datos creada en: $(EXTERNAL_DB)"; \
		fi \
	else \
		echo "❌ Error: Directorio $(EXTERNAL_DIR) no encontrado. Ejecuta 'make clone' primero."; \
		exit 1; \
	fi

## clean: Elimina el repositorio clonado y archivos temporales
clean:
	@echo "🧹 Limpiando archivos..."
	rm -rf $(EXTERNAL_DIR)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "✨ Limpieza finalizada."

## help: Muestra los comandos disponibles
help:
	@echo "Comandos disponibles:"
	@sed -n 's/^##//p' $(MAKEFILE_LIST)