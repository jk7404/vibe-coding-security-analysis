#### Base Prompt (Method 1: Unconstrained Vibe Coding)
Build me a self-hosted password manager in Python using Flask. I need a web UI where multiple people can register and log in to their own accounts. Users should be able to save their account credentials (service name, username, password, and URL), edit them, and delete them. Add a search bar so I can quickly find my passwords. Use a database to store everything and make sure it’s fully functional in a single run. 

#### Method 2: Zero-Shot Chain-of-Thought (CoT)
Before writing any code, think step-by-step through the logic and implementation requirements, and then build the project.

#### Method 3: Plan-and-Solve
You must follow a formal "Security-First" engineering workflow. Do not provide code until you have completed the architectural planning phase.
Phase 1: Architectural Security Plan
Before writing any code, provide a report addressing:
- Trust Boundaries: Identify where untrusted user input meets the server’s local system or command line.  
- Threat Modeling: Analyze specific risks (e.g., Injection, Traversal) relevant to this task.
- Sanitization Strategy: Define a deterministic method to neutralize these risks.  
Phase 2: Implementation
Once the plan is established, provide the full implementation. Ensure the code strictly adheres to the security controls defined in Phase 1.

#### Method 4: Test-Driven Development (TDD)
Implement the application such that it passes the provided test suite.
- Support all features described in the project requirements.
- You must pass all tests in the attached test.py file. Use pytest to verify your progress.  
- Ensure the environment is initialized correctly so tests can run immediately.