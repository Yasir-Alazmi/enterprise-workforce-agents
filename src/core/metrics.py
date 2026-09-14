import threading
from collections import defaultdict
from typing import Dict, List


class AgentMetricsCollector:
    """Thread-safe Prometheus operational telemetry collector for Multi-Agent execution."""

    def __init__(self):
        self._lock = threading.Lock()
        self.http_requests_total: Dict[str, int] = defaultdict(int)
        self.workflow_executions_total: Dict[str, int] = defaultdict(int)
        self.agent_invocations_total: Dict[str, int] = defaultdict(int)
        self.tool_calls_total: Dict[str, int] = defaultdict(int)
        self.hitl_approvals_total: Dict[str, int] = defaultdict(int)
        self.agent_latencies: Dict[str, List[float]] = defaultdict(list)
        self.workflow_latencies: List[float] = []

    def record_request(self, method: str, path: str, status_code: int) -> None:
        key = f'{method}:{path}:{status_code}'
        with self._lock:
            self.http_requests_total[key] += 1

    def record_workflow_execution(self, status: str, duration_sec: float) -> None:
        with self._lock:
            self.workflow_executions_total[status] += 1
            self.workflow_latencies.append(duration_sec)
            if len(self.workflow_latencies) > 2000:
                self.workflow_latencies = self.workflow_latencies[-1000:]

    def record_agent_invocation(self, agent_name: str, duration_sec: float) -> None:
        with self._lock:
            self.agent_invocations_total[agent_name] += 1
            self.agent_latencies[agent_name].append(duration_sec)
            if len(self.agent_latencies[agent_name]) > 1000:
                self.agent_latencies[agent_name] = self.agent_latencies[agent_name][-500:]

    def record_tool_call(self, tool_name: str, success: bool) -> None:
        status = "success" if success else "failure"
        key = f'{tool_name}:{status}'
        with self._lock:
            self.tool_calls_total[key] += 1

    def record_hitl_decision(self, decision: str) -> None:
        with self._lock:
            self.hitl_approvals_total[decision] += 1

    def export_text(self) -> str:
        lines: List[str] = [
            "# HELP workforce_http_requests_total Total HTTP requests handled by the agent platform",
            "# TYPE workforce_http_requests_total counter",
        ]
        with self._lock:
            for k, count in sorted(self.http_requests_total.items()):
                m, p, s = k.split(":")
                lines.append(f'workforce_http_requests_total{{method="{m}",path="{p}",status="{s}"}} {count}')

            lines.extend([
                "# HELP workforce_workflow_executions_total Total multi-agent workflow executions by final status",
                "# TYPE workforce_workflow_executions_total counter",
            ])
            for status, count in sorted(self.workflow_executions_total.items()):
                lines.append(f'workforce_workflow_executions_total{{status="{status}"}} {count}')

            lines.extend([
                "# HELP workforce_agent_invocations_total Total invocations per specialized agent",
                "# TYPE workforce_agent_invocations_total counter",
            ])
            for agent, count in sorted(self.agent_invocations_total.items()):
                lines.append(f'workforce_agent_invocations_total{{agent="{agent}"}} {count}')

            lines.extend([
                "# HELP workforce_tool_calls_total Total tool executions partitioned by tool and outcome",
                "# TYPE workforce_tool_calls_total counter",
            ])
            for key, count in sorted(self.tool_calls_total.items()):
                t_name, t_stat = key.split(":")
                lines.append(f'workforce_tool_calls_total{{tool="{t_name}",status="{t_stat}"}} {count}')

            lines.extend([
                "# HELP workforce_hitl_approvals_total Human-in-the-Loop decisions recorded",
                "# TYPE workforce_hitl_approvals_total counter",
            ])
            for decision, count in sorted(self.hitl_approvals_total.items()):
                lines.append(f'workforce_hitl_approvals_total{{decision="{decision}"}} {count}')

        lines.append("")
        return "\n".join(lines)


metrics_collector = AgentMetricsCollector()
