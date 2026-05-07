# CS122-Project

## Project Title:
NASA Climate Data Dashboard

## Authors:
Ryuto Kawabata\
Jane Tiche

## Project Description:
This project is a Python-based application designed to collect, analyze, and visualize climate-related data from public APIs. The system allows users to explore long-term trends in global sea levels and understand climate change impacts. Data will be retrieved from online source such as NASA. The application processes and analyzes the data to identify patterns and trends. The results will be displayed through interactive visualizations, providing users with a clear understanding of climate data.

---

## Project Outline / Plan:
1. Retrieve sea level and climate data from NASA API
2. Store the data locally in structured formats (CSV/JSON)
3. Clean and preprocess the data using Python
4. Analyze trends such as average sea level rise over time
5. Visualize the data using graphs
6. Build an interactive interface for user interaction

---

## Interface Plan:
The interface is built using Python (Tkinter).

The application will include:
- A main window with two tabs (Sea Level and Climate), each with its own metric and station controls
- A shared secondary window for displaying graphs and statistics
- Buttons to fetch and update data
- Input fields for filtering data (e.g., date range)
- Dropdown menu for user to select a station/location from a preset list

---

## Data Collection and Storage Plan (Author #1: Ryuto Kawabata)
1. The program uses NASA API to retrieve data.
2. Retrieved data wil be stored locally in structured formats, like CSV and JSON files.
3. The system will allow updating stored data when new API calls are made.
4. Basic error handling will be implemented for failed API requests.

---

## Data Analysis and Visualization Plan (Author #2: Jane Tiche)
1. The collected data will be loaded from local storage into Python for analysis.
2. The data will be cleaned and structured using libraries such as NumPy and Pandas, including handling missing values and formatting data types.
3. The program will analyze the data by calculating trends such as average sea level rise over time and identifying patterns or changes.
4. The results will be visualized using Matplotlib, with line plots showing how sea level changes over time.
5. The visualizations will update dynamically when new data is loaded or when user input changes.

---

## Technologies Used:
- Python
- Requests (API communication)
- Pandas & NumPy (data processing)
- Matplotlib (visualization)
- Tkinter (user interface)
