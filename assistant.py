import time
from openai import OpenAI

client = OpenAI(api_key='example')
# ID = "asst_qpHTGON8eP34j7wPb70lsnKt"


# First, we want to create our Assistant
assistant = client.beta.assistants.create(
    name="Pirate Pete",
    instructions="You are a happy pirate.",
    model="gpt-3.5-turbo",
)

# Then we want to create a Thread which represents a conversation between the user and the Assistant(s)
# This can be created when a user (or the AI app) starts a conversation with the Assistant
thread = client.beta.threads.create()

# Now we can add a message to the Thread
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="Ahoy, matey!"
)

# Finally, once all user messages are added to the Thread, we can Run the Thread with ANY assistant. 
# These Runs use the model and tools associated with the Assistant to generate a response. These responses are added to the Thread as 'assistant' messages.
from typing_extensions import override
from openai import AssistantEventHandler

class EventHandler(AssistantEventHandler):
    @override
    def on_text_created(self, text) -> None:
        print(f"\nassistant > ", end="", flush=True)

    @override
    def on_text_delta(self, delta, snapshot):
        print(delta.value, end="", flush=True)

    @override
    def on_tool_call_created(self, tool_call):
        print(f"\nassistant > {tool_call.type}\n", flush=True)
    
# Then, we use the `stream` SDK helper 
# with the `EventHandler` class to create the Run 
# and stream the response.
 
with client.beta.threads.runs.stream(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account.",
  event_handler=EventHandler(),
) as stream:
  stream.until_done()