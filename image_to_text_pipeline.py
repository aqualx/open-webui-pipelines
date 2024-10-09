import os
import threading
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from urllib.parse import urljoin
from requests.exceptions import HTTPError
import time
import requests
import json
# import http.client as http_client
# import logging

class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str
        OLLAMA_API_KEY: str
        VISION_MODEL_ID : str
        VISION_PROMPT : str
        GENERAL_PURPOSE_MODEL_ID : str
        GENERAL_PURPOSE_PROMPT : str
        PROMPT_TO_USE_DEFAULT_PROMPT : str

    class BColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    def __init__(self):
        self.id = 'image_to_text_pipeline'
        self.name = 'Image to text Pipeline'
        self.error_messages = []
        self.images = []
        self.valves = self.Valves(
            **{
                # Base URL for Open WebUI Ollama proxy API.
                "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434/ollama"),
                # Open WebUI API Key.
                "OLLAMA_API_KEY": os.getenv("OLLAMA_API_KEY", ""),
                # Model ID used for vision purposes.
                "VISION_MODEL_ID": os.getenv("VISION_MODEL_ID", "minicpm-v"),
                # Prompt used for General purpose model.
                "VISION_PROMPT": os.getenv("VISION_PROMPT", "Extract all visible text to markdown blocks."),
                # Model ID used for general purposes.
                "GENERAL_PURPOSE_MODEL_ID": os.getenv("GENERAL_PURPOSE_MODEL_ID", "llama3.1"),
                # Prompt used for General purpose model
                "GENERAL_PURPOSE_PROMPT": os.getenv("GENERAL_PURPOSE_PROMPT", "Answer to following without repeating question. Answer should mention proper answer and short explanation why it is correct."),
                # Default prompt is used if user input contains this value; otherwise, prompt provided by user is used.
                "PROMPT_TO_USE_DEFAULT_PROMPT": os.getenv("PROMPT_TO_USE_DEFAULT_PROMPT", "_"),
            }
        )

        # enable logging
        # http_client.HTTPConnection.debuglevel = 0
        # logging.basicConfig()
        # logging.getLogger().setLevel(logging.ERROR)
        # requests_log = logging.getLogger("requests.packages.urllib3")
        # requests_log.setLevel(logging.ERROR)
        # requests_log.propagate = True

    async def on_valves_updated(self):
        self.init()
        self.validate_settings_in_background()

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        self.init()
        self.validate_settings_in_background()

    async def inlet(self, body: dict, user: dict) -> dict:
        print(f'inlet:{__name__}')
        message = body['messages'][-1] # read only last message
        if(message['role'] == 'user') and isinstance(message['content'], list):
            for content in message['content']:
                if isinstance(content, dict) and 'type' in content and content['type'] == 'image_url':
                    self.images.append(self.process_image(content['image_url']))

        return body

    def init(self):
        self.headers = {
            'Authorization': f'Bearer {self.valves.OLLAMA_API_KEY}',
            'Content-Type': 'application/json'
        }
        self.generate_endpoint = urljoin(self.valves.OLLAMA_BASE_URL +'/', 'api/generate')
        self.chat_endpoint = urljoin(self.valves.OLLAMA_BASE_URL +'/', 'api/chat')
        self.models_endpoint = urljoin(self.valves.OLLAMA_BASE_URL +'/', 'v1/models')

    def validate_settings_in_background(self):
        thread = threading.Thread(target=self.validate_settings)
        thread.start()

    def validate_settings(self):
        self.error_messages = []
        try:
            r = requests.get(self.models_endpoint, headers=self.headers)
            models = json.loads(r.content.decode("utf-8")).get('data', [])
            model_names = [item['id'] for item in models]

            if self.valves.GENERAL_PURPOSE_MODEL_ID not in model_names:
                self.error_messages.append(f"Model not present: {self.valves.GENERAL_PURPOSE_MODEL_ID}")

            if self.valves.VISION_MODEL_ID not in model_names:
                self.error_messages.append(f"Model not present: {self.valves.VISION_MODEL_ID}")

            return len(self.error_messages) == 0
        except Exception as e:
            msg = f"Error during model validation: {e}"
            print(self.BColors.FAIL + msg + self.BColors.ENDC)
            self.error_messages.append(msg)
            return False

    def process_image(self, image_data):
        if image_data['url'].startswith('data:image'):
            _, base64_data = image_data['url'].split(',', 1)
            return base64_data
        else:
            return image_data['url']

    def process_response_chunks(self, response):
        buffer = ''  # Buffer to store incomplete JSON data
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                decoded_chunk = chunk.decode('utf-8').strip()
                buffer += decoded_chunk
                try:
                    json_data = json.loads(buffer)

                    if 'response' in json_data and json_data['response']:
                        yield json_data['response']
                    elif 'message' in json_data and json_data['message']:
                        yield json_data['message']['content']
                    elif 'done' in json_data and json_data['done']:
                        if all(key in json_data for key in ('model', 'total_duration', 'load_duration', 'eval_duration')):
                            print(f"{self.BColors.WARNING}INFO:{self.BColors.ENDC}" +
                                  f" model         : {json_data['model']}{self.BColors.ENDC}\n"
                                  f"      total_duration: {self.BColors.OKCYAN}{'%.2f' % (int(json_data['total_duration']) / 1000000000)}s{self.BColors.ENDC}\n" +
                                  f"      load_duration : {self.BColors.OKCYAN}{'%.2f' % (int(json_data['load_duration'])/1000000000)}s{self.BColors.ENDC}\n" +
                                  f"      eval_duration : {self.BColors.OKCYAN}{'%.2f' % (int(json_data['eval_duration'])/1000000000)}s{self.BColors.ENDC}")
                        buffer = ''
                        break
                    else:
                        print(f'{self.BColors.WARNING}Unknown structure received:{self.BColors.ENDC} {buffer}')
                    buffer = ''
                except json.JSONDecodeError:
                    continue
        if buffer != '':
            print(f'{self.BColors.FAIL}Error:{self.BColors.ENDC} Failed to decode chunk: {buffer}')
            yield f'\nError: Failed to decode chunk: {buffer}'

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f'pipe:{__name__}')

        if body.get('title', False):
            print('Title Generation')
            yield self.name
        else:
            start_time = time.time()
            try:
                if not len(self.error_messages) == 0 and not self.validate_settings():
                    yield f"Settings validation error: {self.error_messages}"
                    return ''

                if self.images:
                    yield '## *Recognized text:*\n'
                    response = requests.post(
                        self.generate_endpoint,
                        headers=self.headers,
                        json={
                            'model': self.valves.VISION_MODEL_ID,
                            'prompt': self.valves.VISION_PROMPT,
                            'images': self.images,
                            'stream': True,
                            'options': {
                                'temperature': 0.3
                            },
                            'keep_alive': 0
                        },
                        stream=True)

                    response.raise_for_status()

                    response_from_vision = ''
                    for chunk in self.process_response_chunks(response):
                        yield chunk
                        response_from_vision += chunk

                    yield '\n---\n## *Analyzed result:*\n'

                    prompt_message = self.valves.GENERAL_PURPOSE_PROMPT if (user_message == self.valves.PROMPT_TO_USE_DEFAULT_PROMPT) else user_message
                    prompt = f'{prompt_message}\n///\n{response_from_vision}'

                    response = requests.post(
                        self.generate_endpoint,
                        headers=self.headers,
                        json={
                            'model': self.valves.GENERAL_PURPOSE_MODEL_ID,
                            'prompt': prompt,
                            'stream': True,
                            'options': {
                                'temperature': 0.3
                            },
                            'keep_alive': 0
                        },
                        stream=True)

                    response.raise_for_status()

                    for chunk in self.process_response_chunks(response):
                        yield chunk

                    return ''
                else:
                    messages = []
                    for message in body['messages']:
                        if isinstance(message['content'], list):
                            for content in message['content']:
                                if isinstance(content, dict) and 'type' in content and content['type'] == 'text':
                                    messages.append({'role': message['role'], 'content': content['text']})
                        elif 'content' in message:
                            messages.append({'role': message['role'], 'content': message['content']})

                    r = requests.post(
                        self.chat_endpoint,
                        headers=self.headers,
                        json={
                            'model': self.valves.GENERAL_PURPOSE_MODEL_ID,
                            'messages': messages,
                            'stream': True,
                            'options': {
                                'temperature': 0.3
                            },
                            'keep_alive': 360
                        },
                        stream=True)

                    r.raise_for_status()

                    if body["stream"]:
                        for chunk in self.process_response_chunks(r):
                            yield chunk
                    else:
                        result = ''
                        for chunk in self.process_response_chunks(r):
                            result += chunk
                        return result
                    return ''
            except HTTPError as e:
                print(f"{self.BColors.FAIL}ERROR: {e}.\nresponse={r.content.decode('utf-8')}{self.BColors.ENDC}")
                yield f'Error: {e}'
            except Exception as e:
                print(f'{self.BColors.FAIL}ERROR: {e}{self.BColors.ENDC}')
                yield f'Error: {e}'
            finally:
                processing_time='%.2f' % float(time.time()-start_time)
                msg =f'Response received in: {self.BColors.OKGREEN}{processing_time}s{self.BColors.ENDC}'
                print(msg)
                yield f'\n\n*Response received in: **{processing_time}s***'
                self.images.clear()
