import asyncio
from unittest import runner
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.adk.apps.app import App
from agent import root_agent

import warnings 
from dotenv import load_dotenv
# from google.genai import types

# warnings.filterwarnings("ignore", category=UserWarning)
load_dotenv()

# warnings.filterwarnings("ignore", category=UserWarning, module="google\.adk\..*")
 
async def run_cli():
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()
    credential_service = InMemoryCredentialService()

    session = await session_service.create_session(app_name="TravelPlanner", user_id="user_1")
    app = App(name="TravelPlanner", root_agent=root_agent)

    runner = Runner(
        app=app,
        artifact_service=artifact_service,
        session_service=session_service,
        credential_service=credential_service,
    )

    print("Welcome to Travel Planner CLI!")
    print("Type 'exit' or 'quit' to quit.")

    while True:
        user_input = input("[You]: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        content = types.Content(role="user", parts=[types.Part(text=user_input)])
      
        agen = runner.run_async(user_id=session.user_id, session_id=session.id, new_message=content)
       
        async for event in agen:
            if event.content and event.content.parts:
                text = "".join(part.text for part in event.content.parts if part.text)
                if text:
                    print(f"[{event.author}]: {text}")

    await runner.close()


if __name__ == "__main__":
    asyncio.run(run_cli())