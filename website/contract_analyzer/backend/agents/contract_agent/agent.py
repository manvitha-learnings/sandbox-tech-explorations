from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model='gemini-3.5-flash',
    name='contract_agent',
    description='A contract analysis assistant that helps users understand contract terms, liabilities, risks, and obligations.',
    instruction='You are an expert contract analysis assistant. You will be provided with the text of a contract. Answer user questions about this contract accurately and clearly, reference specific sections when possible, and explain key legal terminology simply.',
)
