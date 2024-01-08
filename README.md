# Medical Report Assessment

## Project Overview

This project is an assessment from Co:Helm focused on evaluating medical reports that request specific treatments. Our objective is to determine the appropriateness of the requested treatment based on a set of predefined rules and information extracted from these documents.

## Approach

We developed an interactive dashboard that leverages the Llama Index to sequentially search for pertinent pieces of information within the medical reports. The process involves the following steps:

1. **Identifying the Requested Procedure**: Our first task is to ascertain the nature of the requested treatment. We only have the guidelines for colonoscopy (CPT dode 45378) available so if the procedure is not a colonoscopy, the search is terminated early.

2. **Assessing Previous Treatments**: We evaluate if the patient has already undergone successful treatment for the condition in question. An early stop is initiated if this is the case.

3. **Further Searches for Colonoscopy Guidelines**: If the requested procedure is a colonoscopy and there's no history of successful treatment, we proceed to search the patient's documents for specific colonoscopy guidelines.

The dashboard is designed to be intuitive, guiding the user through each step of the process.

## How to Run the Code

To run the application, follow these steps:

1. **Clone the Repository**:
    ```
   git clone [repository-url]
    ```

2. **Build the Docker Image**:
    ```
   docker build -t medical_report_assessment -f Dockerfile .
    ```

3. **Run the Docker Container**:
    ```
   docker run -v .:/code -p 80:80 medical_report_assessment
    ```

4. **Access the Dashboard**:
   Open your web browser and navigate to `http://0.0.0.0:80/`. Follow the on-screen instructions to proceed.

## File Structure

Below is the basic structure of the project:

```
medical_report_assessment/
│
├── app/               # Application code
│   ├── data/          # uploaded .pdf files.
│   ├── functions/     # Function modules
│   │   ├── llm_output_functions.py  # functions to process mistral output
│   │   ├── medical_assessment.py    # asking all the questions
│   │   └── styling_functions.py     # page styling
│   └── main.py        # Main application script
│
├── Dockerfile         # Dockerfile for setting up the application environment
├── requirements.txt   # List of package dependencies
└── README.md          # Documentation (this file)
```

**Note**: Replace `[repository-url]` with the actual URL of your Git repository.