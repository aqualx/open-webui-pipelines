# Open WebUI Pipelines

This repository contains custom pipelines for [Open WebUI](https://github.com/open-webui/pipelines/), designed to extend its capabilities and unlock new, powerful use cases.

## Pipeline: **Image to Text Pipeline**

This pipeline is designed to extract text from images and generate a response based on recognized text. It uses different models and prompts for vision-to-text and text-to-text generation.

### Key Features

1. **Image Text Recognition**  
   Utilizes a vision model to accurately recognize visible text within images.  
   - Supports multiple image inputs.  
   - Analyze images from the last user post.
   
2. **Text Analysis**  
   The recognized text is passed to a general-purpose language model for detailed analysis and response generation based on the provided prompt or user query.

### Pipeline Parameters

- **`OLLAMA_BASE_URL`**: URL pointing to your Ollama server API or Open WebUI proxy endpoint.

   _Default: `http://OPEN_WEBUI_HOST/ollama`_
- **`VISION_MODEL_ID`**: ID of the vision model used for text extraction.

   _Default: `minicpm-v:latest`_
* **`VISION_PROMPT`**: The prompt provided to the vision model for extracting text.
* **`GENERAL_PURPOSE_MODEL_ID`**: The ID of the general-purpose language model used for analysis.

   _Default: `llama3.1:latest`_
* **`GENERAL_PURPOSE_PROMPT`**:  The default prompt provided to the general-purpose model.
* **`USER_PROMPT_TO_USE_DEFAULT_PROMPT`**:  User marker to use default prompt for general-purpose model.

   _Default: `_`_
  
> For more details on parameters, see the `Valve` class within the code.

### Use Cases

- **Answering Questions from Images**  
  Extract text from images containing questions and provide answers based on the image content.

  [![Demo of question task](https://img.youtube.com/vi/o_Kq1HiODcs/0.jpg)](https://www.youtube.com/watch?v=o_Kq1HiODcs)

- **Analyzing Text-Based Images**  
  Process images with textual information (e.g., signs, documents, etc) to derive meaning and extract insights.

- **Document Summarization**  
  Summarize the main points of documents captured as images, turning them into concise text.

### Contributing

Contributions to enhance this pipeline are welcome! Feel free to submit pull requests with suggestions and improvements.
