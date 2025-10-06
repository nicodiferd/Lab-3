# Lab #3 Assignment: Building a Real-Time AQI Dashboard with Streamlit and AirNow API

## Objective
Create a web application using Streamlit that displays real-time Air Quality Index (AQI) information. The app will have two main functionalities:

1. Display a map of AQI levels for major cities in California. Each city marker is color-coded by AQI category.
2. Allow the user to input a ZIP code to retrieve the AQI for a specific location in the United States.

### Additional Functionality
In addition to the above two main functionalities, you are required to incorporate one **additional feature based on your creative thinking**. This can be anything that enhances the app, such as historical AQI data, visual enhancements, or any other feature that you feel adds value to the application. This part is **open-ended**, so feel free to be creative!

## Requirements

### 1. API Integration
You will use the **AirNow API** to fetch AQI data. You will need to sign up for a free API key from [AirNow](https://docs.airnowapi.org/).

### 2. California AQI Map
- Display a map of California with markers showing the AQI values for several pre-defined cities and towns.
- You can use the provided CSV file, which contains the ZIP codes of major cities and towns in California, to populate the map. The CSV file can be downloaded from the link: [california_zip_codes.csv](link).
- The map should be interactive, showing AQI levels and the category (e.g., Good, Moderate) when a user clicks on the markers. Each marker should be color-coded by AQI category.

### 3. ZIP Code AQI
- Allow the user to input any U.S. ZIP code and fetch the AQI for that location.
- Display the AQI and its category (e.g., Good, Moderate, Unhealthy) for the entered ZIP code.

### 4. Caching
- Use `st.cache_data` to optimize the API calls and map rendering so that repeated API requests for the same data are avoided.

## Example User Flow
1. The user enters an AirNow API key.
2. The app displays an interactive map showing AQI data for several major cities in California.
3. The user enters a ZIP code, and the app fetches and displays the AQI data for that location.
4. The user can also explore the additional feature you implemented based on your creative idea.

## Group-Based Activity
1. This is a **group-based activity**. Students can form their own groups, with each group consisting of **at least 2 members and no more than 3 members**.
2. **Each group needs to submit only one final version** of the app. The project will be developed over two sessions:
   - **Today**: Groups will work on developing the app and completing both required and additional functionalities.
   - **Next Class (Tuesday)**: Each group will demonstrate their app to the class, showcasing both the required features and the creative additional feature.

## Submission Requirements
1. **Streamlit App Source Code (.py)**: Submit the complete and functional Python file for the app.
2. **Video Demo of the App (.mp4/.mov)**: Provide a short video showing the working California AQI map and ZIP code AQI lookup feature.
3. **Feature Explanation (.pdf)**: Include a document explaining how your additional feature works.

**NOTE**: When submitting the assignment, the group member responsible for submission should list the **names of all other group members in the comment box**.

## Grading Criteria
- **Main Functionalities (50%)**: Focuses on whether students successfully implemented both the California AQI map and the ZIP code AQI lookup. This is the core functionality of the app.
- **Responsiveness and Efficiency (20%)**: Evaluates how well the app performs in terms of speed, caching, and avoiding unnecessary reloading.
- **Additional Feature: Creativity (15%)**: Assesses the value and creativity of the extra feature added.
- **Additional Feature: Implementation (15%)**: Looks at how well the additional feature is implemented, ensuring it works as intended and integrates with the rest of the app.
