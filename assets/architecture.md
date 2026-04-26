# PawPal+ System Architecture

## System Flow Diagram

![System Flow Diagram](./system-flow.png)

## Class Diagram

![Class Diagram](./class-diagram.png)

## Component Legend

| Layer | Color | Components |
|-------|-------|------------|
| **UI** | Orange | Streamlit web interface |
| **AI** | Blue | PawPalAI agent with agentic workflow |
| **Core** | Green | Domain models and scheduler |

## Flow Description

1. **User Input**: Owner enters pet info, creates tasks via Streamlit UI
2. **AI Processing**: PawPalAI analyzes tasks through 4-stage workflow
3. **Scheduling**: Core system uses knapsack algorithm to generate plan
4. **Output**: Schedule displayed with AI explanations and validation