# Avatar Demo Setup - Complete Guide

## What Was Created

### 1. Demo Scripts (`avatars/` folder)
- ✅ 9 demo scripts (90-120 seconds each)
  - 7 CLI examples
  - 2 web app examples
- ✅ README.md with usage instructions

### 2. Demo Page (`demo.html`)
- ✅ Interactive demo page with:
  - Left panel: Code examples and explanations
  - Right panel: Video player for avatar explanations
  - Dropdown selector for all 9 examples
  - Responsive design

## File Structure

```
LangGraph 2/
├── avatars/
│   ├── README.md
│   ├── simple_graph.txt
│   ├── llm_graph.txt
│   ├── chat_loop.txt
│   ├── persistent_chat.txt
│   ├── tool_agent.txt
│   ├── advanced_pipeline.txt
│   ├── requirements_transformer.txt
│   ├── app_web_ui.txt
│   └── transformer_web_ui.txt
└── demo.html
```

## Next Steps

### 1. Generate Videos with HeyGen

For each script in `avatars/`:
1. Open HeyGen
2. Copy the script text from the `.txt` file
3. Paste into HeyGen's script editor
4. Select your avatar
5. Generate the video
6. Download as MP4
7. Save in `avatars/` folder with matching name:
   - `simple_graph.mp4`
   - `llm_graph.mp4`
   - etc.

### 2. View the Demo

1. Open `demo.html` in your browser
2. Select an example from the dropdown
3. The video will play in the right panel (if MP4 exists)
4. Code and explanations appear on the left

## Script Details

Each script:
- **Length**: 90-120 seconds when spoken
- **Content**: Explains what the code does, key concepts, and features
- **Tone**: Educational and friendly
- **Format**: Plain text, ready for HeyGen

## Demo Page Features

- **Responsive Design**: Works on desktop and mobile
- **Video Player**: HTML5 video player with controls
- **Auto-loading**: Videos load automatically when example is selected
- **Error Handling**: Gracefully handles missing video files
- **Navigation**: Easy switching between examples

## Testing

To test the demo page:
```bash
# Open in browser
open demo.html

# Or serve with Python
python3 -m http.server 8000
# Then visit http://localhost:8000/demo.html
```

## Notes

- Videos are expected to be MP4 format
- Video files should be named exactly as: `{example_name}.mp4`
- The demo page will show a placeholder if video is missing
- All scripts are optimized for 90-120 second duration
