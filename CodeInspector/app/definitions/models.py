from dataclasses import dataclass

@dataclass
class CheckstyleViolation:
    file: str
    line: int
    severity: str
    message: str
    source: str
    
@dataclass
class PmdViolation:
    file: str
    beginline: int
    endline: int
    begincolumn: int
    endcolumn: int
    rule: str
    ruleset: str
    class_name: str
    priority: int
    message: str
    externalInfoUrl: str
    method: str | None = None
    variable: str | None = None

@dataclass
class TestFailureDetails:
    message: str
    stackTrace: list[str]
    
@dataclass
class UnitTestingSummary:
    testsRun: str
    failures: str
    errors: str
    skipped: str
    timeElapsed: str
 
@dataclass 
class UnitTestCase:
    name: str
    time: str
    status: str
    failureDetails: TestFailureDetails
    
@dataclass 
class UnitTestingResults:
    testSuite: str
    summary: UnitTestingSummary
    testcases: list[UnitTestCase]
    
@dataclass
class CombinedParsedViolations:
    checkstyle: list[CheckstyleViolation]
    pmd: list[PmdViolation]
    unit_testing: UnitTestingResults 
    
@dataclass
class ViolationReport:
    system: str
    studentName: str
    checkDate: str
    linesOfCode: int
    violations: CombinedParsedViolations

@dataclass
class 