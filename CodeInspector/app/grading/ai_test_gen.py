from pathlib import Path
from ollama import chat
import re

# llm_model = os.environ["OLLAMA_MODEL"]
# test_dir = os.environ["UNIT_TEST_DIR"]

llm_model = 'qwen2.5-coder:7b'
ROOT = Path(__file__).resolve().parents[3]
output_dir = ROOT / "PA_tests"
skeleton_file = ROOT / "PA_skeletons/PA03_skel.java"

system_prompt = """
You are an expert Java test engineer. Your task is to generate a complete, compilable JUnit test class for a Java assignment skeleton.

CONTRACT SOURCE
- Each method's expected behavior is defined by its Javadoc and signature. Treat the Javadoc as the authoritative specification — test what it states, including return values, state changes, and documented edge cases.
- Do NOT invent behavior that is not specified. If the Javadoc describes a return code (e.g. 0, 1, 2) or a specific side effect, test exactly those.
- If a method's behavior is genuinely ambiguous (e.g. an index mapping that is not specified), write tests only for the parts that ARE specified, and do not assume an unstated convention.

SCOPE
- Generate tests only for the public static methods. Ignore `main` and any interactive/IO code.
- For methods that return a value, assert on the return value.
- For methods that mutate an array or object, assert on the resulting state.
- For void methods that only print to stdout, test loosely if at all — assert only on essential content, not exact formatting. Prefer to skip them rather than write brittle whitespace-sensitive assertions.

TEST DESIGN
- Cover the meaningful input partitions implied by the contract: valid cases, boundary cases, and the failure/edge cases the Javadoc describes.
- Each test method should verify one behavior and have a descriptive name.
- Make tests deterministic and self-contained — construct fresh input data in each test; do not rely on shared mutable state between tests.
- Do NOT be too nit-picky with the edge cases, as the implementations will generally be written by Novice Java programming students

OUTPUT FORMAT
- Use JUnit 4 (`org.junit.Test`, `org.junit.Assert.*`).
- Output exactly ONE public test class. Java requires the file to contain a single public class, so do not emit helper public classes.
- Output ONLY the Java source code. No explanations, no commentary, no markdown code fences.
- Begin directly with the package declaration or imports.
"""

def read_skeleton(skeleton_file_path: Path) -> str:
    
    path = skeleton_file_path

    if not path.is_file():
        raise FileNotFoundError(f"Skeleton file not found: {path}")

    source = path.read_text(encoding="utf-8")
    
    return (
        f"Below is a Java assignment skeleton. Each method's Javadoc "
        f"specifies its contract — use these as the source of truth for "
        f"expected behavior, return values, and edge cases. Generate JUnit "
        f"tests for the public static methods (ignore `main`).\n\n"
        f"```java\n{source}\n```"
    )
    
"""
    Extract Java code from an LLM response and save it as a .java file
    named to match its public class.

    Args:
        llm_response: Raw text returned by the LLM.
        output_dir:   Directory to write the .java file into.

    Returns:
        Path to the written .java file.

    Raises:
        ValueError: If no public class name can be found in the code.
"""
def save_test_file(llm_response: str, output_dir: str) -> Path:
    code = _strip_markdown_fences(llm_response)

    match = re.search(r"public\s+class\s+(\w+)", code)
    if not match:
        raise ValueError("No public class declaration found in LLM response.")

    class_name = match.group(1)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    file_path = out_dir / f"{class_name}_TEST.java"
    file_path.write_text(code, encoding="utf-8")

    return file_path    

"""Remove surrounding ```java ... ``` fences if the LLM added them."""
def _strip_markdown_fences(text: str) -> str:
    fence = re.search(r"```(?:java)?\s*\n(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text.strip()

def request_test_generation(code: str) -> str:
    user_prompt = f"""
        ASSIGNMENT SKELETON:
        <<<CODE>>>
        {code}
        <<<END CODE>>>
    """
        
    print("Requesting Test Case Generation...")
    response = chat(
        model=llm_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        options={"num_ctx": 16384, "temperature": 0}
    )
    print("Done Generating Test Cases...")
    print(f"response token count: {response.prompt_eval_count}")
    return response.message.content

if __name__ == "__main__":
    
    code = read_skeleton(skeleton_file)

    llm_output = request_test_generation(code)
    if not llm_output or not llm_output.strip():
        raise RuntimeError("LLM returned empty response for test generation.")
    test_path = save_test_file(llm_output, output_dir)
    