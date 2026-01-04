# Avatar Demo Scripts for HeyGen

This folder contains demo scripts for each LangGraph example, designed to be used with HeyGen to create avatar explanation videos.

## Scripts Overview

Each script is approximately 90-120 seconds when read at a normal speaking pace (150-180 words per minute).

### CLI Examples:
1. **simple_graph.txt** - Basic sentiment analysis without LLM
2. **llm_graph.txt** - LLM-powered sentiment analysis with Ollama
3. **chat_loop.txt** - Multi-turn conversation with cycles
4. **persistent_chat.txt** - Checkpointing and thread-based conversations
5. **tool_agent.txt** - ReAct pattern with tool calling
6. **advanced_pipeline.txt** - 7-step document processing pipeline
7. **requirements_transformer.txt** - Human-in-the-loop transformation

### Web Apps:
8. **app_web_ui.txt** - General examples web interface
9. **transformer_web_ui.txt** - Requirements transformer web interface

## How to Use with HeyGen

1. **Upload Script**: Copy the text from any `.txt` file and paste it into HeyGen's script editor
2. **Select Avatar**: Choose your preferred HeyGen avatar
3. **Generate Video**: Let HeyGen generate the video with the avatar speaking the script
4. **Download MP4**: Download the generated MP4 file
5. **Place in Avatars Folder**: Save the MP4 file in this folder with the corresponding name:
   - `simple_graph.mp4`
   - `llm_graph.mp4`
   - `chat_loop.mp4`
   - `persistent_chat.mp4`
   - `tool_agent.mp4`
   - `advanced_pipeline.mp4`
   - `requirements_transformer.mp4`
   - `app_web_ui.mp4`
   - `transformer_web_ui.mp4`

## Demo Page Integration

Once you have the MP4 files, open `demo.html` in your browser. The page will automatically:
- Display the video in the right panel when you select an example
- Show the corresponding code and explanation on the left
- Allow you to navigate between examples

## Script Format

Each script:
- Explains what the example does
- Describes key LangGraph concepts demonstrated
- Highlights important features
- Provides context for understanding the code
- Is written in a conversational, educational tone

## Tips for HeyGen

- **Pacing**: The scripts are written for natural speech. HeyGen should handle pacing automatically
- **Pauses**: Natural pauses are included in the text for better flow
- **Tone**: Scripts use an educational, friendly tone suitable for tutorials
- **Length**: Each script targets 90-120 seconds, perfect for keeping attention

## File Naming Convention

The MP4 files must match the script names exactly:
- Script: `simple_graph.txt` → Video: `simple_graph.mp4`
- Script: `llm_graph.txt` → Video: `llm_graph.mp4`
- etc.

This ensures the demo page can automatically load the correct video for each example.

