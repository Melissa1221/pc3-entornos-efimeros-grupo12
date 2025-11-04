#!/usr/bin/env python3
"""
Monitor de limpieza para stacks efímeros.
Proporciona análisis y alertas sobre recursos huérfanos.
"""

import json
import subprocess
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class CleanupMonitor:
    """Monitor para análisis de recursos y necesidades de limpieza."""

    def __init__(self):
        self.current_time = datetime.now()

    def scan_ephemeral_resources(self) -> Dict[str, List[Dict]]:
        """Escanea todos los recursos efímeros en el sistema."""
        return {
            "containers": self._scan_containers(),
            "volumes": self._scan_volumes(),
            "networks": self._scan_networks(),
        }

    def _scan_containers(self) -> List[Dict]:
        """Escanea contenedores efímeros."""
        try:
            cmd = [
                "docker",
                "ps",
                "-a",
                "--filter",
                "label=environment=ephemeral",
                "--format",
                "{{.Names}}\t{{.Status}}\t{{.CreatedAt}}\t{{.Labels}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            containers = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 3:
                    container_info = {
                        "name": parts[0],
                        "status": parts[1],
                        "created_at": parts[2],
                        "labels": parts[3] if len(parts) > 3 else "",
                        "pr_number": self._extract_pr_number(parts[0]),
                        "age_hours": self._calculate_age_hours(parts[2]),
                    }
                    containers.append(container_info)

            return containers
        except subprocess.CalledProcessError:
            return []

    def _scan_volumes(self) -> List[Dict]:
        """Escanea volúmenes efímeros."""
        try:
            cmd = [
                "docker",
                "volume",
                "ls",
                "--filter",
                "name=ephemeral-pr-",
                "--format",
                "{{.Name}}\t{{.Driver}}\t{{.CreatedAt}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            volumes = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    volume_info = {
                        "name": parts[0],
                        "driver": parts[1],
                        "created_at": parts[2] if len(parts) > 2 else "unknown",
                        "pr_number": self._extract_pr_number(parts[0]),
                        "age_hours": (
                            self._calculate_age_hours(parts[2])
                            if len(parts) > 2
                            else None
                        ),
                    }
                    volumes.append(volume_info)

            return volumes
        except subprocess.CalledProcessError:
            return []

    def _scan_networks(self) -> List[Dict]:
        """Escanea redes efímeras."""
        try:
            cmd = [
                "docker",
                "network",
                "ls",
                "--filter",
                "name=ephemeral-pr-",
                "--format",
                "{{.Name}}\t{{.Driver}}\t{{.CreatedAt}}",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)

            networks = []
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2 and parts[0] not in ["bridge", "host", "none"]:
                    network_info = {
                        "name": parts[0],
                        "driver": parts[1],
                        "created_at": parts[2] if len(parts) > 2 else "unknown",
                        "pr_number": self._extract_pr_number(parts[0]),
                        "age_hours": (
                            self._calculate_age_hours(parts[2])
                            if len(parts) > 2
                            else None
                        ),
                    }
                    networks.append(network_info)

            return networks
        except subprocess.CalledProcessError:
            return []

    def _extract_pr_number(self, name: str) -> Optional[int]:
        """Extrae número de PR del nombre del recurso."""
        import re

        match = re.search(r"ephemeral-pr-(\d+)", name)
        return int(match.group(1)) if match else None

    def _calculate_age_hours(self, created_at: str) -> Optional[float]:
        """Calcula edad en horas desde la fecha de creación."""
        if not created_at or created_at == "unknown":
            return None

        try:
            # Manejar diferentes formatos de fecha de Docker
            for fmt in [
                "%Y-%m-%d %H:%M:%S %z",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S%z",
            ]:
                try:
                    created_time = datetime.strptime(created_at, fmt)
                    if created_time.tzinfo is None:
                        created_time = created_time.replace(
                            tzinfo=self.current_time.tzinfo
                        )

                    age = self.current_time - created_time.replace(tzinfo=None)
                    return age.total_seconds() / 3600
                except ValueError:
                    continue

            return None
        except Exception:
            return None

    def analyze_cleanup_needs(self, max_age_hours: int = 72) -> Dict[str, any]:
        """Analiza qué recursos necesitan limpieza."""
        resources = self.scan_ephemeral_resources()

        cleanup_candidates = {
            "containers": [],
            "volumes": [],
            "networks": [],
            "pr_numbers": set(),
        }

        # Analizar contenedores
        for container in resources["containers"]:
            if container["age_hours"] and container["age_hours"] > max_age_hours:
                cleanup_candidates["containers"].append(container)
                if container["pr_number"]:
                    cleanup_candidates["pr_numbers"].add(container["pr_number"])

        # Analizar volúmenes
        for volume in resources["volumes"]:
            if volume["age_hours"] and volume["age_hours"] > max_age_hours:
                cleanup_candidates["volumes"].append(volume)
                if volume["pr_number"]:
                    cleanup_candidates["pr_numbers"].add(volume["pr_number"])

        # Analizar redes
        for network in resources["networks"]:
            if network["age_hours"] and network["age_hours"] > max_age_hours:
                cleanup_candidates["networks"].append(network)
                if network["pr_number"]:
                    cleanup_candidates["pr_numbers"].add(network["pr_number"])

        cleanup_candidates["pr_numbers"] = list(cleanup_candidates["pr_numbers"])

        return {
            "total_resources": {
                "containers": len(resources["containers"]),
                "volumes": len(resources["volumes"]),
                "networks": len(resources["networks"]),
            },
            "cleanup_candidates": cleanup_candidates,
            "analysis_time": self.current_time.isoformat(),
            "max_age_hours": max_age_hours,
        }

    def generate_cleanup_report(self, max_age_hours: int = 72) -> str:
        """Genera reporte de análisis de limpieza."""
        analysis = self.analyze_cleanup_needs(max_age_hours)

        report = f"""# Reporte de Análisis de Limpieza

**Fecha de análisis:** {analysis['analysis_time']}
**Edad máxima permitida:** {max_age_hours} horas

## Resumen de Recursos

- **Contenedores efímeros:** {analysis['total_resources']['containers']}
- **Volúmenes efímeros:** {analysis['total_resources']['volumes']}
- **Redes efímeras:** {analysis['total_resources']['networks']}

## Candidatos para Limpieza

- **Contenedores antiguos:** {len(analysis['cleanup_candidates']['containers'])}
- **Volúmenes antiguos:** {len(analysis['cleanup_candidates']['volumes'])}
- **Redes antigas:** {len(analysis['cleanup_candidates']['networks'])}
- **PRs afectados:** {len(analysis['cleanup_candidates']['pr_numbers'])}

"""

        if analysis["cleanup_candidates"]["pr_numbers"]:
            report += "### PRs con Recursos Antiguos\n\n"
            for pr_num in sorted(analysis["cleanup_candidates"]["pr_numbers"]):
                report += f"- PR #{pr_num}\n"
            report += "\n"

        if analysis["cleanup_candidates"]["containers"]:
            report += "### Contenedores para Limpiar\n\n"
            report += "| Nombre | Estado | Edad (h) | PR |\n"
            report += "|--------|---------|----------|----|\n"
            for container in analysis["cleanup_candidates"]["containers"]:
                age = (
                    f"{container['age_hours']:.1f}" if container["age_hours"] else "N/A"
                )
                pr = f"#{container['pr_number']}" if container["pr_number"] else "N/A"
                report += (
                    f"| {container['name']} | {container['status']} | {age} | {pr} |\n"
                )
            report += "\n"

        if not analysis["cleanup_candidates"]["pr_numbers"]:
            report += "✅ **No se encontraron recursos que requieran limpieza.**\n"

        return report

    def check_pr_status(self, pr_number: int) -> str:
        """Verifica estado de PR usando GitHub CLI."""
        try:
            cmd = [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--json",
                "state",
                "--jq",
                ".state",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else "UNKNOWN"
        except subprocess.CalledProcessError:
            return "UNKNOWN"

    def get_resource_summary(self) -> Dict[str, int]:
        """Obtiene resumen rápido de recursos."""
        resources = self.scan_ephemeral_resources()

        return {
            "total_containers": len(resources["containers"]),
            "running_containers": len(
                [c for c in resources["containers"] if "Up" in c["status"]]
            ),
            "total_volumes": len(resources["volumes"]),
            "total_networks": len(resources["networks"]),
            "unique_prs": len(
                set(
                    r["pr_number"]
                    for r in resources["containers"]
                    + resources["volumes"]
                    + resources["networks"]
                    if r["pr_number"] is not None
                )
            ),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Monitor de limpieza de stacks efímeros"
    )
    parser.add_argument(
        "--max-age",
        type=int,
        default=72,
        help="Edad máxima en horas para considerar limpieza",
    )
    parser.add_argument(
        "--report", action="store_true", help="Generar reporte de limpieza"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Mostrar resumen de recursos"
    )
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")

    args = parser.parse_args()

    monitor = CleanupMonitor()

    if args.summary:
        summary = monitor.get_resource_summary()
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(
                f"Contenedores: {summary['total_containers']} (ejecutándose: {summary['running_containers']})"
            )
            print(f"Volúmenes: {summary['total_volumes']}")
            print(f"Redes: {summary['total_networks']}")
            print(f"PRs únicos: {summary['unique_prs']}")

    elif args.report:
        report = monitor.generate_cleanup_report(args.max_age)
        print(report)

    else:
        analysis = monitor.analyze_cleanup_needs(args.max_age)
        if args.json:
            print(json.dumps(analysis, indent=2, default=str))
        else:
            candidates = analysis["cleanup_candidates"]
            print(f"Recursos que requieren limpieza (>{args.max_age}h):")
            print(f"  Contenedores: {len(candidates['containers'])}")
            print(f"  Volúmenes: {len(candidates['volumes'])}")
            print(f"  Redes: {len(candidates['networks'])}")
            print(f"  PRs afectados: {len(candidates['pr_numbers'])}")

            if candidates["pr_numbers"]:
                print(
                    f"  PRs: {', '.join(f'#{pr}' for pr in sorted(candidates['pr_numbers']))}"
                )


if __name__ == "__main__":
    main()
