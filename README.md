# open-webui-pipelines

This repository houses custom pipelines for [Open WebUI](https://github.com/open-webui/pipelines/), designed to extend its functionality and enable powerful new use cases.

**1. Pipeline: 'Image to Text Pipeline'**

This pipeline focusing on extracting text from images and analyzing it with a general-purpose language model.

**What it does:**

1. **Image Text Recognition:** Utilizes a vision-specific model (default is `minicpm-v`) to accurately recognize all visible text within an image.
 * Supports multiple image input. 
 * Images from last user post are taken into consideration
2. **Text Analysis:**  Passes the recognized text to a general-purpose language model (default is `llama3.1`) for in-depth analysis and response generation based on a provided prompt or user query.

**Pipeline Parameters:**

*   **`OLLAMA_BASE_URL`**: The URL pointing to your Ollama server API endpoint. (Defaults to `http://host.docker.internal:11434/v1`)
*   **`VISION_MODEL_ID`**:  The ID of the vision model used for text extraction. (Defaults to `minicpm-v`)
*   **`VISION_PROMPT`**: The prompt provided to the vision model for extracting text.
*   **`GENERAL_PURPOSE_MODEL_ID`**: The ID of the general-purpose language model used for analysis. (Defaults to `llama3.1`)
*   **`GENERAL_PURPOSE_PROMPT`**:  The default prompt provided to the general-purpose model. (Defaults to a template for answering questions and providing explanations).
*   **`USER_PROMPT_TO_USE_DEFAULT_PROMPT_FOR_GENERAL_PURPOSE_MODEL`**:  User marker to use default prompt for general-purpose model.

**(For more details on parameters, see the `Valve` class within the code.)**


 **Use Cases:**

*   **Answering Questions from Images:** Extract text from images containing questions and have the pipeline provide answers based on the image content.

<div align="center">
    <video width="512" height="512" controls>
    <source src="https://github.com/aqualx/open-webui-pipelines/raw/refs/heads/main/docs/video/image_to_text_pipeline_question.mp4" type="video/mp4">
    </video>
</div>

*   **Analyzing Text-Based Images:**  Process images with textual information (e.g., signs, documents) to understand their meaning and extract key insights.
*   **Document Summarization:** Summarize the main points of a document captured as an image.

### Contributing:

Any contribution is wellcome to improve this pipeline. Please submit pull requests with your suggestions and enhancements.