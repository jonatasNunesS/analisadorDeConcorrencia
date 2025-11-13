import runpy
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Executa a pipeline completa: raspagem -> comparação -> IA."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Modo teste (apenas logs, mas executa as etapas normalmente).",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)

        # BASE_DIR do Django (raiz do projeto)
        base_dir = Path(settings.BASE_DIR)

        pipeline_path = base_dir / "siteweb" / "core" / "pipeline.py"

        if not pipeline_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    f"Arquivo da pipeline não encontrado: {pipeline_path}"
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f"Executando pipeline completa a partir de: {pipeline_path}"
            )
        )

        # Aqui o --dry-run é mais “informativo” – você poderia usar para pular gravação em disco,
        # mas por enquanto ele só serve para log.
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run ATIVO (execução normal, apenas marcado como teste)."))

        # Executa o pipeline.py
        runpy.run_path(str(pipeline_path), run_name="__main__")

        self.stdout.write(self.style.SUCCESS("Pipeline concluída com sucesso."))
