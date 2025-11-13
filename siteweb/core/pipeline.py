import runpy
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent  # pasta siteweb/core

    etapas = [
        ("Raspagem", base_dir / "raspagem.py"),
        ("Comparação", base_dir / "comparacao.py"),
        ("Inteligência (IA)", base_dir / "inteligencio.py"),
    ]

    for nome, caminho in etapas:
        if not caminho.exists():
            print(f"[PIPELINE] ETAPA {nome} pulada. Arquivo não encontrado: {caminho}")
            continue

        print(f"[PIPELINE] Iniciando etapa: {nome} -> {caminho}")
        # executa o arquivo como se fosse rodado diretamente
        runpy.run_path(str(caminho), run_name="__main__")
        print(f"[PIPELINE] Etapa {nome} concluída.\n")


if __name__ == "__main__":
    main()
