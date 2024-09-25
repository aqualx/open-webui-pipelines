# Open WebUI Pipelines

This repository contains custom pipelines for [Open WebUI](https://github.com/open-webui/pipelines/), designed to extend its capabilities and unlock new, powerful use cases.

## Pipeline: **Image to Text Pipeline**

This pipeline is designed to extract text from images and generate a response based on recognized text. It uses different models and prompts for vision-to-text and text-to-text generation.

### Key Features

1. **Image Text Recognition**  
   Utilizes a vision-specific model (default: `minicpm-v`) to accurately recognize visible text within images.  
   - Supports multiple image inputs.  
   - Analyzes images from the last user post by default.
   
2. **Text Analysis**  
   The recognized text is passed to a general-purpose language model (default: `llama3.1`) for detailed analysis and response generation based on the provided prompt or user query.

### Pipeline Parameters

- **`OLLAMA_BASE_URL`**: URL pointing to your Ollama server API endpoint.  
  _Default: `http://host.docker.internal:11434/v1`_
  
- **`VISION_MODEL_ID`**: ID of the vision model used for text extraction.  
  _Default: `minicpm-v`_

- **`VISION_PROMPT`**: The prompt provided to the vision model for text extraction.

- **`GENERAL_PURPOSE_MODEL_ID`**: ID of the general-purpose language model used for analysis.  
  _Default: `llama3.1`_

- **`GENERAL_PURPOSE_PROMPT`**: The default prompt used for the general-purpose model.  
  _Default: Template for answering questions and providing explanations._

- **`USER_PROMPT_TO_USE_DEFAULT_PROMPT_FOR_GENERAL_PURPOSE_MODEL`**: Marker to instruct the general-purpose model to use the default prompt.

> For more details on parameters, see the `Valve` class within the code.

### Use Cases

- **Answering Questions from Images**  
  Extract text from images containing questions and provide answers based on the image content.

  [![Demo of question task](https://img.youtube.com/vi/o_Kq1HiODcs/0.jpg)](https://www.youtube.com/watch?v=o_Kq1HiODcs)

- **Analyzing Text-Based Images**  
  Process images with textual information (e.g., signs, documents) to derive meaning and extract insights.

- **Document Summarization**  
  Summarize the main points of documents captured as images, turning them into concise text.

### Contributing

Contributions to enhance this pipeline are welcome! Feel free to submit pull requests with suggestions and improvements.
