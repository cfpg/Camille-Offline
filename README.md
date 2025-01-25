# Camille Offline AI Assistant

Welcome to Camille Offline, a Python-based AI assistant that enables voice conversations using local Large Language Models (LLMs). This project leverages Whisper for speech-to-text, LM Studio for local LLM inference, and Porcupine for wake-word detection, all while prioritizing privacy and accessibility. Camille Offline is designed to provide a seamless, interactive voice-based AI experience entirely on your local machine.

## Key Features

- **Privacy-First**: All processing happens locally—no data is sent to external servers.
- **Voice Interaction**: Speak naturally to interact with the AI using wake-word detection and speech-to-text.
- **Customizable**: Easily configure the AI's name, voice, and behavior to suit your preferences.
- **Offline Capable**: Runs entirely on your machine, intended to prevent them from listening to you.
- **Extensible Functionality**: Supports custom tools and functions through LangChain integration.
- **Conversation Context**: Maintains context across interactions using LangChain's memory system.

## Getting Started

This guide will walk you through setting up and running Camille Offline on your local machine. Follow the steps below to prepare your environment, install dependencies, and start using the assistant.

---

### Prerequisites

Before you begin, ensure you have the following installed:

1. **Anaconda**: A Python distribution that simplifies package management. Download and install it from the [official Anaconda website](https://www.anaconda.com/).
2. **LM Studio**: A desktop application for running local LLMs. Download it from the [LM Studio website](https://lmstudio.ai/).

---

### Setting Up Your Python Environment

1. **Create a Conda Environment**:
   Open a terminal and create a new Conda environment with Python 3.11:
   ```
   conda create -n camille-env python=3.11
   ```
   Replace `camille-env` with a name of your choice.

2. **Activate the Environment**:
   Activate the newly created environment:
   ```
   conda activate camille-env
   ```

3. **Clone the Repository**:
   Clone the Camille Offline repository to your local machine:
   ```
   git clone https://github.com/cfpg/Camille-Offline
   cd Camille-Offline
   ```

4. **Install Required Packages**:
   Install the necessary Python packages using the provided `requirements.txt` file:
   ```
   pip install -r requirements.txt
   ```

---

### Configuring LM Studio

1. **Download a Model**:
   Open LM Studio and download a compatible LLM model (e.g., `llama-3.2-3b-instruct`).

2. **Start the Local Inference Server**:
   In LM Studio, navigate to the "Local Server" tab and start the server. Ensure it is running on `http://localhost:1234`.

---

### Running Camille Offline

1. **Set Up Environment Variables**:
   Create a `.env` file in the project directory and add the following variables:
   ```
   PICOVOICE_ACCESS_KEY=your_access_key_here
   ```
   Replace `your_access_key_here` with your actual Picovoice access key.

2. **Run the Script**:
   Execute the main script to start Camille Offline:
   ```
   python main.py
   ```

3. **Interact with Camille**:
   - Use the wake phrase **"Hey Camille"** to activate the assistant.
   - Speak your command after the wake phrase is detected.
   - Camille will process your request and respond via text-to-speech, maintaining context across interactions.

---

## Troubleshooting

- **LM Studio Compatibility**: If the provided setup doesn't work for your system, refer to the [LM Studio documentation](https://lmstudio.ai/docs) for alternative configurations.
- **Dependency Issues**: Regularly update the `requirements.txt` file to ensure compatibility with the latest versions of dependencies.
- **Need Help?**: This project was initially developed with the help of ChatGPT. If you encounter issues, consider consulting GPT-based tools for troubleshooting and solutions.

---

## Customization

- **Change the Wake Phrase**: Replace the `hey-camille.ppn` file in the project directory with a custom wake-word model from [Picovoice Console](https://console.picovoice.ai/).
- **Modify the AI's Behavior**: Edit the system prompt in the `process_input` function to customize the AI's responses.
- **Add Custom Tools**: Create new Python files in the `tools` directory to add custom functionality.
- **Adjust Audio Settings**: Modify the `RATE`, `CHUNK`, and `FORMAT` variables to optimize audio recording for your environment.

## Adding New Tools

Camille Offline supports custom tools through LangChain's tool system. Follow these steps to add new functionality:

1. **Create a New Tool File**:
   Create a new Python file in the `tools` directory (e.g., `tools/my_tool.py`).

2. **Define Your Tool**:
   Use the following template to create your tool:

   ```python
   from tools import register_tool
   from langchain.tools import tool

   @tool
   @register_tool
   def my_tool(parameter: str) -> str:
       """
       Brief description of what your tool does.
       
       Args:
           parameter: Explanation of the parameter
           
       Returns:
           Explanation of the return value
       """
       # Your implementation here
       return "Tool result"
   ```
3. **Automatic Registration**:
    The tool will be automatically discovered and registered when the application starts.

---

## Contributing

We welcome contributions to improve Camille Offline! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **LM Studio**: For providing an easy-to-use interface for local LLM inference.
- **OpenAI Whisper**: For enabling accurate speech-to-text capabilities.
- **Picovoice**: For wake-word detection technology.
- **LangChain**: For providing tools and memory management capabilities.
- **VideotronicMaker**: This script was originally forked from [VideotronicMaker/LM-Studio-Voice-Conversation](https://github.com/VideotronicMaker/LM-Studio-Voice-Conversation).

---

Enjoy using Camille Offline! If you have any questions or feedback, feel free to open an issue on the [GitHub repository](https://github.com/cfpg/Camille-Offline).