from dataclasses import dataclass, field
from typing import TypeAlias
    
@dataclass
class CheckstyleViolation:
    file_name: str
    line: int
    severity: str
    type_name: str
    message: str
    category: str | None = None
    
@dataclass
class PmdViolation:
    file_name: str
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
    message: str = ""
    stack_trace: list[str] = field(default_factory=list)
    
@dataclass
class UnitTestingSummary:
    tests_ran: int = 0
    failures: int = 0 
    errors: int = 0
    skipped: int = 0
    time_elapsed: str = ""
 
@dataclass 
class UnitTestCase:
    name: str | None = None
    time: str | None = None
    status: str | None = None  
    failure_details: TestFailureDetails | None = None
    
@dataclass 
class UnitTestingResults:
    summary: UnitTestingSummary | None = None
    testcases: list[UnitTestCase] | None = None
    test_suite: str | None = None
    
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

# a violation can be either of type Checkstyle or PMD
Violation: TypeAlias = CheckstyleViolation | PmdViolation

@dataclass
class ViolationsWithinType:
    # each error type can occur multiple times
    violations: list[Violation] = field(default_factory=list)
    
    def get_error_count_within_type(self) -> int:
        # get total error count within type
        return len(self.violations)
        
@dataclass
class TypesWithinCategory:
    # one category class can have multiple subtypes
    # type_name: str -> type_structure
    types: dict[str, ViolationsWithinType] = field(default_factory=dict)
    
    def get_error_count_within_cat(self) -> int:
        # get total error count within category
        return sum(
            t.get_error_count_within_type()
            for t in self.types.values()
        )
    
    def get_most_common_error_type_and_count(self) -> tuple[str, int]:
        if not self.types:
            return ("None", 0) 
        
        return max(
                (
                    (type_name, type_class.get_error_count_within_type())
                    for type_name, type_class in self.types.items()
                ),
                key=lambda type_and_count: type_and_count[1]
            )  
    
@dataclass
class CategoriesWithinSeverity:
    # one severity class can have multiple subcategories.
    # category_name: str -> category_structure 
    categories: dict[str, TypesWithinCategory] = field(default_factory=dict)
    
    def get_error_count_within_sev(self) -> int:
        """get total error count within severity class

        Returns:
            int: the number of errors
        """
        return sum(
            category.get_error_count_within_cat()
            for category in self.categories.values()
        )
        
    def get_most_common_error_category_and_count(self) -> tuple[str, int]:
        if not self.categories:
            return ("None", 0) 
        
        return max(
                (
                    (category_name, category_class.get_error_count_within_cat())
                    for category_name, category_class in self.categories.items()
                ),
                key=lambda category_and_count: category_and_count[1]
            )   
    
@dataclass
class SeveritiesWithinFile:
    # one file can contain errors of multiple severity classes (checkstyle: 3, pmd: 5)
    # severity_name: str -> severity_structure 
    severities: dict[str, CategoriesWithinSeverity] = field(default_factory=dict)
    
    def get_error_count_within_file(self) -> int:
        # get total error count within file
        return sum(
            severity.get_error_count_within_sev()
            for severity in self.severities.values()
        )
        
    def get_most_common_severity(self) -> tuple[str, int]:
        if not self.severities:
            return ("None", 0)

        return max(
            (
                (severity_name, severity_class.get_error_count_within_sev()) 
                for severity_name, severity_class in self.severities.items()
            ),
            key=lambda severity_and_count: severity_and_count[1]
        )   

@dataclass
class CheckstyleSeveritiesWithinFile(SeveritiesWithinFile):
    # initialize structure with severity keys for checkstyle
    def __post_init__(self):
        self.severities = {
            "info": CategoriesWithinSeverity(),
            "warning": CategoriesWithinSeverity(),
            "error": CategoriesWithinSeverity()
        }
    
@dataclass
class PmdSeveritiesWithinFile(SeveritiesWithinFile):
    # initialize structure with severity keys for pmd
    def __post_init__(self):
        self.severities = {
            "5": CategoriesWithinSeverity(),
            "4": CategoriesWithinSeverity(),
            "3": CategoriesWithinSeverity(),
            "2": CategoriesWithinSeverity(),
            "1": CategoriesWithinSeverity()
        }

@dataclass
class ProcessedViolations:
    # one submission can contain multiple files.
    # file_name -> file_datastructure
    severity_class: type[SeveritiesWithinFile] # CheckstyleSeveritiesWithinFile or PmdSeveritiesWithinFile
    files: dict[str, SeveritiesWithinFile] = field(default_factory=dict)
    
    def get_error_count_within_submission(self) -> int:
        # get total error count within submission
        return sum(
            file_data.get_error_count_within_file()
            for file_data in self.files.values()
        )
        
    def get_file_with_most_errors(self) -> tuple[str, int]:
        if not self.files:
            return ("None", 0)

        return max(
            (
                (file_name, file_data.get_error_count_within_file()) 
                for file_name, file_data in self.files.items()
            ),
            key=lambda file_and_count: file_and_count[1]
        )
    
    def file_bucket(self, file_name: str) -> SeveritiesWithinFile:
        return self.files.setdefault(file_name, self.severity_class())
        
    def add_violation(
        self, 
        file_name: str, 
        severity: str, 
        category: str, 
        type_name: str, 
        violation: Violation
    ) -> None:
        file_bucket = self.file_bucket(file_name)
        severity_bucket = file_bucket.severities.setdefault(severity, CategoriesWithinSeverity())
        category_bucket = severity_bucket.categories.setdefault(category, TypesWithinCategory())
        type_bucket = category_bucket.types.setdefault(type_name, ViolationsWithinType())
        type_bucket.violations.append(violation)
        
@dataclass
class ProcessedJunitTests:
    all_tests: list[UnitTestCase]
    failed_tests: list[UnitTestCase]
        
@dataclass 
class ProcessedSubmission:
    cs_processed: ProcessedViolations
    pmd_processed: ProcessedViolations
    junit_processed: ProcessedJunitTests
    
@dataclass
class SubmissionScores:
    cs_score: int
    cs_weighted_error: float
    pmd_score: int
    pmd_weighted_error: float
    junit_success_ratio: float
    coding_std_score: int
    req_score: int
    overall_score: int
    run_score: int | None = None