from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field
from urllib.parse import urljoin
from requests.exceptions import HTTPError
import time
import requests
import json

class Pipeline:
    class Valves(BaseModel):
        OLLAMA_BASE_URL: str = Field(
            default="http://host.docker.internal:11434/ollama",
            description="Base URL for Open WebUI Ollama proxy API.",
        )
        OLLAMA_API_KEY: str = Field(
            default     = "",
            description = "Open WebUI API Key.",
        )
        VISION_MODEL_ID : str = Field(
            default     = "minicpm-v",
            description = "Model ID used for vision purposes.",
        )
        VISION_PROMPT : str = Field(
            default     = "Extract all visible text to markdown blocks.",
            description = "Prompt used for Vision model"
        )
        GENERAL_PURPOSE_MODEL_ID : str = Field(
            default     = "llama3.1",
            description = "Model ID used for general purposes.",
        )
        GENERAL_PURPOSE_PROMPT : str = Field(
            default     = "Answer to following without repeating question. Answer should mention proper answer and short explanation why it is correct.",
            description = "Prompt used for General purpose model"
        )
        PROMPT_TO_USE_DEFAULT_PROMPT : str = Field(
            default     = "_",
            description = "Default prompt is used if user input contains this value; otherwise, prompt provided by user is used."
        )

    def __init__(self):
        self.id = "image_to_text_pipeline"
        self.name = "Image to text Pipeline"
        self.images = []
        self.valves = self.Valves()

    async def inlet(self, body: dict, user: dict) -> dict:
        print(f"inlet:{__name__}")
        message = body['messages'][-1] # read only last message
        if(message['role'] == 'user') and isinstance(message['content'], list):
            for content in message['content']:
                if isinstance(content, dict) and 'type' in content and content['type'] == 'image_url':
                    self.images.append(self._process_image(content['image_url']))

        return body

    def _process_image(self, image_data):
        if image_data["url"].startswith("data:image"):
            _, base64_data = image_data["url"].split(",", 1)
            return base64_data 
        else:
            return image_data['url']

    def _process_response_chunks(self, response):
        buffer = ""  # Buffer to store incomplete JSON data
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                decoded_chunk = chunk.decode('utf-8').strip()
                buffer += decoded_chunk
                try:
                    json_data = json.loads(buffer)
                    
                    if "response" in json_data and json_data["response"]:
                        yield json_data["response"]
                    elif "message" in json_data and json_data["message"]:
                        yield json_data["message"]["content"]
                    elif "done" in json_data and json_data["done"]:
                        if all(key in json_data for key in ("model", "total_duration", "load_duration", "eval_duration")):
                            print(f"{bcolors.WARNING}INFO:{bcolors.ENDC}" + 
                                  f" model         : {json_data['model']}{bcolors.ENDC}\n"
                                  f"      total_duration: {bcolors.OKCYAN}{'%.2f' % (int(json_data['total_duration']) / 1000000000)}s{bcolors.ENDC}\n" +
                                  f"      load_duration : {bcolors.OKCYAN}{'%.2f' % (int(json_data['load_duration'])/1000000000)}s{bcolors.ENDC}\n" +
                                  f"      eval_duration : {bcolors.OKCYAN}{'%.2f' % (int(json_data['eval_duration'])/1000000000)}s{bcolors.ENDC}") 
                        buffer = ''
                        break
                    else:
                        print(f"{bcolors.WARNING}Unknown structure received:{bcolors.ENDC} {buffer}")
                    buffer = ''
                except json.JSONDecodeError:
                    continue
        if buffer != "":
            print(f"{bcolors.FAIL}Error:{bcolors.ENDC} Failed to decode chunk: {buffer}")
            yield f"\nError: Failed to decode chunk: {buffer}"
    

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe:{__name__}")

        if body.get("title", False):
            print("Title Generation")
            yield self.name
        else:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.valves.OLLAMA_API_KEY}'
            }
            generate_endpoint = urljoin(self.valves.OLLAMA_BASE_URL +'/', 'api/generate')
            chat_endpoint = urljoin(self.valves.OLLAMA_BASE_URL +'/', 'api/chat')
            start_time = time.time()
            try:
                if self.images:
                    yield "## *Recognized text:*\n"
                    response = requests.post(
                        generate_endpoint,
                        headers=headers,
                        json={
                            "model": self.valves.VISION_MODEL_ID,
                            "prompt": self.valves.VISION_PROMPT,
                            "images": self.images,
                            "stream": True,
                            "options": {
                                'temperature': 0.3
                            },
                            "keep_alive": 0 
                        },
                        stream=True)

                    response.raise_for_status()

                    response_from_vision = ''
                    for chunk in self._process_response_chunks(response):
                        yield chunk
                        response_from_vision += chunk

                    yield "\n---\n## *Analyzed result:*\n"

                    prompt_message = self.valves.GENERAL_PURPOSE_PROMPT if (user_message == self.valves.PROMPT_TO_USE_DEFAULT_PROMPT) else user_message
                    prompt = f'{prompt_message}\n///\n{response_from_vision}'

                    response = requests.post(
                        generate_endpoint,
                        headers=headers,
                        json={
                            "model": self.valves.GENERAL_PURPOSE_MODEL_ID,
                            "prompt": prompt,
                            "stream": True,
                            "options": {
                                'temperature': 0.3
                            },
                            "keep_alive": 0
                        },
                        stream=True)
                    
                    response.raise_for_status()

                    for chunk in self._process_response_chunks(response):
                        yield chunk

                    return ""
                else:
                    messages = []
                    for message in body['messages']:
                        if isinstance(message['content'], list):
                            for content in message['content']:
                                if isinstance(content, dict) and 'type' in content and content['type'] == 'text':
                                    messages.append({"role": message["role"], "content": content["text"]})
                        elif 'content' in message:
                            messages.append({"role": message["role"], "content": message["content"]})

                    response = requests.post(
                        chat_endpoint,
                        headers=headers,
                        json={
                            "model": self.valves.GENERAL_PURPOSE_MODEL_ID,
                            "messages": messages,
                            "stream": True,
                            "options": {
                                'temperature': 0.3
                            },
                            "keep_alive": 0
                        },
                        stream=True)
                    
                    response.raise_for_status()
                    
                    for chunk in self._process_response_chunks(response):
                        yield chunk

                    return ""
            except HTTPError as e:
                print(f"{bcolors.FAIL}ERROR: {e}.\nresponse={response.content.decode('utf-8')}{bcolors.ENDC}")
                yield f"Error: {e}"
            except Exception as e:
                print(f"{bcolors.FAIL}ERROR: {e}{bcolors.ENDC}")
                yield f"Error: {e}"
            finally:
                processing_time='%.2f' % float(time.time()-start_time)
                msg =f"Response received in: {bcolors.OKGREEN}{processing_time}s{bcolors.ENDC}"
                print(msg)
                yield f"\n\n*Response received in: **{processing_time}s***"
                self.images.clear()

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'