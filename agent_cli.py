"""CLI entry point for the LangChain requirement-automation agent.

Usage:
    export OPENAI_API_KEY=sk-...
    python agent_cli.py "Load the demo requirements, generate API and Playwright UI tests, then run the API tests."
"""
import argparse
import os
import sys

from reqauto.agent import RequirementAutomationAgent

DEFAULT_INSTRUCTION = (
    "Load the demo requirements, generate API and Playwright UI tests for all of them, "
    "then run the API tests and summarize the results and what still needs human review."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="LangChain agent that turns requirements into pytest/Playwright automation.")
    parser.add_argument("instruction", nargs="?", default=DEFAULT_INSTRUCTION, help="Plain-language instruction for the agent.")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI chat model name.")
    parser.add_argument("--output-dir", default="generated_project", help="Folder to save generated files into.")
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("Set the OPENAI_API_KEY environment variable before running the agent.")

    agent = RequirementAutomationAgent(openai_api_key=api_key, model=args.model)
    summary = agent.run(args.instruction)

    print("\n=== Agent summary ===")
    print(summary)

    if agent.generated_files:
        written = agent.save_generated_files(args.output_dir)
        print(f"\nSaved {len(written)} files to {args.output_dir}/")


if __name__ == "__main__":
    main()
