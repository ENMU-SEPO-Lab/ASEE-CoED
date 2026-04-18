import app.paths as paths
from pathlib import Path
from ollama import chat
import json

prompt= "" # TODO: Prompt design

def request_efficiency_eval(code: str):
    
    response = chat(
        model='gemini-3-flash-preview',
        messages=[
            {'role': 'system', 'content': prompt},
            {'role': 'user', 'content': code}
        ],
    )
    
    return response.message.content
    
def read_all_code_files(upload_dir_path: Path):
    
    complete_code = "\
        This is the student submission. The start of a separate code file is indicated \
        by the keywords: 'NEW CODE FILE' followed by the file name.\
    "
    
    for java_file in upload_dir_path.rglob("*.java"):
        
        try:
            with java_file.open("r", encoding="utf-8", errors="ignore") as file:
                code = file.read()
                
        except OSError:
            continue
            
        complete_code = complete_code + f"\n\nNEW CODE FILE: {java_file.name}\n\n" + code
    
    return complete_code

def get_preliminary_report():
    
    with open(paths.TEMP_JSON_FILE, "r") as file:
        data = json.load(file)

        report_file_path = Path(data.get("report_file_path"))
        
    with report_file_path.open("r", encoding="utf-8") as f:
        report = f.read()
        
    return (report_file_path, report)

def enhance_report(report: str, eff_eval: str):
    pass

def store_report(report: str, old_path: Path | str):
    pass

if __name__ == "__main__":
    
    upload_dir_path = paths.get_upload_dir_path_yml() # get the upload dir path
    code = read_all_code_files(upload_dir_path) # read all submitted .java code files
    eff_eval = request_efficiency_eval(code) # send code to llm for efficiency evaluation
    
    prelim_report_path, prelim_report = get_preliminary_report() 
    enhanced_report = enhance_report(prelim_report, eff_eval)
    
    store_report(enhance_report, prelim_report_path)
    
    # TODO: generate report and store it
    