from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from ollama import Client
import time


class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(
            default="http://host.docker.internal:11434/v1",
            description="Base URL for Ollama API.",
        )
        VISION_MODEL_ID : str = Field(
            default="minicpm-v",
            description="Model ID used for vision purposes.",
        )
        VISION_PROMPT : str = Field(
            default="Extract all visible text to markdown blocks.",
            description="Prompt used for Vision model"
        )
        GENERAL_PURPOSE_MODEL_ID : str = Field(
            default="llama3.1",
            description="Model ID used for general purposes.",
        )
        GENERAL_PURPOSE_PROMPT : str = Field(
            default="Answer to following without repeating question. Answer should mention proper answer and short explanation why it is correct.",
            description="Prompt used for General purpose model"
        )
        USER_PROMPT_TO_USE_DEFAULT_PROMPT_FOR_GENERAL_PURPOSE_MODEL : str = Field(
            default="_",
            description="Default prompt is used if user input contains this value; otherwise, prompt provided by user is used."
        )

    def __init__(self):
        self.id = "image_to_text_pipeline"
        self.name = "Image to text Pipeline"
        self.images = []
        self.valves = self.Valves()

    async def on_startup(self):
        # This function is called when the server is started.
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        # This function is called when the server is stopped.
        print(f"on_shutdown:{__name__}")
        pass

    async def inlet(self, body: dict, user: dict) -> dict:
        print(f"inlet:{__name__}")

        message = body['messages'][-1] # read only last message
        if(message['role'] == 'user') and isinstance(message['content'], list):
            for content in message['content']:
                if isinstance(content, dict) and 'type' in content and content['type'] == 'image_url':
                    self.images.append(self.process_image(content['image_url']))

        return body

    def process_image(self, image_data):
        if image_data["url"].startswith("data:image"):
            _, base64_data = image_data["url"].split(",", 1)
            return base64_data 
        else:
            return image_data['url']

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        if body.get("title", False):
            print("Title Generation")
            yield self.name
        else:
            start_time = time.time()
            try:
                client = Client(host=self.valves.OLLAMA_BASE_URL)
                if self.images:
                    response = client.generate(
                        model=self.valves.VISION_MODEL_ID,
                        prompt=self.valves.VISION_PROMPT,
                        stream=True,
                        images=self.images
                    )

                    yield "## *Recognized text:*\n"

                    response_from_vision = ""
                    for chunk in response:
                        response_from_vision += chunk["response"]
                        yield chunk["response"]

                    yield '\n---\n## *Analyzed result:*\n'
                    prompt_message = self.valves.GENERAL_PURPOSE_PROMPT if (user_message == self.valves.USER_PROMPT_TO_USE_DEFAULT_PROMPT_FOR_GENERAL_PURPOSE_MODEL) else user_message
                    prompt = f'{prompt_message}\n///\n{response_from_vision}'

                    print(f'Vision model took: {int(time.time()-start_time)}s')

                    response = client.generate(
                        model=self.valves.GENERAL_PURPOSE_MODEL_ID,
                        prompt=prompt,
                        stream=True
                    )

                    for chunk in response:
                        yield chunk["response"]
                    return ""
                else:
                    prompt = ""
                    for message in body['messages']:
                        if isinstance(message['content'], list):
                            for content in message['content']:
                                if isinstance(content, dict) and 'type' in content and content['type'] == 'text':
                                    prompt += content["text"] + "\n"
                        elif 'content' in message:
                            prompt += message['content']
                    prompt += user_message
                    response = client.generate(
                        model=self.valves.GENERAL_PURPOSE_MODEL_ID,
                        prompt=prompt,
                        stream=False
                    )

                    yield response["response"]

            except Exception as e:
                yield f'Error ocured: {e}'
            finally:
                msg =f'\n*Response received in: {int(time.time()-start_time)}s*'
                print(msg)
                yield f'\n {msg}'
                self.images.clear()
