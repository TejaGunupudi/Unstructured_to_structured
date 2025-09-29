class PromptBuilder:
    GENERAL_PHYSICAL_REQ_PROMPT: str = (
        "Extract the number of hours for physical activities of Sit, Stand and Walk "
        "which are circled out basically from the image for all the 4 activities of Sit, Stand, Walk and Drive motor Vehicle."
    )
    ATTENDANCE_REQ_PROMPT: str = (
        "Regarding work attendance and eligibility for alternative worksite arrangements: "
        "(these are checkboxes in the content), give in the following format:\n"
        "(keep a quick note that sometimes these marked checkboxes will be represented as in some symbol(like 9 or square root) "
        "before start of the statement because of wrong format in the content, so if you see such symbols that particular statement is true "
        "for this section, if check box is empty then its a false for that statement)\n"
        "must_attend_workplace : <boolean>,\n"
        "alt_worksite_eligible: <boolean>,\n"
        "wfo_essential: <boolean>,\n"
        "wfo_non_essential: <boolean>"
    )
    KEYBOARD_SUFFIX_STRING: str = (
        "keyboarding:\n"
        "right: false\n"
        "left: false\n"
        "both: false\n"
        "filing:\n"
        "right: false\n"
        "left: false\n"
        "both: false\n"
    )

    def constructPositionSummaryPrompt(self, extracted_position_summary: str):
        return f"""
        Extracted Text: {extracted_position_summary}
        Task:
        - Clean the following text by fixing spelling mistakes, correcting formatting issues, and making it more readable while retaining the original meaning. Return the cleaned paragraph without any unnecessary characters or errors.
        - don't include "marry, arry , rry, ry, y" if it is a first word
        - give me only position summary details exclude if any other detils found like "Professor, Chair of Department, Name of Supervisor"
        - give me in a single string.
        """

    def constructActiveHrsExtractionPrompt(
        self, extracted_text_general_physical_activity: str
    ):
        return f"""

    For each activity listed (Sitting, Standing, Walking, Driving a Motor Vehicle):

    extracted text: {extracted_text_general_physical_activity}
    extracted part of the text use both but give me the correct number of hours for the general physical requirements u can observe the text also wherever number is put in brackets or
    rounded of with a rectangle box that might be the number of hours, check it out, the numbers should be from 0 to 8, so mostly which ever is missing or breaking the flow or a number
    is put in brackets then that is the correct number of hours, for example: for a n activity if the extracted numbers are:
    Example1:  0 12 3 4 5[6]7 8 x here number of hours is 6 - as 6 is put in brackets
    Example2: 0 23 4 5 67 8 X here number of hours is 1 - as 1 is missed completely after 0 from left to right
    Example3: 0 23 4 5 6 7 8 xX here 1 is number of hours as 1 is missed completely
    Example 4: 0 12 3 4 5 6 7 8 here it is 0 as no number is put in brackets or missed
    Example 5: Sit 0 12 3 4 6 7 8 x here it is 5 as 5 is missing from the flow
    Example 6: Stand 0 23 4 5 6 7 8 x here it is 1 as 1 is missing from the flow
    Example 7: Walk 0 23 4 5 6 7 8 X here it is 1 as 1 is missing from the flow
    Example 8:
    0 3 4 5 6 7 8 xX
    Drive Motor 2
    Vehicle:
    here in this example it is a little disoriented but observed properly it is 1 as 1 is missing from the flow

    Example 9: Drive Motor 0 123 4 5 6 7 8 here it is 0 as no number is put in brackets or missed
    give the answer simple no need of any explanations: like
    sit - number of hours required
    stand - number of hours required
    ....
    """

    def constructAttendancePrompt(self, extracted_text_attendance_req: str):
        return f"""
Extracted Text: {extracted_text_attendance_req}

Task:
Format the extracted information into the following structured format:
must_attend_workplace: <boolean>,
alt_worksite_eligible: <boolean>,
wfo_essential: <boolean>,
wfo_non_essential: <boolean>

Key Rules to Follow:
There are two "or" conditions in the provided text:
    1. "must_attend_workplace" OR "alt_worksite_eligible"
        a. If one is true, the other must be false.
    2. "wfo_essential" OR "wfo_non_essential"
        b. If one is true, the other must be false.

Anywhere 9 is mentioned before the statement then it is true so you can make the alternate one false.
For example:
- If 9 is mentioned before "IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT" then alt_worksite_eligible will be false (so must_attend_workplace would be true).
- If 9 is mentioned before "ESSENTIAL" then wfo_essential will be false (making wfo_non_essential true).
- If 9 is mentioned before "NON-ESSENTIAL" then wfo_non_essential will be false (making wfo_essential true).

Example 1: (where 9 is present before the text)
Extracted text:
sition:
9 REQUIRES ATTENDANCE AT THE WORKPLACE

or

1] IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT (request forms required)

-And is considered:

ESSENTIAL (per inclement weather policy, essential employees are expected to report to and work at their
assigned campus worksite)

or

9 NON-ESSENTIAL (able to
markdown response...............

In this example:
- 9 is mentioned before "REQUIRES ATTENDANCE AT THE WORKPLACE" so must_attend_workplace = true, thus alt_worksite_eligible = false.
- 9 is mentioned before "NON-ESSENTIAL" so wfo_non_essential = true, thus wfo_essential = false.

Final output:
must_attend_workplace: true
alt_worksite_eligible: false
wfo_essential: false
wfo_non_essential: true

Example 2: (where 0 and ¢ is present before the text)
Extracted Text:
ITION:
0 REQUIRES ATTENDANCE AT THE WORKPLACE

or

¢ IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT

And is considered:

¢ ESSENTIAL (per inclement weather policy, essential employees are expected to report
to and work at their assigned campus worksite)

or

1 NON-ESSENTIAL (__ able

Interpretation:
- ¢ means false. Since ¢ is mentioned before "IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT", alt_worksite_eligible = false, so must_attend_workplace = true.
- ¢ before "ESSENTIAL" means wfo_essential = false, so wfo_non_essential = true.

Final output:
must_attend_workplace: true
alt_worksite_eligible: false
wfo_essential: false
wfo_non_essential: true

Example 3: (¢, e - represents false, 1 represents true )
Extracted text:
0 REQUIRES ATTENDANCE AT THE WORKPLACE

or

¢ IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT (request forms required)
And is considered: ,

e ESSENTIAL (per inclement weather policy, essential employees are expected to report to
and work at their assigned campus worksite)

or

1 NON-ESSENTIAL (able to

Here:
- ¢ before "IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT" means alt_worksite_eligible = false, so must_attend_workplace = true.
- e before "ESSENTIAL" means wfo_essential = false, so wfo_non_essential = true.

Example 4:
Given the extracted text:
"or

0 IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT (request forms required)

And is considered:

O ESSENTIAL (per inclement weather policy, essential employees are expected to report to and work at their
assigned campus worksite)

or

9"
Interpretation:
- 0 before "IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT" means alt_worksite_eligible = false, so must_attend_workplace = true.
- O (treated same as 0) before "ESSENTIAL" means wfo_essential = false, so wfo_non_essential = true.

Final output:
must_attend_workplace: true
alt_worksite_eligible: false
wfo_essential: false
wfo_non_essential: true

Example 5:
Extracted Text:
¢ IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT (request forms
required)

And is considered:

e ESSENTIAL (per inclement weather policy, essential employees are expected to report
to and work at their assigned campus worksite)

No additional information or explanations are needed in the response.

Interpretation:
- ¢ means alt_worksite_eligible = false, so must_attend_workplace = true.
- e means wfo_essential = false, so wfo_non_essential = true.

Final output:
must_attend_workplace: true
alt_worksite_eligible: false
wfo_essential: false
wfo_non_essential: true

Example 6:
Extracted Text:
or

O IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT

And is considered:

0 ESSENTIAL (per inclement weather policy, essential employees are expected to report to and work at their
assigned campus worksite)

or

9

Interpretation:
- O (0) before "IS ELIGIBLE FOR ALTERNATIVE WORKSITE ARRANGEMENT" means alt_worksite_eligible = false, so must_attend_workplace = true.
- 0 before "ESSENTIAL" means wfo_essential = false, so wfo_non_essential = true.

Final output:
must_attend_workplace: true
alt_worksite_eligible: false
wfo_essential: false
wfo_non_essential: true

Example 7:
9 IS ELIGIBLE TO APPLY FOR ALTERNATIVE WORKSITE ARRANGEMENT

And is considered:

ESSENTIAL (per inclement weather policy, essential employees are expected to report to and work at their
assigned campus worksite)

or

9 NON-ESSENTIAL (able to work from home when the office closes for inclement weather)

for this example the answer is:
must_attend_workplace: false
alt_worksite_eligible: true
wfo_essential: false
wfo_non_essential: true

because 9 is present before "IS ELIGIBLE TO APPLY FOR ALTERNATIVE WORKSITE ARRANGEMENT" so alt_worksite_eligible is true and must_attend_workplace is false
and 9 is present before "NON-ESSENTIAL (able to work from home....)" so wfo_non_essential is true and wfo_essential is false
    """

    def constructMarkdownPrompt(
        self,
        general_physical_req_prompt: str,
        attendance_req_prompt: str,
        file_name: str,
    ):
        return f"""
    I have attached the PDF pages(job description of {file_name}) as images here, in the same order of the pages, now i want your help in providing the content back in the same order but in markdown format that a
    language model can understand. I want all the content to be provided accurately, meaning no content should be missed. At the same time, I want you to give me the complete content
    properly, as I will use this data to understand and convert it into a structure that can be used for further processing. In some places there is a table break from 1 image to other
    image so please take care of that and provide the content properly. Strictly note not to miss any information while extracting.

    Few things to note:
    For the general information you can write it like key value pairs.extract each element in the content, if anywhere there is no information then put that element as blank.
    from the position summary Use standard headers (#, ##, ###), lists (-, *, 1.), and formatting to clearly define the hierarchy of data.
    For the duties and responsibilities for each metric please get the percentage of time and also essential functions in this format:
    responsibilty: <responsibility> ... responsibility is nothing but a header for the tasks in the content not the tasks, if no header is present then you can generate one and add here. if there is no star or symbol present for essential functions then it is false, if present then true
    time_spent_percentage: <percentage>
    essential_function: <boolean> if the essential function is not represented by any symbol then you can put false, if it is represented by any symbol then put true
    tasks: [list of tasks]
    if time_spent_percentage is blank mark it as 0 and if essential_function is missing mark it as False but don't miss any tasks below
    For physical requirements:

    General Physical Requirements:
    for each activity check if the activity is intermittent or constant, the itermittent or constant are defined as columns, where 'x' is mentioned for that activity it is intermittent or constant
    with this particular intermittent or constant column, i would need the number of hours for the activity, {general_physical_req_prompt}
    now tell me here for each activity how many number of hours it is and also if it is intermittent or constant,
    for this section you can follow this format for example: sit: <number of hours> <intermittent/constant>

    Position-Specific Physical Requirements:
    For activities such as Squatting, Bending, Kneeling, and Reaching has sub parts(Overhead, Forward, Low), Twisting, Crawling, Climbing has sub parts(Ladder, Stairs, or Other), 'Walking on rough ground',
    'Exposure to changes of temperature/humidity', 'Exposure to dust/fumes/gases/chemicals', 'Being near moving machinery', 'Working from heights'
    Check the category ('Occasionally', 'Between 2-5 hrs daily', 'Over 5 hrs daily') it is in the same order in the image from left to right.
    give me this section in the this format:
    activity: frequency , if there is no x in that activity for that particular frequency put blank string:
    for example:
    squatting: "" # whatever is applicable
    Bending:  # whatever is applicable (if x is in first column then it is occasionally, if x is in second column then it is between 2-5 hrs daily, if x is in third column then it is over 5 hrs daily)
    ...

    For Weight lifting requirements('THIS POSITION REQUIRES EMPLOYEE TO: '):
    For items requiring lifting, carrying, pushing, or pulling specific weight ranges, return the text label (e.g., L.C.P.PL -- L is Lifting, C is Carrying, P is Pushing, PL is Pulling) for the specific weights mentioned('11-24 lbs', '25-49 lbs', '50-74 lbs', '75-100lbs', 'Over 100 lbs'). frequency: ........# < frequency is less than 2 hrs daily/ Up to 2 hrs daily/ Between 2-5 hrs daily/ Over 5 hrs daily> mostly weight will be one for each activity.
    give this weight lifting requirements in this format: (define for each activity in which weight range and which frequency was mentioned)
    Lift:
        weight_range:....(for all weight ranges specified we need)
        frequency:...
    Carry:
        weight_range:...
        frequency:...
    Push:
        weight_range:...
        frequency:....
    Pull:
        weight_range:
        frequency:
    Note: If LCPL is mentioned then it is for all the 4 activities, if only LC is mentioned then it is for only lift and carry activities, If nothing is mentioned then you can put empty string or no need to mention anything,if x is mentioned then also for all activities, for all weights, range and frequency will be empty.

    For tools (' POSITION REQUIRES USE OF HANDS OR SPECIAL TOOLS/EQUIPMENT FOR:')
    For tools/equipment handling identify if each is right/left/both handed and return the text label for the respective tool/equipment.
    Give this in the format:
    task: keyboarding:
    (here right is the first column, left is the second column, both is the third column so where x is there it can be picked up)
    right: <true/false>
    left: <true/false>
    both: <true/false>
    task: filing:
    right: <true/false>
    left: <true/false>
    both: <true/false>
    other_description: <string> (if any other description is there write it here)

    Other Categories:
    For questions related to work attendance and eligibility for alternative worksite arrangements:
    Assess if 'Essential', 'Non-Essential', etc., have 'X' marked and return '1' for 'X', '0' for no 'X'.

    For Qualifications and Attributes:
    For Required Qualifications also incase any required license or certification details is mentioned additionally, you can extract/include that also here
    In preferred qualifications sometimes there is a line space so dont miss that information,
    for example: (just an example to understand the pattern for this)
    Educational coursework .....

    An equivalent combination of ....

    The ideal candidate ....

    For zone definition factors:
    Also dont miss extracting zone definition factors if it present in the content. if there are multiple paras then you can put all in one para, but dont miss even one point from the content. (This is very important DONT SKIP ANY POINTS, PUT EVERYTHING IN THE PARA)

    For supervision:
    There will be nature of supervision or details related to it, if anything related to supervision is present in the content you can put all the information on supervision in one para. (This is very important DONT SKIP ANY POINTS, PUT EVERYTHING IN THE ONE PARA)

    {attendance_req_prompt}

    The Job Family Zone Questionnaire is not needed for the structured format, so ignore it.

    If incase very few sections among all the mentioned are present give those content only, but if all the sections are present then give all the content in the same order as mentioned above.

    At the end of your response, please provide a structured JSON object containing confidence scores for each of the following categories on how much confident you are while extracting these specifics:

"confidence_scores": {{
    "general_information": <confidence score>,
    "position_summary": <confidence score>,
    "duties_and_responsibilities": <confidence score>,
    "supervision": <confidence score>,
    "qualifications_and_attributes": <confidence score>,
    "zone_definition_factors": <confidence score>,
    "physical_activities": {{
        "general_physical_reqs": <confidence score>,
        "special_physical_reqs": <confidence score>,
        "lifting_handling_reqs": <confidence score>,
        "manual_dexterity_reqs": <confidence score>,
        "work_attendance_reqs": <confidence score>
    }},
    "application_procedure": <confidence score>,
    "additional_information": <confidence score>
}}

Make sure this JSON block is the last thing in your response and that it is syntactically valid JSON.
    """

    @classmethod
    def constructQualifactionPrompt(cls, qualifications_lines: str):
        return f"""
I want you to extract the qualifications specifics in the mentioned JSON format from the given data.
Make sure to correctly classify the qualifications into the appropriate list in the JSON, based on the content provided.

### Rules:
1. Any qualifications explicitly marked as "minimum qualifications" should go under "minimum_qualifications," even if they appear to be helpful or beneficial.
2. If the qualifications are implied as required but not explicitly stated, place them under "required_qualifications".
3. If the qualifications are preferred or considered a bonus, place them under "preferred_qualifications".
4. Qualifications that could be helpful but are not explicitly required or preferred go under "helpful_qualifications".
5. Any additional information that does not fit into the above categories goes under "other_information".

### Important:
- All qualifications listed under a specific header, such as "minimum qualifications," must be fully included in the corresponding category in the JSON, even if they seem to fit other categories like helpful or preferred.
- Do not split sentences from the same qualification header into different categories.

Qualification JSON:
{{
"required_qualifications": [],
"preferred_qualifications": [],
"helpful_qualifications": [],
"minimum_qualifications": [],
"other_information": []
}}

Input data:
{qualifications_lines}

Your task is to parse the input data carefully and provide the output in the exact JSON format above. Make sure no qualifications are missed or misplaced, and all points under "minimum qualifications" go directly under "minimum_qualifications".
    """

    def constructJsonConversionPrompt(self, markdown_response: str):
        return f"""
    I am sharing a PDF content in markdown format below:
    {markdown_response}

    I want you to convert this markdown content into a JSON format, the sample of format sharing below: (If information is not present then put empty string dont assume and add any information strictly follow the content)
    The content beneath each header is captured in full, including multiline paragraphs and bullet points, and stored as the value of the corresponding key.
    Also give me only the json as asked, no need of any explanations or any other content, just the json format as asked. For null values you can put empty string
    {{
    "general_information": {{
        "working_job_title": "string",
        "job_family": "string",
        "job_family_zone": "string",
        "job_code": "string",
        "position_number": "integer",
        "department_name": "string",
        "sap_organization_unit_number": "string",
        "employee_name": "string",
        "date_of_last_update": "date(in ddmmyyyy format)",
        "last_updated_by": "string",
        "title_of_supervisor": "string",
        "sap_personnel": "string",
        "name_of_supervisor": "string"
    }},
    "position_summary": "string",
    "duties_and_responsibilities": [
        {{
        "responsibility": "string",
        "time_spent_percentage": "integer",
        "essential_function": "boolean",
        "tasks": [
            "string"
        ]
        }}
    ],
    "supervision": "string",
    "qualifications_and_attributes": {{ ## please put the information in respective places, like if any minimum qualification information is available put it in minimum_qualifications if that element is not present you can leave it emprty also
        "required_qualifications": [
        "string"
        ],
        "preferred_qualifications": [
        "string"
        ],
        "helpful_qualifications": [
        "string"
        ],
        "minimum_qualifications": [
        "string"
        ],
        "other_information": [ # if there is any attribute information you can put it here
        "string"
        ]
    }},
    "zone_definition_factors": [
        {{
        "factor": "Nature/Complexity of Work",
        "description": "string"
        }},
        {{
        "factor": "Problem Solving/Decision-making",
        "description": "string"
        }},
        {{
        "factor": "Strategic Impact",
        "description": "string"
        }},
        {{
        "factor": "Know How",
        "description": "string"
        }},
        {{
        "factor": "Technical Know How",
        "description": "string"
        }},
        {{
        "factor": "Interactions",
        "description": "string"
        }},
        {{
        "factor": "Leadership",
        "description": "string"
        }}
    ],
    "physical_activities": {{
        "general_physical_reqs": [
        {{
            "activity": "sitting",
            "hours": "integer",
            "type": "string"
        }},
        {{
            "activity": "standing",
            "hours": "integer",
            "type": "string"
        }},
        {{
            "activity": "walking",
            "hours": "integer",
            "type": "string"
        }},
        {{
            "activity": "drive_motor_vehicle",
            "hours": "integer",
            "type": "string"
        }}
        ],
        "specific_physical_reqs": [ # in here the frequency value will be either empty string or "occasionally" or "between 2-5 hrs daily" or "over 5 hrs daily" ]
        {{
            "activity": "squating",
            "frequency": "string"
        }},
        {{
            "activity": "bending",
            "frequency": "string"
        }},
        {{
            "activity": "kneeling",
            "frequency": "string"
        }},
        {{
            "activity": "reaching_overhead",
            "frequency": "string"
        }},
        {{
            "activity": "reaching_forward",
            "frequency": "string"
        }},
        {{
            "activity": "reaching_low",
            "frequency": "string"
        }},
        {{
            "activity": "twisting",
            "frequency": "string"
        }},
        {{
            "activity": "crawling",
            "frequency": "string"
        }},
        {{
            "activity": "climbing_ladders",
            "frequency": "string"
        }},
        {{
            "activity": "climbing_stairs",
            "frequency": "string"
        }},
        {{
            "activity": "climbing_other",
            "frequency": "string"
        }},
        {{
            "activity": "walking_on_rough_ground",
            "frequency": "string"
        }},
        {{
            "activity": "exposure_to_changes_of_temperature_humidity",
            "frequency": "string"
        }},
        {{
            "activity": "exposure_to_dust_fumes_gases_chemicals",
            "frequency": "string"
        }},
        {{
            "activity": "being_near_moving_machinery",
            "frequency": "string"
        }},
        {{
            "activity": "working_from_heights",
            "frequency": "string"
        }}
        ],
        "lifting_handling_reqs": [ # L means Lifting, C means Carrying, P means Pushing, PL means Pulling] -- just for reference if all 4 L, C, P, PL are mentioned then give this format for all the 4 activities with the same weight range and frequency
        {{
            "activity_type": "lift",
            range_and_frequency: [
                {{
                    "weight_range": "11-24 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "25-49 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "50-74 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "75-100 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "Over 100 lbs",
                    "frequency": "string"
                }}
            ]
        }},
        {{
            "activity_type": "carry",
            range_and_frequency: [
                {{
                    "weight_range": "11-24 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "25-49 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "50-74 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "75-100 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "Over 100 lbs",
                    "frequency": "string"
                }}
            ]
        }},
        {{
            "activity_type": "push",
            range_and_frequency: [
                {{
                    "weight_range": "11-24 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "25-49 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "50-74 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "75-100 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "Over 100 lbs",
                    "frequency": "string"
                }}
            ]
        }},
        {{
            "activity_type": "pull",
            range_and_frequency: [
                {{
                    "weight_range": "11-24 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "25-49 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "50-74 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "75-100 lbs",
                    "frequency": "string"
                }},
                {{
                    "weight_range": "Over 100 lbs",
                    "frequency": "string"
                }}
            ]
        }}
        ],
        "manual_dexterity_reqs": {{
        "keyboarding" : {{
            "right_hand": "boolean",
            "left_hand": "boolean",
            "both_hands": "boolean"
        }},
        "filing": {{
            "right_hand": "boolean",
            "left_hand": "boolean",
            "both_hands": "boolean"
        }},
        "other_description": "string" ## if any other description in tools write here
        }},
        "work_attendance_reqs": {{
        "must_attend_workplace": "boolean",
        "alt_worksite_eligible": "boolean",
        "wfo_essential": "boolean",
        "wfo_non_essential": "boolean"
        }}
    }},
    "application_procedure": "",
    "additional_information": "",
    "confidence_scores":{{
        "general_information": <confidence score>,
        "position_summary": <confidence score>,
        "duties_and_responsibilities": <confidence score>,
        "supervision": <confidence score>,
        "qualifications_and_attributes": <confidence score>,
        "zone_definition_factors": <confidence score>,
        "physical_activities": {{
        "general_physical_reqs": <confidence score>,
        "specific_physical_reqs": <confidence score>,
        "lifting_handling_reqs": <confidence score>,
        "manual_dexterity_reqs": <confidence score>,
        "work_attendance_reqs": <confidence score>
        }},
        "application_procedure": <confidence score>,
        "additional_information": <confidence score>
    }}
    }}
    """

    def liftHandlingrerunPrompt():
        return """
Analyze the attached image and extract the lifting, carrying, pushing, and pulling requirements into the following JSON format. Each activity type should specify weight ranges and their corresponding frequency (as described in the image). If any weight range has no frequency listed, leave the frequency value as an empty string. the frequencies can be filled with only 4 values: "Less than 2 hrs daily", "Between 2-5 hrs daily", "Up to 2 hrs daily","Over 5 hrs daily" and "". if x is written in first row first column, then leave it blank for all frequencies in all weight ranges, in all activities.
[
{
    "activity_type": "lift",
    "range_and_frequency": [
        {
            "weight_range": "50-74 lbs",
            "frequency": ""
        },
        {
            "weight_range": "11-24 lbs",
            "frequency": ""
        },
        {
            "weight_range": "25-49 lbs",
            "frequency": ""
        },
        {
            "weight_range": "75-100 lbs",
            "frequency": ""
        },
        {
            "weight_range": "Over 100 lbs",
            "frequency": ""
        }
    ]
},
{
    "activity_type": "carry",
    "range_and_frequency": [
        {
            "weight_range": "50-74 lbs",
            "frequency": ""
        },
        {
            "weight_range": "11-24 lbs",
            "frequency": ""
        },
        {
            "weight_range": "25-49 lbs",
            "frequency": ""
        },
        {
            "weight_range": "75-100 lbs",
            "frequency": ""
        },
        {
            "weight_range": "Over 100 lbs",
            "frequency": ""
        }
    ]
},
{
    "activity_type": "push",
    "range_and_frequency": [
        {
            "weight_range": "11-24 lbs",
            "frequency": ""
        },
        {
            "weight_range": "25-49 lbs",
            "frequency": ""
        },
        {
            "weight_range": "50-74 lbs",
            "frequency": ""
        },
        {
            "weight_range": "75-100 lbs",
            "frequency": ""
        },
        {
            "weight_range": "Over 100 lbs",
            "frequency": ""
        }
    ]
},
{
    "activity_type": "pull",
    "range_and_frequency": [
        {
            "weight_range": "11-24 lbs",
            "frequency": ""
        },
        {
            "weight_range": "25-49 lbs",
            "frequency": ""
        },
        {
            "weight_range": "50-74 lbs",
            "frequency": ""
        },
        {
            "weight_range": "75-100 lbs",
            "frequency": ""
        },
        {
            "weight_range": "Over 100 lbs",
            "frequency": ""
        }
    ]
}
]

Carefully analyze the content in the image and map all details into this format. Ensure the frequencies and weight ranges align exactly with the image data. Leave any missing frequencies as an empty string.
"""

    def generalInformationExtractionPrompt():
        return """
        From the attached image extract the following mentioned in the same format and give the output in the json format as asked below:
        Few notes:
        job code and position number are different, if job code or any element is not present then put it as empty string
        {
        "working_job_title": "string",
        "job_family": "string",
        "job_family_zone": "string",
        "job_code": "string",
        "position_number": "integer",
        "department_name": "string",
        "sap_organization_unit_number": "string",
        "employee_name": "string",
        "date_of_last_update": "date(in mm-dd-yyyy format)",
        "last_updated_by": "string",
        "title_of_supervisor": "string",
        "sap_personnel": "string",
        "name_of_supervisor": "string"
        }
"""
