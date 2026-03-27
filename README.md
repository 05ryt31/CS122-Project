# CS122-Project

## Project Title: 
NASA Climate Data Dashboard

## Authors: 
Ryuto Kawabata\
Jane Tiche

## Project Description:
This project is a Python-based application designed to collect, analyze, and visualize climate-related data from public APIs. The system allows users to explore long-term trends in global sea levels and understand climate change impacts. Data will be retrieved from online sources such as NASA and other public APIs (if needed). The application processes and analyzes the data to identify patterns and trends. The results will be displayed through interactive visualizations, providing users with a clear understanding of climate data.


## Project Outline/Plan:

### Interface
The interface will be built using Python (Tkinter).
The application will include:
- A main window for selecting data sources and preferred statistics
- A secondary window for displaying graph and statistics
- Buttons to fetch and update data
- Input fields for filtering data (e.g., date range)
- Potential entry box for user to input location

### Data Collection and Storage Plan (Author #1: Ryuto Kawabata)
1. The program will use public APIs (such as NASA API) to retrieve data.
2. Data will be stored locally in files such as CSV or JSON format.
3. The system will allow updating the stored data when new API calls are made.

### Data Analysis and Visualization (Author #2: Jane Tiche)
1. Transfer the data file from github into Python
2. Data cleanup with NumPy and Pandas
3. Calculate sea level rise trends, averages/trends
4. Use Matplotlib to create graphs for visualization
5. Make sure the graph updates to user input 
