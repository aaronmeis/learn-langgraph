# Sample Requirements Documents

This folder contains sample requirements documents written in a conversational, "asking for an example" style. These can be used as input for the Requirements Transformer examples (G and I).

## Available Samples

### 1. E-Commerce Platform (`sample_1_ecommerce.md`)
A complete e-commerce platform with customer and admin features, payment processing, and order management.

**Use Case**: Online store with shopping cart and checkout
**Complexity**: Medium-High
**Domain**: E-commerce, Retail

### 2. Task Management Application (`sample_2_task_manager.md`)
A team collaboration tool for managing tasks, projects, and team workflows.

**Use Case**: Team task management and collaboration
**Complexity**: Medium
**Domain**: Project Management, Collaboration

### 3. Blog Platform (`sample_3_blog_platform.md`)
A content publishing platform for writers and readers with articles, comments, and subscriptions.

**Use Case**: Blogging and content publishing
**Complexity**: Medium
**Domain**: Content Management, Publishing

### 4. Weather Application (`sample_4_weather_app.md`)
A weather app showing current conditions, forecasts, and location-based weather information.

**Use Case**: Weather information and forecasts
**Complexity**: Low-Medium
**Domain**: Weather, Mobile Apps

### 5. Fitness Tracker (`sample_5_fitness_tracker.md`)
A comprehensive fitness and health tracking application with workouts, nutrition, and goals.

**Use Case**: Personal fitness and health tracking
**Complexity**: Medium-High
**Domain**: Health & Fitness, Mobile Apps

## How to Use These Samples

### With Requirements Transformer (CLI)

```bash
# Activate virtual environment
venv\Scripts\activate.bat  # Windows CMD
# or
venv\Scripts\Activate.ps1  # Windows PowerShell

# Run transformer with a sample
python requirements_transformer.py
# When prompted, provide path to sample file:
# requirements/sample_1_ecommerce.md
```

### With Transformer Web App

```bash
# Start the web app
python transformer_app.py

# Open http://localhost:5001
# Use the file upload or paste content from a sample file
```

## Document Format

These requirements documents are written in a natural, conversational style as if someone is describing what they want built. They include:

- **Project Overview**: High-level description
- **Core Features**: Main functionality requested
- **Technical Requirements**: Technical constraints and needs
- **Must-Have vs Nice-to-Have**: Prioritization
- **Timeline/Budget**: Project constraints

## Customization

Feel free to:
- Modify these samples for your own use cases
- Create new requirement documents following the same style
- Use them as templates for your own projects
- Test the transformer with different scenarios

## Notes

- These are example requirements, not complete specifications
- They're designed to demonstrate the transformer's capabilities
- Real requirements documents would typically be more detailed
- The transformer converts these to IEEE 830 format

---

**Tip**: Start with `sample_4_weather_app.md` (simplest) to test the transformer, then try more complex examples like `sample_1_ecommerce.md`.

