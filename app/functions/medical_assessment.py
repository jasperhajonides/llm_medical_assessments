from functions.llm_output_functions import *


def run_assessment(query_engine, temp_csv):

    # Number of iterations for confidence check
    n_iterations = 9

    while True:
        # Update status
        with open("status.txt", "w") as status_file:
            status_file.write(
                "First, we extract code for requested treatment... (Please be patient)"
            )

        response = query_engine.query(
            """Hospitals use CPT codes to treatments, 
                                      these codes are 5 digits. Can you identify any of these codes 
                                      related to treatments in this report?"""
        )
        text = response.response

        code_present, code = check_for_cpt_code(text)
        with open(temp_csv, "a") as file:
            file.write("desc,confidence,output\n")
            file.write(
                f"CPT code for the requested treatment,-,{code}\n"
            )  # Example data

        if code != 45378:
            break

        # --------Check age of patient----------------------------
        # now lets get the age of the patient, because this will be relevant later:
        response = query_engine.query(
            """What is the date of birth of the patient in this report?
 """
        )

        # Example usage
        dob_string = response.response
        # Calculate age as of today,
        # We can also insert the date at which the report was created in calculate_age().
        age = calculate_age(dob_string)
        age_present = check_age(age)  # check if valid number
        with open(temp_csv, "a") as file:
            file.write(f"Patients age is: ,-,{age}\n")  # Example data

        # -------------check if there has been a successful treatment---------------
        # run the model 'n_iterations' times to check if there was a previous successful treatment.
        # multiple iterations help the model to be more accurate due to inherent noise.
        #   It also helps flush out different formats of responses that dont
        #   work so well for my hack-y string detection code.

        # write status
        with open("status.txt", "w") as status_file:
            status_file.write("Determining if there has been a successful treatment...")

        checks = []
        for i in range(n_iterations):
            response = query_engine.query(
                "Has there been a previous treatment that successfully improved colonalrectal or absominal discomfort? Answer with a yes or a no"
            )
            checks.append(response.response)

            # update status
            with open("status.txt", "w") as status_file:
                status_file.write(
                    f"Determining if there has been a successful treatment... {i+1}/{n_iterations}"
                )
        yes_count, no_count = count_yes_no(checks)

        # check if successfully treated.
        result_previous_success, perc_successfully_treated = evaluate_success(
            yes_count, no_count
        )

        # write results in dash table
        with open(temp_csv, "a") as file:
            file.write(
                f"Previous sucessful treatment?: ,{perc_successfully_treated},{result_previous_success}\n"
            )  # Example data

        # if successfully treated, break
        if result_previous_success == "Yes":
            break

        # ------------If 45 or older check if they already had a colonoscopy----------------
        #
        if age >= 45:
            checks = []
            for i in range(n_iterations):
                response = query_engine.query(
                    "Check if patient already had a colonoscopy in past 10 years, apart from one that is possible scheduled, yes or no?"
                )
                checks.append(response.response)

                # update status
                with open("status.txt", "w") as status_file:
                    status_file.write(
                        f"Determining if there has already been a colonoscopy... {i+1}/{n_iterations}"
                    )

            yes_count, no_count = count_yes_no(checks)
            result_already_had_colonoscopy, colonoscopy_perc = evaluate_success(
                yes_count, no_count
            )

            # write results in dash table
            with open(temp_csv, "a") as file:
                file.write(
                    f"Already had a colonoscopy?: ,{colonoscopy_perc},{result_already_had_colonoscopy}\n"
                )  # Example data
        else:
            result_already_had_colonoscopy = "N/A"
        # -------------If 40 or older check the following---------------
        # -------------CHeck if there is any family history of colorectal cancer---------------

        if age >= 40:
            checks = []
            relative_yn = []
            for i in range(n_iterations):
                response = query_engine.query(
                    "Is there any family history of colorectal cancer? If yes, answer just with the family relationship"
                )
                checks.append(response.response)

                relative_present, relative = detect_first_degree_relative(
                    response.response
                )
                relative_yn.append(relative_present)

                # update status
                with open("status.txt", "w") as status_file:
                    status_file.write(
                        f"Checking for colon cancer in first-degree family history... {i+1}/{n_iterations}"
                    )

            # if we detect less than 25% of the time, we can assume they dont have colonoscopy
            #   check if first degree history:
            if sum(relative_yn) / len(relative_yn) < 0.25:
                result_relatives = "No"
                confidence = (1 - sum(relative_yn) / len(relative_yn)) * 100
            else:
                result_relatives = "Yes"
                confidence = (sum(relative_yn) / len(relative_yn)) * 100

            confidence_str = f"{confidence} % sure"  # flip

            with open(temp_csv, "a") as file:
                file.write(
                    f"First-degree family history of colorectal cancer?: ,{confidence_str},{result_relatives}\n"
                )  # Example data

            # ------------- Check if symptomatic ---------------

            checks = []
            for i in range(n_iterations):
                response = query_engine.query(
                    "Is the patient symptomatic (e.g. abdominal pain, iron deficiency anemia, rectal bleeding)? Answer just yes or no."
                )
                checks.append(response.response)

                # update status
                with open("status.txt", "w") as status_file:
                    status_file.write(
                        f"Checking if the patient is symptomatic... {i+1}/{n_iterations}"
                    )

            yes_count, no_count = count_yes_no(checks)
            result_symptomatic, sympomatic_perc = evaluate_success(yes_count, no_count)

            with open(temp_csv, "a") as file:
                file.write(
                    f"Is the patient symptomatic?: ,{sympomatic_perc},{result_symptomatic}\n"
                )  # Example data
        else:
            result_symptomatic = "N/A"
            relative_present = "N/A"
        # ------------- Juvenile polyposis ---------------

        checks = []
        for i in range(n_iterations):
            response = query_engine.query(
                "Check if patient already had a colonoscopy in past 10 years, apart from one that is possible scheduled, yes or no?"
            )
            checks.append(response.response)

            # update status
            with open("status.txt", "w") as status_file:
                status_file.write(
                    f"Determining if there has already been a colonoscopy... {i+1}/{n_iterations}"
                )

        yes_count, no_count = count_yes_no(checks)
        result_juv, juv_polyposis_perc = evaluate_success(yes_count, no_count)

        # write results in dash table
        with open(temp_csv, "a") as file:
            file.write(
                f"Juvenile polyposis reported in the document?: ,{juv_polyposis_perc},{result_juv}\n"
            )  # Example data

        break

    if code != 45378:
        # update status
        with open("status.txt", "w") as status_file:
            status_file.write(
                f"""
                            
                            Assessment complete. 
                            \n
                            Dear Sir/Madam, \n
                            \n
                            The patient does not request a diagnostic colonoscopy (CPT code: 45378).\n
                            \n
                            Kind regards,
                            Jasper                          
                            """
            )

    elif result_previous_success == "Yes":
        with open("status.txt", "w") as status_file:
            status_file.write(
                f""" 
                            Assessment complete. \n
                            \n 
                            Dear Sir/Madam,\n
                            \n
                            The patient has been treated successfully, diagnostic colonoscopy (CPT code: 45378) may not be required. \n
                            Please get in touch if you have any questions. \n
                            \n
                            Kind regards, \n
                            Jasper                          
                            """
            )

    elif (
        ((age > 45) & (result_already_had_colonoscopy == "No"))
        | (result_juv == "Yes")
        | ((age >= 40) & (result_relatives == "Yes") & (result_symptomatic == "Yes"))
    ):
        with open("status.txt", "w") as status_file:
            status_file.write(
                f""" 
                                Assessment complete. \n
                                \n 
                                Dear Sir/Madam,
                                \n
                                Diagnostic colonoscopy (CPT code: 45378) is advised: \n \n
                                Age: {age} \n
                                Previous colonoscopy: {result_already_had_colonoscopy} \n
                                First-degree history of colorectal cancer: {result_relatives}, Currently sympomatic: {result_symptomatic} \n
                                Juvenile polyposis reported in the document: {result_juv} \n 
                                \n
                                Kind regards, \n
                                Jasper                          
                        """
            )

    else:
        with open("status.txt", "w") as status_file:
            status_file.write(
                f""" 
                                Assessment complete. 
                                \n
                                Dear Sir/Madam,\n
                                \n
                                Diagnostic colonoscopy (CPT code: 45378) may not be required.: \n \n
                                Age: {age} \n
                                Previous colonoscopy: {result_already_had_colonoscopy} \n
                                First-degree history of colorectal cancer: {result_relatives}, Currently sympomatic: {result_symptomatic} \n
                                Juvenile polyposis reported in the document: {result_juv} \n 
                                \n
                                Kind regards, \n
                                Jasper                          
                        """
            )
