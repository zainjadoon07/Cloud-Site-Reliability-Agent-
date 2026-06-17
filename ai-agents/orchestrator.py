from langgraph.graph import StateGraph, START, END
from metrics_agent import MetricsAgent
from logs_agent import LogsAgent
from deployment_agent import DeploymentAgent
from root_cause_agent import RootCauseAgent, SREAgentState

class SREOrchestrator:
    def __init__(self):
        # Build and compile the state graph
        self.graph = self._build_graph()
        # Check Bedrock status from RCA agent
        rca = RootCauseAgent()
        self.use_bedrock = rca.use_bedrock

    def _build_graph(self):
        # Initialize the individual agents
        metrics = MetricsAgent()
        logs = LogsAgent()
        deployment = DeploymentAgent()
        rca = RootCauseAgent()

        # Initialize StateGraph with the SRE State Schema
        workflow = StateGraph(SREAgentState)

        # Add agent nodes to the graph
        workflow.add_node("metrics_node", metrics.analyze_metrics)
        workflow.add_node("logs_node", logs.analyze_logs)
        workflow.add_node("deployment_node", deployment.analyze_deployment)
        workflow.add_node("rca_node", rca.analyze_incident)

        # Define the structural connections (edges)
        # 1. Parallel execution: Start executes metrics, logs, and deployment agents simultaneously
        workflow.add_edge(START, "metrics_node")
        workflow.add_edge(START, "logs_node")
        workflow.add_edge(START, "deployment_node")

        # 2. Map-Reduce merge: Route all three specialist nodes' output to the RCA synthesizer
        workflow.add_edge("metrics_node", "rca_node")
        workflow.add_edge("logs_node", "rca_node")
        workflow.add_edge("deployment_node", "rca_node")

        # 3. End condition: RCA node completes the flow
        workflow.add_edge("rca_node", END)

        return workflow.compile()

    def run_analysis(self, initial_state: SREAgentState) -> SREAgentState:
        """
        Executes the LangGraph SRE workflow with the provided input telemetry state.
        """
        final_state = self.graph.invoke(initial_state)
        return final_state
