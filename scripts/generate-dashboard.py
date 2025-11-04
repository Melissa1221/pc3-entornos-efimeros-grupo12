#!/usr/bin/env python3
"""
Generador de dashboard de trends para métricas de IaC.
Crea visualizaciones y reportes de tendencias de provisionado.
"""

import json
import os
import sys
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import statistics


class TrendsAnalyzer:
    """Analizador de tendencias para métricas de IaC."""

    def __init__(self, metrics_file: str):
        self.metrics_file = metrics_file
        self.data = self._load_metrics()

    def _load_metrics(self) -> Dict[str, List]:
        """Carga datos de métricas desde archivo JSON."""
        if not os.path.exists(self.metrics_file):
            return {"operations": [], "drift_checks": []}

        try:
            with open(self.metrics_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"operations": [], "drift_checks": []}

    def get_operation_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analiza tendencias de operaciones en los últimos N días."""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_ops = [
            op
            for op in self.data.get("operations", [])
            if datetime.fromisoformat(op["timestamp"].replace("Z", "+00:00"))
            > cutoff_date
        ]

        deploy_times = [
            op["duration_seconds"]
            for op in recent_ops
            if op["operation"] == "deploy" and op["status"] == "success"
        ]
        destroy_times = [
            op["duration_seconds"]
            for op in recent_ops
            if op["operation"] == "destroy" and op["status"] == "success"
        ]

        success_rate = self._calculate_success_rate(recent_ops)

        return {
            "period_days": days,
            "total_operations": len(recent_ops),
            "deploy_stats": self._calculate_stats(deploy_times),
            "destroy_stats": self._calculate_stats(destroy_times),
            "success_rate": success_rate,
            "daily_operations": self._group_operations_by_day(recent_ops, days),
        }

    def get_drift_trends(self, days: int = 30) -> Dict[str, Any]:
        """Analiza tendencias de drift en los últimos N días."""
        cutoff_date = datetime.now() - timedelta(days=days)

        recent_checks = [
            check
            for check in self.data.get("drift_checks", [])
            if datetime.fromisoformat(check["timestamp"].replace("Z", "+00:00"))
            > cutoff_date
        ]

        drift_percentages = [
            check["drift_percent"]
            for check in recent_checks
            if check["status"] == "drift_detected"
        ]
        zero_drift_count = len(
            [check for check in recent_checks if check["drift_percent"] == 0]
        )

        compliance_rate = (
            (zero_drift_count / len(recent_checks) * 100) if recent_checks else 0
        )

        return {
            "period_days": days,
            "total_checks": len(recent_checks),
            "zero_drift_checks": zero_drift_count,
            "compliance_rate": compliance_rate,
            "drift_stats": (
                self._calculate_stats(drift_percentages) if drift_percentages else None
            ),
            "daily_drift": self._group_drift_by_day(recent_checks, days),
        }

    def _calculate_stats(self, values: List[float]) -> Optional[Dict[str, float]]:
        """Calcula estadísticas básicas para una lista de valores."""
        if not values:
            return None

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
        }

    def _calculate_success_rate(self, operations: List[Dict]) -> float:
        """Calcula tasa de éxito de operaciones."""
        if not operations:
            return 0.0

        successful = len([op for op in operations if op["status"] == "success"])
        return (successful / len(operations)) * 100

    def _group_operations_by_day(self, operations: List[Dict], days: int) -> List[Dict]:
        """Agrupa operaciones por día."""
        daily_data = {}

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data[date] = {
                "date": date,
                "deploys": 0,
                "destroys": 0,
                "failures": 0,
            }

        for op in operations:
            date = op["timestamp"][:10]
            if date in daily_data:
                if op["operation"] == "deploy":
                    daily_data[date]["deploys"] += 1
                elif op["operation"] == "destroy":
                    daily_data[date]["destroys"] += 1

                if op["status"] == "failed":
                    daily_data[date]["failures"] += 1

        return list(daily_data.values())

    def _group_drift_by_day(self, checks: List[Dict], days: int) -> List[Dict]:
        """Agrupa verificaciones de drift por día."""
        daily_data = {}

        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            daily_data[date] = {"date": date, "total_checks": 0, "zero_drift": 0}

        for check in checks:
            date = check["timestamp"][:10]
            if date in daily_data:
                daily_data[date]["total_checks"] += 1
                if check["drift_percent"] == 0:
                    daily_data[date]["zero_drift"] += 1

        for day_data in daily_data.values():
            if day_data["total_checks"] > 0:
                day_data["compliance_rate"] = (
                    day_data["zero_drift"] / day_data["total_checks"]
                ) * 100
            else:
                day_data["compliance_rate"] = 0

        return list(daily_data.values())


class DashboardGenerator:
    """Generador de dashboard HTML."""

    def __init__(self, analyzer: TrendsAnalyzer):
        self.analyzer = analyzer

    def generate_html_dashboard(self, output_file: str, days: int = 30) -> str:
        """Genera dashboard HTML completo."""
        operation_trends = self.analyzer.get_operation_trends(days)
        drift_trends = self.analyzer.get_drift_trends(days)

        html_content = self._generate_html_template(
            operation_trends, drift_trends, days
        )

        with open(output_file, "w") as f:
            f.write(html_content)

        return output_file

    def _generate_html_template(
        self, operation_trends: Dict, drift_trends: Dict, days: int
    ) -> str:
        """Genera template HTML para el dashboard."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Dashboard IaC Metrics</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .metric {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
        .success {{ color: green; }}
        .warning {{ color: orange; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>Dashboard IaC Metrics</h1>
    <p>Período: últimos {days} días | Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>Métricas Principales</h2>
    <div class="metric">
        <strong>Operaciones Totales:</strong> {operation_trends.get('total_operations', 0)}
    </div>
    <div class="metric">
        <strong>Tasa de Éxito:</strong> <span class="success">{operation_trends.get('success_rate', 0):.1f}%</span>
    </div>
    <div class="metric">
        <strong>Compliance Drift:</strong> <span class="{'success' if drift_trends.get('compliance_rate', 0) >= 90 else 'warning'}">{drift_trends.get('compliance_rate', 0):.1f}%</span>
    </div>
    
    <h2>Estadísticas de Deploy</h2>
    {self._generate_stats_table(operation_trends.get('deploy_stats'))}
    
    <h2>Estadísticas de Destroy</h2>
    {self._generate_stats_table(operation_trends.get('destroy_stats'))}
    
    <h2>Operaciones por Día (últimos 14 días)</h2>
    <table>
        <tr>
            <th>Fecha</th>
            <th>Deploys</th>
            <th>Destroys</th>
            <th>Fallos</th>
        </tr>
        {self._generate_daily_ops_rows(operation_trends.get('daily_operations', []))}
    </table>
    
    <h2>Drift por Día (últimos 14 días)</h2>
    <table>
        <tr>
            <th>Fecha</th>
            <th>Verificaciones</th>
            <th>0% Drift</th>
            <th>Compliance %</th>
        </tr>
        {self._generate_daily_drift_rows(drift_trends.get('daily_drift', []))}
    </table>
</body>
</html>"""

    def _generate_stats_table(self, stats: Optional[Dict]) -> str:
        """Genera tabla de estadísticas."""
        if not stats:
            return "<p>No hay datos disponibles</p>"

        return f"""<table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Cantidad</td><td>{stats.get('count', 0)}</td></tr>
            <tr><td>Promedio</td><td>{stats.get('mean', 0):.1f}s</td></tr>
            <tr><td>Mediana</td><td>{stats.get('median', 0):.1f}s</td></tr>
            <tr><td>Mínimo</td><td>{stats.get('min', 0):.1f}s</td></tr>
            <tr><td>Máximo</td><td>{stats.get('max', 0):.1f}s</td></tr>
        </table>"""

    def _generate_daily_ops_rows(self, daily_ops: List[Dict]) -> str:
        """Genera filas para tabla de operaciones diarias."""
        rows = []
        for day in daily_ops[-14:]:
            rows.append(
                f"""<tr>
                <td>{day['date']}</td>
                <td>{day['deploys']}</td>
                <td>{day['destroys']}</td>
                <td><span class="{'error' if day['failures'] > 0 else 'success'}">{day['failures']}</span></td>
            </tr>"""
            )
        return "\n".join(rows)

    def _generate_daily_drift_rows(self, daily_drift: List[Dict]) -> str:
        """Genera filas para tabla de drift diario."""
        rows = []
        for day in daily_drift[-14:]:
            compliance = day.get("compliance_rate", 0)
            rows.append(
                f"""<tr>
                <td>{day['date']}</td>
                <td>{day['total_checks']}</td>
                <td>{day['zero_drift']}</td>
                <td><span class="{'success' if compliance >= 90 else 'warning'}">{compliance:.1f}%</span></td>
            </tr>"""
            )
        return "\n".join(rows)


def main():
    parser = argparse.ArgumentParser(description="Generador de dashboard de trends")
    parser.add_argument(
        "--metrics-file",
        default="metrics/operations.json",
        help="Archivo de métricas JSON",
    )
    parser.add_argument(
        "--output", default="dashboard/trends.html", help="Archivo de salida HTML"
    )
    parser.add_argument("--days", type=int, default=30, help="Días a analizar")

    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    analyzer = TrendsAnalyzer(args.metrics_file)
    generator = DashboardGenerator(analyzer)

    output_file = generator.generate_html_dashboard(args.output, args.days)

    print(f"Dashboard generado: {output_file}")


if __name__ == "__main__":
    main()
