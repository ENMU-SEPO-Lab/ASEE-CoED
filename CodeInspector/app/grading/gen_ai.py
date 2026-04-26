from .. import paths as paths
from pathlib import Path
from ollama import chat
import json
import sys

system_prompt = """
You are a teaching assistant grading introductory college (CS1-level) Java programming assignments.

Your task is to:
1. Evaluate the CODE EFFICIENCY of the student's submission
2. Rewrite the existing, preliminary grading report, incorporating the code efficiency feedback

----------------------------------------
CONTEXT
----------------------------------------
- The student is a beginner (CS1 level)
- Focus ONLY on meaningful efficiency issues
- Do NOT expect advanced algorithms or optimizations
- Ignore formatting, style, and minor inefficiencies

----------------------------------------
EFFICIENCY EVALUATION CRITERIA
----------------------------------------
Evaluate based on:
- Avoidance of unnecessary loops or nested loops
- Avoidance of redundant or repeated computations
- Reasonable use of basic data structures (arrays, ArrayList, etc.)
- Simplicity of approach (no unnecessary complexity)

DO NOT penalize:
- Minor inefficiencies
- Lack of advanced knowledge
- Small stylistic issues

----------------------------------------
TASK
----------------------------------------
You will receive:
1. A preliminary grading report serving as additional information for you to compose the final feedback report
2. The student's full code submission

You must:
- Assign an efficiency score (0–10)
- Identify key strengths and issues
- Write the final feedback report by integrating efficiency feedback naturally 
- Do not omit any valuable information provided in the preliminary report (such as most frequent errors, etc)
- Elaborate on the most frequent error of each category for each tool (PMD and CheckStyle) giving examples of what the cause is and how to correct it
- Fill the assigned efficiency score at the marked places in the report, according to the instructions found there

----------------------------------------
OUTPUT FORMAT (STRICT JSON)
----------------------------------------
You MUST return strictly valid JSON.
- Do not include explanations
- Do not include markdown
- Do not include code fences
- Do not include any text outside the JSON object
- The response must be directly parsable with json.loads()

Format of the JSON:

{
  "efficiency_score": 0,
  "strengths": ["..."],
  "issues": ["..."],
  "enhanced_report": "..."
}

----------------------------------------
SCORING GUIDE
----------------------------------------
9-10: Very efficient for CS1 level, no real issues  
7-8: Good, minor inefficiencies  
5-6: Noticeable inefficiencies  
3-4: Significant inefficiencies  
0-2: Very poor efficiency  

----------------------------------------
IMPORTANT RULES
----------------------------------------
- Be fair and consistent
- Do NOT invent problems if the code is simple and correct
- Keep feedback concise and helpful for a beginner
- Personalize the feedback to the student
- The enhanced_report must read naturally as a grading report (not as bullet points)
- The enhanced_report may not contain more than 140 characters per line
"""
    
def read_all_code_files(upload_dir_path: Path) -> str:
    
    complete_code = (
        "This is the student submission.\n"
        "Separate files are marked with 'NEW CODE FILE: filename'.\n"
    )
    
    for java_file in upload_dir_path.rglob("*.java"):
        
        try:
            with java_file.open("r", encoding="utf-8", errors="ignore") as file:
                code = file.read()
                
        except OSError:
            continue
            
        complete_code = complete_code + f"\n\nNEW CODE FILE: {java_file.name}\n\n" + code
    
    return complete_code

def get_preliminary_report() -> tuple[Path, str]:
    
    with open(paths.TEMP_JSON_FILE, "r") as file:
        data = json.load(file)

        report_file_path =  paths.GRADE_REPORTS_DIR / data.get("report_filename")
        
    with report_file_path.open("r", encoding="utf-8") as f:
        report = f.read()
        
    return (report_file_path, report)

def request_full_evaluation(code: str, report: str) -> str:
    
    user_prompt = f"""
        PRELIMINARY REPORT:
        <<<REPORT>>>
        {report}
        <<<END REPORT>>>

        STUDENT CODE:
        <<<CODE>>>
        {code}
        <<<END CODE>>>
    """
        
    response = chat(
        model='gemini-3-flash-preview',
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
    )
    
    return response.message.content

def parse_llm_response(response: str):
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        print("Invalid JSON from LLM:", response)
        return None

def store_report(report: str, old_path: Path | str) -> Path:
    
    old_path = Path(old_path)
    new_path = old_path.with_name(old_path.stem + "_ai_enhanced" + old_path.suffix)
    
    with open(new_path, "w") as file:
        file.write(report)
    
    print(f"Grade report created and saved to: {new_path}", file=sys.stderr)
    return new_path
    
def append_temp_info(json_path: Path | str, enhanced_report_path: Path):
    json_path = Path(json_path)
    
    with open(json_path, 'r+') as f:
        temp_info = json.load(f)
        temp_info["enhanced_report_filename"] = str(enhanced_report_path.name)
        
        f.seek(0)
        json.dump(temp_info, f, indent=4)
        f.truncate()
        print("JSON temp_info file updated successfully.", file=sys.stderr)

if __name__ == "__main__":
    
    upload_dir_path = paths.get_upload_dir_path_yml() # get the upload dir path
    code = read_all_code_files(upload_dir_path) # read all submitted .java code files
    
    prelim_report_path, prelim_report = get_preliminary_report() 
    llm_response = request_full_evaluation(code, prelim_report)
    
    llm_response = parse_llm_response(llm_response)
    
    if llm_response is None:
        print("LLM failed, using preliminary report", file=sys.stderr)
        store_report(prelim_report, prelim_report_path)
        sys.exit(0)
        
    enhanced_report = llm_response.get('enhanced_report')
    
    if not enhanced_report:
        print("Missing enhanced_report in LLM response", file=sys.stderr)
        enhanced_report = prelim_report

    enhanced_report_path = store_report(enhanced_report, prelim_report_path)
    append_temp_info(paths.TEMP_JSON_FILE, enhanced_report_path)   
