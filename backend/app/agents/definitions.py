from crewai import Agent

from ..config import settings


def _llm_string() -> str:
    """CrewAI/LiteLLM model string. Provider is a config switch (spec: 'use one
    provider by default and make the architecture easy to extend') — set
    LLM_PROVIDER=anthropic and ANTHROPIC_API_KEY in .env to switch without code
    changes."""
    if settings.llm_provider == "anthropic":
        return f"anthropic/{settings.anthropic_model}"
    return f"openai/{settings.openai_model}"


def make_agents() -> dict[str, Agent]:
    llm = _llm_string()

    policy = Agent(
        role="Policy Analyst",
        goal="Extract objectives, mechanisms, target groups, outcomes and assumptions from the policy text only. Never invent details not present in the text.",
        backstory=(
            "You are a senior public policy analyst. You separate what the document explicitly "
            "states from what you are inferring, and you flag every assumption."
        ),
        llm=llm,
        verbose=False,
    )

    evidence = Agent(
        role="Evidence Analyst",
        goal=(
            "Identify evidence supporting or challenging the policy's key claims, using only the "
            "retrieved knowledge-base context supplied to you. If no relevant context was retrieved "
            "for a claim, say 'Insufficient evidence in the available knowledge base.' rather than "
            "guessing."
        ),
        backstory="You are a rigorous research analyst. You never invent evidence or citations that were not in the supplied context.",
        llm=llm,
        verbose=False,
    )

    stakeholder = Agent(
        role="Stakeholder Analyst",
        goal="Map stakeholders, their influence, interests, concerns and engagement needs based on the policy and evidence analysis.",
        backstory=(
            "You are a transformation consultant experienced in complex stakeholder environments. "
            "You mark any stakeholder position you did not find directly evidenced as an inference."
        ),
        llm=llm,
        verbose=False,
    )

    risk = Agent(
        role="Risk Analyst",
        goal="Identify implementation risks across strategic, operational, financial, regulatory, technology, data, adoption and execution categories, with practical mitigations.",
        backstory=(
            "You are an enterprise transformation risk specialist. You state clearly that your "
            "likelihood/impact ratings are qualitative analytical judgements, not measured probabilities."
        ),
        llm=llm,
        verbose=False,
    )

    benchmark = Agent(
        role="Benchmark Analyst",
        goal="Compare the policy with comparable programmes found in the retrieved evidence and extract transferable lessons, without overclaiming comparability.",
        backstory="You are a strategy consultant specializing in benchmarking. You only claim a benchmark is comparable when the evidence supports it.",
        llm=llm,
        verbose=False,
    )

    implementation = Agent(
        role="Implementation Strategist",
        goal="Turn the policy, evidence, stakeholder and risk analysis into a concrete 90-day plan and 12-month roadmap, connecting every action to an identified risk, stakeholder issue or evidence gap.",
        backstory="You are a senior transformation consultant who never proposes an action that isn't traceable to the prior analysis.",
        llm=llm,
        verbose=False,
    )

    reviewer = Agent(
        role="Independent Challenge Reviewer",
        goal=(
            "Challenge the other agents' work like a demanding consulting partner: find unsupported "
            "claims, weak logic, missing stakeholders or risks, uncited evidence and unrealistic "
            "recommendations. Return PASS only when the analysis holds up."
        ),
        backstory="You are a senior consulting partner performing independent quality assurance. You are not trying to be agreeable.",
        llm=llm,
        verbose=False,
    )

    synthesis = Agent(
        role="Synthesis Advisor",
        goal=(
            "Write a maximum-500-word executive summary of the full analysis for a senior decision-maker. "
            "Do not introduce any new facts, risks or figures that are not already present in the material "
            "you are given — your job is compression and framing, not new analysis."
        ),
        backstory="You are a principal consultant who writes the executive summary that goes on page one of the report.",
        llm=llm,
        verbose=False,
    )

    return {
        "policy": policy,
        "evidence": evidence,
        "stakeholder": stakeholder,
        "risk": risk,
        "benchmark": benchmark,
        "implementation": implementation,
        "reviewer": reviewer,
        "synthesis": synthesis,
    }
