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
    begin_line: int
    end_line: int
    begin_column: int
    end_column: int
    rule: str
    ruleset: str
    priority: int
    message: str
    class_name: str | None = None
    external_info_url: str | None = None
    method: str | None = None
    variable: str | None = None

@dataclass
class TestFailureDetails:
    message: str = None
    stackTrace: list[str] = None
    
@dataclass
class UnitTestingSummary:
    tests_ran: str
    failures: str
    errors: str
    skipped: str
    time_elapsed: str
 
@dataclass 
class UnitTestCase:
    name: str = None
    time: str = None
    status: str = None  
    failure_details: TestFailureDetails | None = None
    
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
    student_name: str
    check_date: str
    lines_of_code: int
    violations: CombinedParsedViolations

@dataclass
class ErrorsWithinCategoryStats:
    category_stats: dict[str, int]
    
    def get_most_common_error_category_and_count(self) -> tuple[str, int]:
        return max(
            self.category_stats.items(), 
            key=lambda x: x[1], 
            default=("None", 0)
        )
    
    def total_errors(self) -> int:
        return sum(self.category_stats.values())
    
@dataclass
class ErrorsWithinSeverityStats:
    severity_stats: dict[str, ErrorsWithinCategoryStats]
    
    def total_errors(self) -> int:
        return sum(
            stats.total_errors()
            for stats in self.severity_stats.values()
        )
        
    def get_most_common_severity(self) -> tuple[str, int]:
        if not self.severity_stats:
            return ("None", 0)

        return max(
            (
                (severity, stats.total_errors())
                for severity, stats in self.severity_stats.items()
            ),
            key=lambda severity_and_count: severity_and_count[1]
        )    
    
@dataclass
class ErrorsWithinFileStats:
    file_stats: dict[str, ErrorsWithinSeverityStats]
    
    def total_errors(self) -> int:
        return sum(
            stats.total_errors()
            for stats in self.file_stats.values()
        )

    def get_file_with_most_errors(self) -> tuple[str, int]:
        if not self.file_stats:
            return ("None", 0)

        return max(
            (
                (file, stats.total_errors())
                for file, stats in self.file_stats.items()
            ),
            key=lambda file_and_count: file_and_count[1]
        )    

@dataclass
class ErrorsWithinSubmissionStats:
    submission_stats: dict[str, ErrorsWithinFileStats]
    
    def total_errors(self) -> int:
        return sum(
            stats.total_errors()
            for stats in self.submission_stats.values()
        )