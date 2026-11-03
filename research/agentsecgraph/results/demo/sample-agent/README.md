# AgentSecBench authored demo

This tiny project exists only to demonstrate static analysis. AgentSecBench
reads `agent.py` as text and does not import or execute it.

The deliberately review-worthy function passes parameters to a shell-capable
process invocation and a filesystem write. These are analysis candidates, not
claims that this authored example is a real vulnerability.
