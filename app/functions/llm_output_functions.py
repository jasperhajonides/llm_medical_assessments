import re
from datetime import datetime


def check_for_cpt_code(text):
    """
    Checks for the presence of a 5-digit CPT code in a given string.

    This function uses regular expressions to search for a 5-digit number (CPT code) in the provided text.
    It returns a boolean indicating whether such a code is found and the code itself if present.

    Parameters:
    text (str): The text string to be searched for a CPT code.

    Returns:
    tuple:
        - A boolean indicating whether a 5-digit CPT code is present.
        - The CPT code in integer format if present, or None if not present.
    """

    # Regular expression to find 5 consecutive digits
    match = re.search(r"\b\d{5}\b", text)

    if match:
        # Convert the found code to integer
        code = int(match.group())
        return True, code
    else:
        return False, None


def count_yes_no(strings):
    """
    Counts occurrences of 'Yes' and 'No' within the first five tokens of each string in a list.

    This function goes through each string in the provided list, tokenizes the string, and checks
    the first five tokens for occurrences of 'Yes' or 'No'. The search is case-insensitive. It counts
    the occurrences of each and returns the counts.

    Parameters:
    strings (list of str): A list of strings to be searched.

    Returns:
    tuple: A tuple containing two integers:
        - The count of 'Yes' occurrences.
        - The count of 'No' occurrences.
    """

    yes_count = 0
    no_count = 0

    for string in strings:
        tokens = string.split()[:5]
        for token in tokens:
            if re.search(r"\byes\b", token, re.IGNORECASE):
                yes_count += 1
                break
            elif re.search(r"\bno\b", token, re.IGNORECASE):
                no_count += 1
                break

    return yes_count, no_count


def calculate_age(dob_string, reference_date=None):
    """
    Calculate the age of a patient based on their date of birth extracted from a given string.

    Parameters:
    dob_string (str): A string containing the patient's date of birth in mm/dd/yyyy format.
    reference_date (str, optional): The date from which to calculate the age, in mm/dd/yyyy format.
                                   Defaults to the current date if not provided.

    Returns:
    int: The age of the patient.
    """
    # Regular expression to find the date of birth in the string
    dob_match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", dob_string)

    if not dob_match:
        raise ValueError("Date of birth not found in the provided string.")

    dob = datetime.strptime(dob_match.group(), "%m/%d/%Y")

    # Use the current date or the provided reference date to calculate the age
    if reference_date:
        reference_date = datetime.strptime(reference_date, "%m/%d/%Y")
    else:
        reference_date = datetime.today()

    # Calculate age
    age = (
        reference_date.year
        - dob.year
        - ((reference_date.month, reference_date.day) < (dob.month, dob.day))
    )

    return age


def check_age(age):
    """
    Check if the variable 'age' is a number or can be converted to a number.

    Parameters:
    age: The variable to be checked.

    Returns:
    bool: True if 'age' is a number or can be converted to a number, False otherwise.
    """
    if isinstance(age, (int, float)):
        # 'age' is already a number
        return True
    elif isinstance(age, str):
        # Try converting the string to a number
        try:
            float(age)  # Attempt to convert to float
            return True
        except ValueError:
            # Conversion failed, 'age' is not a number
            return False
    else:
        # 'age' is neither a number nor a string that can be converted
        return False


def detect_first_degree_relative(text):
    """
    Detects if a string contains any mention of a first-degree relative and identifies the relative.

    Parameters:
    text (str): The input string to be searched.

    Returns:
    tuple:
        - A boolean indicating whether a first-degree relative is mentioned.
        - The first identified first-degree relative or None if none is mentioned.
    """
    # Define a list of first-degree relatives
    relatives = ["mother", "father", "brother", "sister", "son", "daughter"]

    # Create a regular expression pattern to find these relatives
    pattern = r"\b(?:" + "|".join(relatives) + r")\b"

    # Search the text for the pattern
    match = re.search(pattern, text, re.IGNORECASE)

    # Check if a match is found and return the results
    if match:
        return True, match.group().lower()
    else:
        return False, None


def evaluate_success(yes_count, no_count):
    """
    Evaluates llm output based on counts of 'yes' and 'no' responses.

    The function calculates the percentage of 'yes' or 'no' responses and determines which
    one is in the majority. It returns a flag indicating the majority response and a result
    string that includes the calculated percentage or a statement of uncertainty if both
    counts are zero.

    Parameters:
    yes_count (int): The count of 'yes' responses.
    no_count (int): The count of 'no' responses.

    Returns:
    tuple:
        - flag (bool): True if 'yes' is in the majority, False if 'no' is in the majority,
                       None if both counts are zero.
        - result (str): A string indicating the calculated percentage or a statement of uncertainty.
    """
    if yes_count > no_count:
        flag = "Yes"
        perc = yes_count / (yes_count + no_count) * 100
        result = f"{perc:.2f}% sure"
    elif yes_count == 0 and no_count == 0:
        flag = None
        result = "Unsure."
    else:
        flag = "No"
        perc = no_count / (yes_count + no_count) * 100
        result = f"{perc:.2f}% sure"

    return flag, result
