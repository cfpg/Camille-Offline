# Camille - Your Local AI Voice Assistant

Camille is a Python-based AI voice assistant that runs entirely on your local machine, ensuring your privacy. It listens for a wake phrase, transcribes your voice commands, and uses a local Large Language Model (LLM) to provide intelligent responses. You can also interact with it through tools like weather, brave search and url visits.

## Key Features

*   **Privacy-Focused:** No data is sent to external servers. Everything stays on your machine.
*   **Voice Interaction:** Activate with a wake phrase and speak your commands naturally.
*   **Customizable:** Configure the assistant's name and voice.
*   **Offline Operation:** Works without an internet connection after initial setup.
*   **Tools:** Extend functionality with tools like weather information, web search, and more.
*   **Conversational Memory:** Maintains context across multiple interactions.

## Getting Started

Follow these instructions to set up and run Camille on your local machine.

---

### Prerequisites

*   **Anaconda:** A Python distribution for easy package management. Download and install it from the [Anaconda website](https://www.anaconda.com/).
*   **LM Studio:** A desktop application for running local LLMs. Download it from the [LM Studio website](https://lmstudio.ai/).

---

### Setting Up Your Python Environment

1.  **Create a Conda Environment:**

    Open a terminal and create a new Conda environment:
    ```
    conda create -n camille python=3.10
    ```
2.  **Activate the Environment:**
    ```
    conda activate camille
    ```
3.  **Clone the Repository:**
    ```
    git clone <repository_url>
    cd Camille
    ```
    Replace `<repository_url>` with the actual repository URL.
4.  **Install Dependencies:**
    ```
    pip install -r requirements.txt
    ```

---

### Configuration

1.  **LM Studio:**
    *   Download a compatible LLM model (e.g., `llama-3.2-3b-instruct`) in LM Studio.
    *   Start the LM Studio local inference server, ensuring it runs on `http://localhost:1234`.

2.  **Environment Variables:**

    Create a `.env` file in the project directory with the following content, filling in your actual API keys:
    ```
    PICOVOICE_ACCESS_KEY=""
    MODEL_NAME="llama-3.2-3b-instruct"
    OPENWEATHERMAP_API_KEY=""
    OPENWEATHERMAP_DEFAULT_CITY=""
    BRAVE_SEARCH_API_TOKEN=""
    ```
    *   **PICOVOICE\_ACCESS\_KEY:** Obtain this from [Picovoice Console](https://console.picovoice.ai/).
    *   **MODEL\_NAME:** The name of the LLM model you downloaded in LM Studio.
    *   **OPENWEATHERMAP\_API\_KEY:** (Optional) Sign up for an API key at [openweathermap.org](https://openweathermap.org/).
    *   **OPENWEATHERMAP\_DEFAULT\_CITY:** (Optional) Default city for weather requests.
    *   **BRAVE\_SEARCH\_API\_TOKEN:** (Optional) Get an API key from [Brave Search API](https://brave.com/search/api/).

---

### Running Camille

1.  **Start the Assistant:**
    ```
    python main.py
    ```

---

### Initial Setup Questions

The first time you run Camille, it will ask you a few questions to personalize your experience. These questions help the AI understand your preferences and provide more relevant responses. The questions are:

*   What's your name?
*   Which city do you live in?
*   What do you do for a living?

Your answers to these questions are stored locally and used to inform the AI's interactions with you.  This information is only used to improve the quality and relevance of the AI's responses and is not shared externally.  The answers will be passed on every new converastion in the system prompt to let the AI know more about you.

---

### Interacting with Camille

*   **Wake Up:** Say **"Hey Camille"** to activate the assistant.
*   **Speak Your Command:** After activation, speak your request clearly.
*   **Stop Camille:** Say **"Camille stop"** to interrupt the assistant.
*   **New Conversation:** Say **"New conversation"** to clear the memory and start fresh.

---

### Tools and AI Functionality

Camille leverages a variety of tools to enhance its capabilities and provide more comprehensive assistance. These tools allow the AI to access real-time information, perform specific tasks, and deliver more accurate and relevant responses.

The AI intelligently determines when and how to use these tools based on your requests. When you ask a question that requires external data or a specific action, Camille will automatically select the appropriate tool, retrieve the necessary information, and incorporate it into its response. This seamless integration of tools allows for a more dynamic and helpful conversational experience.

Here are the available tools:

*   **Weather:** Provides current weather information for a specified city.  Activated when you ask about the weather.
*   **Brave Search:** Searches the web for information on a given topic. Activated when you request information not readily available in the AI's knowledge base.
*   **Visit URL:** Extracts the main text content from a specified URL.  Activated when you ask the AI to summarize a webpage.

To enable the full functionality of these tools, ensure you have correctly configured the necessary API keys in the `.env` file, as described in the Configuration section.

---

## Contributing

We welcome contributions to improve Camille Offline! If you'd like to contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
