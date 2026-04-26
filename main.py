"""
BQ NL Agent - Convierte lenguaje natural a queries de BigQuery y genera gráficos.
"""

import argparse
import sys
from dotenv import load_dotenv
load_dotenv()

from src.agent.orchestrator import Orchestrator


def main():
    parser = argparse.ArgumentParser(
        description="Agente que convierte lenguaje natural a consultas BigQuery y genera gráficos."
    )
    parser.add_argument(
        "question",
        nargs="?",
        help="Pregunta en lenguaje natural (ej: '¿Cuáles fueron las ventas por mes en 2024?')",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Modo interactivo (loop de preguntas)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Ruta donde guardar el gráfico (ej: ./grafico.png). Si no se indica, se muestra en pantalla.",
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Genera la SQL pero NO la ejecuta en BigQuery (útil para revisar antes de lanzar).",
    )

    args = parser.parse_args()
    orchestrator = Orchestrator()

    if args.interactive:
        print("🤖 Agente BQ activo. Escribe tu pregunta o 'salir' para terminar.\n")
        while True:
            try:
                question = input("📝 Pregunta: ").strip()
                if question.lower() in ("salir", "exit", "quit"):
                    print("👋 ¡Hasta luego!")
                    break
                if not question:
                    continue
                orchestrator.run(question, output_path=args.output, dry_run=args.dry_run)
            except KeyboardInterrupt:
                print("\n👋 ¡Hasta luego!")
                break
    elif args.question:
        orchestrator.run(args.question, output_path=args.output, dry_run=args.dry_run)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
